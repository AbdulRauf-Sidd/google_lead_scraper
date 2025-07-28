#!/usr/bin/env python3
"""
Log viewer utility for Lead Scraper application.
This script helps filter and view logs for errors and items without emails.
"""

import re
import sys
import json
from datetime import datetime
from pathlib import Path

def parse_log_line(line):
    """Parse a log line and extract timestamp, level, and message"""
    # Expected format: 2024-01-01 12:00:00,000 - INFO - message
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)'
    match = re.match(pattern, line.strip())
    
    if match:
        timestamp_str, level, message = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'raw': line.strip()
            }
        except ValueError:
            return None
    return None

def extract_json_from_message(message):
    """Try to extract JSON from log message"""
    try:
        # Look for JSON patterns in the message
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, message, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return None

def filter_logs(log_file, show_errors=True, show_no_emails=True, show_all=False):
    """Filter logs based on criteria"""
    if not Path(log_file).exists():
        print(f"❌ Log file '{log_file}' not found!")
        return
    
    print(f"📋 Analyzing log file: {log_file}")
    print("=" * 80)
    
    error_count = 0
    no_emails_count = 0
    total_lines = 0
    
    with open(log_file, 'r') as f:
        for line in f:
            total_lines += 1
            log_entry = parse_log_line(line)
            
            if not log_entry:
                continue
            
            # Show errors
            if show_errors and log_entry['level'] in ['ERROR', 'CRITICAL']:
                print(f"🔴 ERROR [{log_entry['timestamp']}] {log_entry['message']}")
                error_count += 1
                
                # Try to extract and pretty-print JSON from error messages
                json_data = extract_json_from_message(log_entry['message'])
                if json_data:
                    print("   JSON data:")
                    print(json.dumps(json_data, indent=4))
                    print()
            
            # Show warnings about no emails found
            elif show_no_emails and "No emails found in search result" in log_entry['message']:
                print(f"⚠️  NO EMAILS [{log_entry['timestamp']}]")
                print(f"   {log_entry['message']}")
                no_emails_count += 1
                
                # Try to extract and pretty-print the JSON object
                json_data = extract_json_from_message(log_entry['message'])
                if json_data:
                    print("   JSON object without emails:")
                    print(json.dumps(json_data, indent=4))
                    print()
            
            # Show all logs if requested
            elif show_all:
                level_icon = {
                    'INFO': 'ℹ️',
                    'WARNING': '⚠️',
                    'ERROR': '🔴',
                    'CRITICAL': '🚨'
                }.get(log_entry['level'], '📝')
                
                print(f"{level_icon} {log_entry['level']} [{log_entry['timestamp']}] {log_entry['message']}")
    
    print("=" * 80)
    print(f"📊 Summary:")
    print(f"   Total log lines: {total_lines}")
    print(f"   Errors found: {error_count}")
    print(f"   Items without emails: {no_emails_count}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python log_viewer.py <log_file> [options]")
        print("\nOptions:")
        print("  --errors-only     Show only errors")
        print("  --no-emails-only  Show only items without emails")
        print("  --all             Show all log entries")
        print("  --help            Show this help message")
        print("\nExamples:")
        print("  python log_viewer.py app.log")
        print("  python log_viewer.py app.log --errors-only")
        print("  python log_viewer.py app.log --no-emails-only")
        print("  python log_viewer.py app.log --all")
        return
    
    log_file = sys.argv[1]
    show_errors = True
    show_no_emails = True
    show_all = False
    
    # Parse command line options
    for arg in sys.argv[2:]:
        if arg == '--errors-only':
            show_errors = True
            show_no_emails = False
            show_all = False
        elif arg == '--no-emails-only':
            show_errors = False
            show_no_emails = True
            show_all = False
        elif arg == '--all':
            show_errors = True
            show_no_emails = True
            show_all = True
        elif arg == '--help':
            print("Usage: python log_viewer.py <log_file> [options]")
            return
        else:
            print(f"Unknown option: {arg}")
            return
    
    filter_logs(log_file, show_errors, show_no_emails, show_all)

if __name__ == "__main__":
    main() 