import requests
import csv
import io
import random
import os
from urllib.parse import quote, urlparse
from rsshub.utils import DEFAULT_HEADERS
from rsshub.extensions import cache
import trafilatura

def ctx(url="https://raw.githubusercontent.com/HenryLoveMiller/ja/refs/heads/main/raz.csv", title_col=0, delimiter=None, min_length=0):
    
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
                
                # Check if content needs extraction (HTML)
                should_extract = False
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Determine if we should attempt extraction
                # If explicit delimiter is CSV/TSV, probably don't extract unless user forces it (not handled here)
                # If URL ends in .txt or .csv, assumption is raw data.
                # If URL is generic web page, assume HTML.
                ext = os.path.splitext(parsed_url.path)[1].lower()
                if 'html' in content_type or ext not in ['.csv', '.txt', '.tsv', '.json']:
                    should_extract = True
                
                if should_extract:
                    extracted_text = trafilatura.extract(content)
                    if extracted_text:
                        print("DEBUG: Content extracted successfully via trafilatura")
                        # Try to extract metadata for title
                        try:
                            metadata = trafilatura.extract_metadata(content)
                            if metadata and metadata.title:
                                feed_title = metadata.title
                        except Exception as e:
                            print(f"DEBUG: Failed to extract metadata: {e}")

                        content = extracted_text
                        # If we extracted text, we treat it as a newline-delimited file automatically
                        if not delimiter:
                            delimiter = 'newline'
                    else:
                        print("DEBUG: Trafilatura extraction returned None, using raw content")

                cache.set(cache_key, content, timeout=3600)
            except Exception as e:
                print(f"DEBUG: Request failed with default headers: {e}")
                # Retry with curl User-Agent to mimic successful CLI command
                try:
                    print("DEBUG: Retrying with curl User-Agent...")
                    headers_curl = {'User-Agent': 'curl/7.68.0'}
                    # ... (retry logic kept simple, but duplicating extraction logic here would be complex. 
                    # For now, let's assume if retry is needed, it's just for fetching.)
                    response = requests.get(url, headers=headers_curl, timeout=30)
                    response.raise_for_status()
                    content = response.text
                    
                    # Same extraction logic for retry
                    should_extract = False
                    content_type = response.headers.get('Content-Type', '').lower()
                    ext = os.path.splitext(parsed_url.path)[1].lower()
                    if 'html' in content_type or ext not in ['.csv', '.txt', '.tsv', '.json']:
                        should_extract = True
                    
                    if should_extract:
                        extracted_text = trafilatura.extract(content)
                        if extracted_text:
                            # Try to extract metadata for title
                            try:
                                metadata = trafilatura.extract_metadata(content)
                                if metadata and metadata.title:
                                    feed_title = metadata.title
                            except Exception as e:
                                print(f"DEBUG: Failed to extract metadata: {e}")

                            content = extracted_text
                            if not delimiter:
                                delimiter = 'newline'

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
        
        # Get all rows with original line numbers (header is line 1, so indices start at line 2)
        # Store as (line_number, row_dict)
        all_rows = list(reader)
        if not all_rows:
            return {
                'title': feed_title,
                'link': url,
                'description': 'No valid rows found in CSV',
                'items': []
            }
            
        indexed_rows = [(i + 2, row) for i, row in enumerate(all_rows)]

        # Validate title_col is within range
        if title_col < 0 or title_col >= len(fieldnames):
            title_col = 0
            
        title_column_name = fieldnames[title_col]
        
        # Filter rows that meet the min_length criteria
        if min_length > 0:
            valid_rows = [
                (ln, row) for ln, row in indexed_rows
                if len(row.get(title_column_name, '').strip()) >= min_length
            ]
            if not valid_rows:
                return {
                    'title': feed_title,
                    'link': url,
                    'description': f'No lines found with length >= {min_length}',
                    'items': []
                }
            indexed_rows = valid_rows

        # Randomly select one row from valid rows
        line_num, row = random.choice(indexed_rows)
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
        
        # Add ChatGPT search link
        chatgpt_url = f"https://chatgpt.com/?hints=search&ref=ext&q={quote(title)}"
        description += f'<br><a href="{chatgpt_url}" target="_blank">ChatGPT解读</a>'

        # Add original line number and source link
        # Format: from line XX of <a href>{file name}</a>
        # We use feed_title as the file name/source name
        description += f'<br><br>from line {line_num} of <a href="{url}" target="_blank">{feed_title}</a>'
            
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