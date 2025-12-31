import requests
import csv
import io
import random
import os
import tempfile
import ebooklib
from ebooklib import epub
import mobi
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
from rsshub.utils import DEFAULT_HEADERS
from rsshub.extensions import cache
import trafilatura

def extract_content(response, url):
    parsed_url = urlparse(url)
    ext = os.path.splitext(parsed_url.path)[1].lower()
    content = None
    delimiter = None
    feed_title = None

    if ext == '.epub':
        print("DEBUG: Detected EPUB file, processing...")
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=True) as tmp:
            tmp.write(response.content)
            tmp.flush()
            book = epub.read_epub(tmp.name)
            extracted_parts = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    extracted_parts.append(soup.get_text('\n', strip=True))
            content = '\n'.join(extracted_parts)
            delimiter = 'newline'
    elif ext == '.mobi':
        print("DEBUG: Detected MOBI file, processing...")
        with tempfile.NamedTemporaryFile(suffix='.mobi', delete=True) as tmp:
            tmp.write(response.content)
            tmp.flush()
            try:
                # mobi.extract returns (tempdir, filepath) or raises
                extraction_result = mobi.extract(tmp.name)
                if isinstance(extraction_result, tuple) and len(extraction_result) == 2:
                    tempdir, filepath = extraction_result
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text('\n', strip=True)
                        delimiter = 'newline'
                    finally:
                        import shutil
                        if os.path.exists(tempdir):
                            shutil.rmtree(tempdir)
                else:
                    print(f"DEBUG: mobi.extract returned unexpected value: {extraction_result}")
                    content = response.text
            except Exception as e:
                print(f"DEBUG: MOBI extraction failed: {e}")
                content = response.text
    else:
        content = response.text
        should_extract = False
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' in content_type or ext not in ['.csv', '.txt', '.tsv', '.json']:
            should_extract = True
        
        if should_extract:
            extracted_text = trafilatura.extract(content)
            if extracted_text:
                print("DEBUG: Content extracted successfully via trafilatura")
                try:
                    metadata = trafilatura.extract_metadata(content)
                    if metadata and metadata.title:
                        feed_title = metadata.title
                except Exception as e:
                    print(f"DEBUG: Failed to extract metadata: {e}")
                content = extracted_text
                delimiter = 'newline'
    
    return content, delimiter, feed_title

def ctx(url="https://raw.githubusercontent.com/HenryLoveMiller/ja/refs/heads/main/raz.csv", title_col=0, delimiter=None, min_length=0):
    
    feed_title = "Random Line Feed"
    try:
        # Extract filename from URL for feed title
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        filetype = ''
        if '.' in filename:
            filename, filetype = filename.rsplit('.', 1)
        filename = filename.upper()
        feed_title = f'{filename} {filetype.upper()} Feed'.strip()
        
        cache_key = f'randomline_csv_content:{url}'
        content = cache.get(cache_key)
        
        if not content:
            url = url.strip()
            print(f"DEBUG: Fetching URL: {url!r}")
            try:
                response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
                response.raise_for_status()
                content, extracted_delimiter, extracted_title = extract_content(response, url)
                if extracted_delimiter:
                    delimiter = extracted_delimiter
                if extracted_title:
                    feed_title = extracted_title
            except Exception as e:
                print(f"DEBUG: Request failed with default headers: {e}, retrying with curl...")
                headers_curl = {'User-Agent': 'curl/7.68.0'}
                response = requests.get(url, headers=headers_curl, timeout=30)
                response.raise_for_status()
                content, extracted_delimiter, extracted_title = extract_content(response, url)
                if extracted_delimiter:
                    delimiter = extracted_delimiter
                if extracted_title:
                    feed_title = extracted_title

            if content:
                cache.set(cache_key, content, timeout=3600)

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
        selected_item = random.choice(indexed_rows)
        if not (isinstance(selected_item, tuple) and len(selected_item) == 2):
            return {
                'title': feed_title,
                'link': url,
                'description': f'Internal error: selected row is not a valid tuple: {type(selected_item)}',
                'items': []
            }
            
        line_num, row = selected_item
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
        
        # Add original line number and source link
        # Format: from line XX of <a href>{file name}</a>
        # We use feed_title as the file name/source name
        description += f'<br><br>来源：<a href="{url}" target="_blank">{filename}</a> 第{line_num}行'
        
        # Add ChatGPT search link
        prompt_prefix = f"explain in plain and vivid English:"
        chatgpt_url = f"https://chatgpt.com/?hints=search&ref=ext&q={quote(title)}"
        chatgpt_url_en = f"https://chatgpt.com/?hints=search&ref=ext&q={quote(prompt_prefix + title)}"
        google_url = f"https://www.google.com/search?q={quote(title)}"
        google_url_en = f"https://www.google.com/search?q={quote(prompt_prefix + title)}"
        xiaohongshu_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(title)}"
        felo_url = f"https://felo.ai/search?q={quote(title)}"
        description += f'<br><br>解读：<a href="{chatgpt_url}" target="_blank">ChatGPT</a>'
        description += f'、<a href="{chatgpt_url_en}" target="_blank">ChatGPT En</a>'
        description += f'、<a href="{google_url}" target="_blank">Google</a>'
        description += f'、<a href="{google_url_en}" target="_blank">Google En</a>'
        description += f'、<a href="{xiaohongshu_url}" target="_blank">小红书</a>'
        description += f'、<a href="{felo_url}" target="_blank">Felo</a>'
        

            
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