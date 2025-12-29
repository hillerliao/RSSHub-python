import requests
import csv
import io
import random
import os
from urllib.parse import quote, urlparse
from rsshub.utils import DEFAULT_HEADERS
from rsshub.extensions import cache

def ctx(url="https://raw.githubusercontent.com/HenryLoveMiller/ja/refs/heads/main/raz.csv", title_col=0, delimiter=None):
    
    try:
        # Extract filename from URL for feed title
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        # Remove extension if present
        if '.' in filename:
            filename = filename.rsplit('.', 1)[0]
        # Convert filename to uppercase
        filename = filename.upper()
        # Use filename as feed title
        feed_title = f'{filename} CSV Feed'
        
        # Check cache first with URL-based cache key
        cache_key = f'randomline_csv_content:{url}'  # Dynamic cache key based on URL
        content = cache.get(cache_key)
        
        if not content:
            # Use direct request with proper timeout if cache miss
            try:
                # Ensure URL is clean
                url = url.strip()
                print(f"DEBUG: Fetching URL: {url!r}")
                response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
                print(f"DEBUG: Status Code: {response.status_code}")
                response.raise_for_status()
                content = response.text
                cache.set(cache_key, content, timeout=3600)
            except Exception as e:
                print(f"DEBUG: Request failed with default headers: {e}")
                # Retry with curl User-Agent to mimic successful CLI command
                try:
                    print("DEBUG: Retrying with curl User-Agent...")
                    headers_curl = {'User-Agent': 'curl/7.68.0'}
                    response = requests.get(url, headers=headers_curl, timeout=30)
                    response.raise_for_status()
                    content = response.text
                    cache.set(cache_key, content, timeout=3600)
                    print("DEBUG: Retry successful!")
                except Exception as e2:
                    print(f"DEBUG: Retry failed: {e2}")
                    if 'response' in locals():
                        print(f"DEBUG: Response text: {response.text[:200]}")
                    raise e
    except Exception as e:
        import sys
        print(f"DEBUG: Randomline error: {e}", file=sys.stderr)
        return {
            'title': feed_title,
            'link': url,
            'description': f'Error fetching data: {str(e)}',
            'items': []
        }

    # Parse CSV
    try:
        # Clean the content to handle any potential issues
        content = content.strip()
        if not content:
            return {
                'title': feed_title,
                'link': url,
                'description': 'Empty content received',
                'items': []
            }
        
        # Determine delimiter
        if delimiter and delimiter.lower() == 'tab':
            delimiter_char = '\t'
        elif delimiter and delimiter.lower() == 'newline':
             delimiter_char = '\n'
        elif delimiter:
             delimiter_char = delimiter
        else:
            delimiter_char = ','

        # Use csv.reader first to check structure
        lines = content.splitlines()
        if len(lines) < 2:
            return {
                'title': feed_title,
                'link': url,
                'description': 'Insufficient data in CSV',
                'items': []
            }
        
        # Parse CSV with DictReader to get fieldnames
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file, delimiter=delimiter_char)
        fieldnames = reader.fieldnames
        
        if not fieldnames or len(fieldnames) < 1:
            return {
                'title': feed_title,
                'link': url,
                'description': 'No header found in CSV',
                'items': []
            }
        
        # Get all rows
        rows = list(reader)
        if not rows:
            return {
                'title': feed_title,
                'link': url,
                'description': 'No valid rows found in CSV',
                'items': []
            }

        # Randomly select one row
        row = random.choice(rows)
        
        # Get specified column as title
        # Validate title_col is within range
        if title_col < 0 or title_col >= len(fieldnames):
            title_col = 0  # Fallback to first column if out of range
        
        title_column_name = fieldnames[title_col]
        title = row.get(title_column_name, '').strip()
        
        if not title:
            # Try again with another random row
            row = random.choice(rows)
            title = row.get(title_column_name, '').strip()

        # Build description from all columns except the title column
        description_parts = [title]  # Start with title
        for i, fieldname in enumerate(fieldnames):
            if i == title_col:  # Skip the title column
                continue
            value = row.get(fieldname, '').strip()
            if value:  # Only add non-empty values
                description_parts.append(f"{fieldname}: {value}")
        
        description = '<br>'.join(description_parts)  # Join with HTML line break
        if len(description) == len(title):  # If no other columns added
            description = title  # Just use title as description
            
        link = f"{url}?title={quote(title[:100])}"

        item = {
            'title': title,
            'description': description,
            'link': link,
            'pubDate': '',  # No date in CSV
        }

        return {
            'title': feed_title,
            'link': url,
            'description': 'Random item from CSV file',
            'items': [item]
        }
    except Exception as e:
        return {
            'title': feed_title,
            'link': url,
            'description': f'Error processing data: {str(e)}',
            'items': []
        }