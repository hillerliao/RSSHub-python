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
import fitz

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
    elif ext == '.pdf':
        print("DEBUG: Detected PDF file, processing...")
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as tmp:
                tmp.write(response.content)
                tmp.flush()
                doc = fitz.open(tmp.name)
                extracted_parts = []
                for page in doc:
                    text = page.get_text()
                    if text:
                        extracted_parts.append(text)
                doc.close()
                content_all = '\n'.join(extracted_parts)
                
                # Heuristic to rejoin lines into paragraphs
                # 1. Standardize line endings
                content_all = content_all.replace('\r\n', '\n').replace('\r', '\n')
                
                # 2. Identify paragraphs by double (or more) newlines
                paragraphs = []
                current_paragraph = []
                
                for line in content_all.split('\n'):
                    stripped = line.strip()
                    if not stripped:
                        if current_paragraph:
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                        continue
                    current_paragraph.append(stripped)
                
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                
                content = '\n'.join(paragraphs)
                delimiter = 'newline'
        except Exception as e:
            print(f"DEBUG: PDF extraction failed: {e}")
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

    # Parse content
    try:
        if not content:
            return {
                'title': feed_title,
                'link': url,
                'description': 'Empty content received',
                'items': []
            }
        
        # Determine delimiter
        is_newline_delimiter = False
        if not delimiter:
            delimiter_char = ','
        elif delimiter.lower() == 'tab':
            delimiter_char = '\t'
        elif delimiter.lower() == 'newline':
             delimiter_char = '\n'
             is_newline_delimiter = True
        elif delimiter.lower() == 'double_newline':
             delimiter_char = '\n\n'
             is_newline_delimiter = True
        elif delimiter.lower() == 'triple_newline':
             delimiter_char = '\n\n\n'
             is_newline_delimiter = True
        elif delimiter.lower() == 'quadruple_newline':
             delimiter_char = '\n\n\n\n'
             is_newline_delimiter = True
        elif delimiter.lower() == 'quintuple_newline':
             delimiter_char = '\n\n\n\n\n'
             is_newline_delimiter = True
        else:
             delimiter_char = delimiter
             if '\n' in delimiter_char:
                 is_newline_delimiter = True
        indexed_rows = []
        fieldnames = []
        
        if is_newline_delimiter:
             # Normalize content to use \n for split
             content = content.replace('\r\n', '\n').replace('\r', '\n')
             # Split into blocks based on delimiter
             blocks = content.split(delimiter_char)
             for i, block in enumerate(blocks, 1):
                 if block.strip():
                     indexed_rows.append((i, {'line_content': block.strip()}))
             fieldnames = ['line_content']
             title_column_name = 'line_content'
        else:
            # For CSV/TSV, we use DictReader but track the actual line number
            # DictReader doesn't expose line numbers of the original file easily if we just pass a string
            # We skip empty lines manually to find the header
            csv_file = io.StringIO(content)
            reader = csv.reader(csv_file, delimiter=delimiter_char)
            
            header_found = False
            for row_idx, row in enumerate(reader, 1):
                if not header_found:
                    if any(cell.strip() for cell in row):
                        fieldnames = row
                        header_found = True
                        # We don't add the header as a data row
                    continue
                
                # It's a data row
                if not any(cell.strip() for cell in row):
                    continue
                
                # Map row to dict
                row_dict = {}
                for i, field in enumerate(fieldnames):
                    if i < len(row):
                        row_dict[field] = row[i]
                    else:
                        row_dict[field] = ""
                
                indexed_rows.append((row_idx, row_dict))

        if not indexed_rows:
            msg = 'No valid data rows found'
            if is_newline_delimiter:
                 msg = 'No non-empty lines found'
            return {
                'title': feed_title,
                'link': url,
                'description': msg,
                'items': []
            }

        # Validate title_col is within range
        if not is_newline_delimiter:
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
        line_num, row = selected_item
        title = row.get(title_column_name, '').strip()

        # Build description
        if is_newline_delimiter:
            description = title
        else:
            description_parts = [title]
            for i, fieldname in enumerate(fieldnames):
                if i == title_col:
                    continue
                value = row.get(fieldname, '').strip()
                if value:
                    description_parts.append(f"{fieldname}: {value}")
            description = '<br>'.join(description_parts)
        
        # Add original line number and source link
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