# Lead Scraper - Professional Search Tool

A modern Flask web application that allows users to search for professional leads across the web using Google Custom Search API. The application features a stylish, responsive frontend with real-time validation and CSV export functionality.

## Features

- **Modern UI**: Beautiful, responsive design with gradient backgrounds and smooth animations
- **Form Validation**: Real-time client-side validation with error messages
- **Loading States**: Animated loading spinner during API calls
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **CSV Export**: Download search results as CSV files
- **Security**: API key validation and secure environment variable handling
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Comprehensive logging system for debugging and monitoring

## Requirements

- Python 3.7+
- Flask
- Google Custom Search API key
- Search Engine ID

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AbdulRauf-Sidd/google_lead_scraper.git
   cd google_lead_scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with the following content:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   SEARCH_ENGINE_ID=your_search_engine_id_here
   CLIENT_KEY=your_client_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

4. **Get Google Custom Search API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Custom Search API
   - Create credentials (API key)
   - Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
   - Create a new search engine
   - Get your Search Engine ID

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

3. **Using the application**:
   - Fill in all required fields (Website, City, Occupation, Email Domain, API Key)
   - Click "Search Leads" to start the search
   - Wait for the search to complete
   - Click "Download CSV" to download the results

## API Endpoints

### POST `/api/search`
Searches for leads based on the provided parameters.

**Request Body**:
```json
{
  "website": "linkedin.com",
  "city": "New York",
  "occupation": "Realtor",
  "email_domain": "gmail.com",
  "key": "your_api_key"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Found 15 results",
  "csv_data": "Title,Source,URL,Emails,First Name,Last Name\n...",
  "results_count": 15,
  "total_processed": 20,
  "items_without_emails": 5
}
```

### POST `/api/download-csv`
Downloads the CSV file.

**Request Body**:
```json
{
  "csv_data": "Title,Source,URL,Emails,First Name,Last Name\n..."
}
```

## Logging

The application includes comprehensive logging for debugging and monitoring:

### Log Files
- **app.log**: Main application log file with all events
- **Console output**: Real-time logging to terminal

### Logged Information
- **API requests**: All Google Custom Search API calls
- **Search results**: Number of items found and processed
- **Email extraction**: Items where no emails were found (with full JSON)
- **Errors**: All application errors with stack traces
- **Rate limiting**: Rate limit violations
- **Authentication**: Invalid API key attempts

### Log Viewer Utility
Use the included log viewer to filter and analyze logs:

```bash
# View all errors and items without emails
python log_viewer.py app.log

# View only errors
python log_viewer.py app.log --errors-only

# View only items without emails
python log_viewer.py app.log --no-emails-only

# View all log entries
python log_viewer.py app.log --all
```

## Security Features

- **Rate Limiting**: 100 requests per day, 10 per minute
- **Search Capacity**: Up to 1000 results per search
- **API Key Validation**: Validates the provided API key against the server's key
- **Input Validation**: Server-side validation of all required fields
- **Error Handling**: Comprehensive error handling without exposing sensitive information

## Project Structure

```
google_lead_scraper/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── test.py              # Original test script
├── log_viewer.py        # Log analysis utility
├── templates/
│   └── index.html       # Frontend template
└── README.md           # This file
```

## Configuration

The application uses the following configuration options (in `config.py`):

- `SECRET_KEY`: Flask secret key for session management
- `GOOGLE_API_KEY`: Your Google Custom Search API key
- `SEARCH_ENGINE_ID`: Your Google Custom Search Engine ID
- `CLIENT_KEY`: Client API key for authentication
- `RATELIMIT_DEFAULT`: Rate limiting configuration

## Error Handling

The application handles various error scenarios:

- **Missing fields**: Returns 400 error with specific field names
- **Invalid API key**: Returns 401 error
- **API rate limits**: Returns 429 error
- **Network errors**: Graceful handling with user-friendly messages
- **Server errors**: Returns 500 error with generic message

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support or questions, please open an issue on the repository. 