import os
import re
import csv
import io
import json
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

# Enable CORS
CORS(app)

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

def fetch_results(query, start=1):
    """Fetch results from Google Custom Search API"""
    if not app.config['GOOGLE_API_KEY'] or not app.config['SEARCH_ENGINE_ID']:
        logger.error("Missing API key or Search Engine ID in configuration")
        return []
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": app.config['GOOGLE_API_KEY'],
        "cx": app.config['SEARCH_ENGINE_ID'],
        "q": query,
        "start": start
    }
    
    try:
        logger.info(f"Making API request to Google Custom Search: query='{query}', start={start}")
        res = requests.get(url, params=params, timeout=30)
        
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            logger.info(f"API request successful: found {len(items)} items")
            return items
        else:
            logger.error(f"API request failed with status {res.status_code}: {res.text}")
            return []
    except requests.RequestException as e:
        logger.error(f"Request exception during API call: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during API call: {str(e)}")
        return []

def extract_emails(obj):
    """Extract emails from any object structure"""
    emails = set()
    
    def scan(data):
        if isinstance(data, dict):
            for k, v in data.items():
                scan(v)
        elif isinstance(data, list):
            for item in data:
                scan(item)
        elif isinstance(data, str):
            found = re.findall(EMAIL_REGEX, data)
            emails.update(found)
    
    scan(obj)
    return list(emails)

def parse_result(item):
    """Parse a search result item"""
    title = item.get("title", "")
    url = item.get("link", "")
    source = "linkedin" if re.search(r'linkedin\.com', url, re.IGNORECASE) else "other"
    emails = extract_emails(item)
    
    meta = {}
    for tag in item.get("pagemap", {}).get("metatags", []):
        meta.update(tag)
    
    first_name = meta.get("profile:first_name", "")
    last_name = meta.get("profile:last_name", "")
    
    # Log if no emails found in this item
    if not emails:
        logger.warning(f"No emails found in search result: {json.dumps(item, indent=2)}")
    
    return {
        "title": title,
        "source": source,
        "url": url,
        "emails": emails,
        "first_name": first_name,
        "last_name": last_name
    }

def generate_csv(data):
    """Generate CSV from the parsed data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Title', 'Source', 'URL', 'Emails', 'First Name', 'Last Name'])
    
    # Write data
    for item in data:
        writer.writerow([
            item['title'],
            item['source'],
            item['url'],
            ', '.join(item['emails']),
            item['first_name'],
            item['last_name']
        ])
    
    output.seek(0)
    return output.getvalue()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
@limiter.limit("10 per minute")
def search():
    """API endpoint for searching and generating CSV"""
    try:
        data = request.get_json()
        logger.info(f"Search request received: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        required_fields = ['website', 'city', 'occupation', 'email_domain', 'key']
        for field in required_fields:
            if not data.get(field):
                error_msg = f'Missing required field: {field}'
                logger.error(f"Validation error: {error_msg}")
                return jsonify({'error': error_msg}), 400
        
        # Validate API key
        if data['key'] != app.config['CLIENT_KEY']:
            error_msg = 'Invalid API key'
            logger.error(f"Authentication error: {error_msg}")
            return jsonify({'error': error_msg}), 401
        
        # Construct query
        query = f'site:{data["website"]} "{data["city"]}" "{data["occupation"]}" "@{data["email_domain"]}"'
        logger.info(f"Constructed search query: {query}")
        
        # Fetch results (up to 1000 results maximum)
        all_data = []
        total_items_processed = 0
        items_without_emails = 0
        
        for i in range(0, 1000, 10):  # Google API returns max 10 results per request
            results = fetch_results(query, start=i + 1)
            if not results:
                logger.info(f"No more results found at offset {i}")
                break
                
            for item in results:
                total_items_processed += 1
                parsed = parse_result(item)
                all_data.append(parsed)
                
                # Count items without emails
                if not parsed['emails']:
                    items_without_emails += 1
        
        logger.info(f"Search completed: {len(all_data)} total results, {items_without_emails} without emails")
        
        # Generate CSV
        csv_data = generate_csv(all_data)
        
        response_data = {
            'success': True,
            'message': f'Found {len(all_data)} results',
            'csv_data': csv_data,
            'results_count': len(all_data),
            'total_processed': total_items_processed,
            'items_without_emails': items_without_emails
        }
        
        logger.info(f"Search response: {json.dumps(response_data, indent=2)}")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"Unexpected error during search: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/download-csv', methods=['POST'])
@limiter.limit("10 per minute")
def download_csv():
    """Download CSV file"""
    try:
        data = request.get_json()
        csv_data = data.get('csv_data', '')
        
        if not csv_data:
            error_msg = 'No CSV data provided'
            logger.error(f"Download error: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        logger.info("CSV download requested")
        
        # Create a file-like object
        csv_io = io.BytesIO(csv_data.encode('utf-8'))
        csv_io.seek(0)
        
        return send_file(
            csv_io,
            mimetype='text/csv',
            as_attachment=True,
            download_name='search_results.csv'
        )
        
    except Exception as e:
        error_msg = f"Unexpected error during CSV download: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': 'Download failed'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 error: {request.url}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def ratelimit_handler(error):
    logger.warning(f"Rate limit exceeded for IP: {get_remote_address()}")
    return jsonify({'error': 'Rate limit exceeded'}), 429

if __name__ == '__main__':
    logger.info("Starting Lead Scraper application")
    app.run(debug=True, host='0.0.0.0', port=5000) 