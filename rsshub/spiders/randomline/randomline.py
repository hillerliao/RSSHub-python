import requests
import csv
import io
import random
import os
import tempfile
try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    ebooklib = None
    epub = None

try:
    import mobi
except ImportError:
    mobi = None

try:
    import fitz
except ImportError:
    fitz = None

from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
from rsshub.utils import DEFAULT_HEADERS
from rsshub.extensions import cache
import json

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

def _extract_semantic_text(html_content, heading_hierarchy=None, split_lines=True):
    """Extract text from semantic tags like p, li, and headings, tracking hierarchical chapters."""
    if heading_hierarchy is None:
        heading_hierarchy = {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tags = ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    extracted = []
    
    
    # Pre-process <br> tags if we intend to split lines later
    # We replace them with a unique placeholder so we can differentiate them from actual text
    # This acts as a logical execution of "split items"
    BR_PLACEHOLDER = "___BR_SEP___"
    if split_lines:
        for br in soup.find_all('br'):
            br.replace_with(BR_PLACEHOLDER)
        
        # Also separate block elements to avoid merging "Block1" and "Block2" in get_text fallback
        # or when adjacent text nodes are involved
        for tag in soup.find_all(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section', 'blockquote']):
            tag.insert_after(BR_PLACEHOLDER)

    for tag in soup.find_all(tags):
        tag_name = tag.name
        # Use space as separator to preserve spacing between inline elements (like text and links)
        # But allow us to control splitting via the placeholder
        text = tag.get_text(separator=' ', strip=True)
        if not text:
            continue
            
        if tag_name.startswith('h'):
            try:
                level = int(tag_name[1])
                heading_hierarchy[level] = text
                # Clear all sub-levels
                for l in range(level + 1, 7):
                    if l in heading_hierarchy:
                        del heading_hierarchy[l]
            except (ValueError, IndexError):
                pass
        else:
            # Build breadcrumb: "H1 > H2 > H3"
            breadcrumb_parts = []
            for l in range(1, 7):
                if l in heading_hierarchy:
                    breadcrumb_parts.append(heading_hierarchy[l])
            
            breadcrumb = " > ".join(breadcrumb_parts)
            
            if split_lines:
                # Replace placeholder with newline and split
                text = text.replace(BR_PLACEHOLDER, '\n')
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        extracted.append({
                            "line_content": line,
                            "chapter": breadcrumb
                        })
            else:
                # Treat the whole tag content as one item
                # Restore <br> conceptually by replacing placeholder with space or keeping it?
                # Actually if split_lines=False (delimiter='p'), we might want to keep newlines as is for display?
                # But here we just want the text. Let's convert placeholder to newline for "one big text blob"
                text = text.replace(BR_PLACEHOLDER, '\n')
                if text.strip():
                    extracted.append({
                        "line_content": text.strip(),
                        "chapter": breadcrumb
                    })
    
    # Fallback if no semantic tags found OR if extraction yielded very few items (heuristic for "missed mixed content")
    # e.g. <p>Title</p> Sibling Text <br> Sibling Text 2
    if (not extracted or (len(extracted) <= 1 and len(html_content) > 100)) and split_lines:
        print("DEBUG: Few items found via tags. Trying full get_text fallback.")
        full_text = soup.get_text(separator=' ', strip=True)
        full_text = full_text.replace(BR_PLACEHOLDER, '\n')
        
        fallback_items = []
        for line in full_text.split('\n'):
            line = line.strip()
            if line:
                fallback_items.append(line)
        
        # Only use fallback if it yields MORE items
        if len(fallback_items) > len(extracted):
             # For fallback, we lose "chapter" info but capture missed text.
             # Convert simple strings to dicts
             return [{"line_content": c, "chapter": ""} for c in fallback_items]

    return extracted

def _extract_semantic_markdown(text):
    """Extract text from markdown headings and paragraphs, tracking hierarchical chapters."""
    lines = text.split('\n')
    extracted = []
    heading_hierarchy = {}
    
    current_para = []
    
    def flush_para():
        if current_para:
            content = " ".join(current_para).strip()
            if content:
                # Build breadcrumb
                breadcrumb_parts = []
                for l in range(1, 7):
                    if l in heading_hierarchy:
                        breadcrumb_parts.append(heading_hierarchy[l])
                extracted.append({
                    "line_content": content,
                    "chapter": " > ".join(breadcrumb_parts)
                })
            current_para.clear()

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            flush_para()
            continue
            
        if stripped_line.startswith('#'):
            flush_para()
            # Count leading #
            level = 0
            for char in stripped_line:
                if char == '#':
                    level += 1
                else:
                    break
            
            # Markdown headings should have a space after #
            # e.g. # Title
            after_hashes = stripped_line[level:]
            if after_hashes.startswith(' ') or not after_hashes:
                heading_text = after_hashes.strip()
                if heading_text:
                    heading_hierarchy[level] = heading_text
                    # Clear sub-levels
                    for l in range(level + 1, 7):
                        if l in heading_hierarchy:
                            del heading_hierarchy[l]
                continue # Headings aren't paragraphs
        
        # If it's not a heading and not empty, it's part of a paragraph
        current_para.append(stripped_line)
            
    flush_para()
    return extracted

def extract_content(response, url, user_delimiter=None):
    parsed_url = urlparse(url)
    ext = os.path.splitext(parsed_url.path)[1].lower()
    content = None
    delimiter = None
    feed_title = None

    # Determine if we should split lines based on user preference
    # Default is True (split by <br>), but if delimiter='p', we keep paragraphs intact
    split_lines = True
    if user_delimiter == 'p':
        split_lines = False

    if ext == '.epub':
        if not epub:
            return None, None, "EPUB processing not supported in Lite Mode"
        print("DEBUG: Detected EPUB file, processing...")
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=True) as tmp:
            tmp.write(response.content)
            tmp.flush()
            book = epub.read_epub(tmp.name)
            extracted_parts = []
            persistent_hierarchy = {}
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    extracted_parts.extend(_extract_semantic_text(item.get_content(), persistent_hierarchy, split_lines=split_lines))
            content = json.dumps(extracted_parts, ensure_ascii=False)
            delimiter = 'semantic'
    elif ext == '.mobi':
        if not mobi:
            return None, None, "MOBI processing not supported in Lite Mode"
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
                            html_content = f.read()
                        extracted_parts = _extract_semantic_text(html_content, heading_hierarchy={}, split_lines=split_lines)
                        content = json.dumps(extracted_parts, ensure_ascii=False)
                        delimiter = 'semantic'
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
    elif ext == '.md':
        print("DEBUG: Detected Markdown file, processing...")
        if response.encoding == 'ISO-8859-1' and 'charset' not in response.headers.get('Content-Type', '').lower():
            text = response.content.decode(response.apparent_encoding, errors='ignore')
        else:
            text = response.text
        
        extracted_parts = _extract_semantic_markdown(text)
        content = json.dumps(extracted_parts, ensure_ascii=False)
        delimiter = 'semantic'
    elif ext == '.pdf':
        if not fitz:
            return None, None, "PDF processing not supported in Lite Mode"
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
        # Handle potential encoding issues (e.g., requests defaulting to ISO-8859-1)
        if response.encoding == 'ISO-8859-1' and 'charset' not in response.headers.get('Content-Type', '').lower():
            content = response.content.decode(response.apparent_encoding, errors='ignore')
        else:
            content = response.text
            
        should_extract = False
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' in content_type or ext not in ['.csv', '.txt', '.tsv', '.json']:
            should_extract = True
        
        if should_extract and HAS_TRAFILATURA:
            # Try to preserve basic formatting (lists, bold, etc.) via HTML output
            extracted_html = trafilatura.extract(content, output_format='html', include_comments=False)
            
            # Smart Fallback: trafilatura often flattens headings into <p> tags.
            # If the source has headings but trafilatura output doesn't, 
            # or if it's a known book-like site, use raw HTML for semantic extraction.
            use_raw_html = False
            if 'gutenberg.org' in url.lower():
                use_raw_html = True
                print("DEBUG: Gutenberg URL detected, using raw HTML for structured extraction")
            elif extracted_html:
                # Compare heading counts
                soup_orig = BeautifulSoup(content, 'html.parser')
                soup_extracted = BeautifulSoup(extracted_html, 'html.parser')
                heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                
                orig_headings = len(soup_orig.find_all(heading_tags))
                extracted_headings = len(soup_extracted.find_all(heading_tags))
                
                if orig_headings > 0 and extracted_headings == 0:
                    use_raw_html = True
                    print(f"DEBUG: Trafilatura stripped {orig_headings} headings. Falling back to raw HTML.")

            if extracted_html and not use_raw_html:
                print("DEBUG: Content extracted successfully via trafilatura (HTML mode)")
                try:
                    metadata = trafilatura.extract_metadata(content)
                    if metadata and metadata.title:
                        feed_title = metadata.title
                except Exception as e:
                    print(f"DEBUG: Failed to extract metadata: {e}")
                
                # Apply semantic extraction to the simplified HTML
                extracted_parts = _extract_semantic_text(extracted_html, split_lines=split_lines)
                
                # Heuristic: If trafilatura flattened the content too much (<= 1 item) but we expect splitting,
                # fallback to raw HTML extraction to check if we can get more structure.
                if len(extracted_parts) <= 1 and split_lines:
                    print("DEBUG: Trafilatura yielded few items. Checking raw HTML for better structure...")
                    raw_parts = _extract_semantic_text(content, split_lines=split_lines)
                    if len(raw_parts) > len(extracted_parts):
                         print(f"DEBUG: Raw HTML yielded {len(raw_parts)} items (vs {len(extracted_parts)}), preferring raw HTML.")
                         extracted_parts = raw_parts
                
                content = json.dumps(extracted_parts, ensure_ascii=False)
                delimiter = 'semantic'
            elif use_raw_html or content:
                print("DEBUG: Using raw HTML for semantic extraction to preserve chapter structure")
                extracted_parts = _extract_semantic_text(content, split_lines=split_lines)
                content = json.dumps(extracted_parts, ensure_ascii=False)
                delimiter = 'semantic'
        elif should_extract and not HAS_TRAFILATURA:
            # Trafilatura not available, use raw HTML directly
            print("DEBUG: Trafilatura not available (Lite Mode). Using raw HTML extraction.")
            extracted_parts = _extract_semantic_text(content, split_lines=split_lines)
            content = json.dumps(extracted_parts, ensure_ascii=False)
            delimiter = 'semantic'
    
    return content, delimiter, feed_title

def ctx(url="https://raw.githubusercontent.com/HenryLoveMiller/ja/refs/heads/main/raz.csv", title_col=0, delimiter=None, min_length=0, include_context=False):
    
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
                content, extracted_delimiter, extracted_title = extract_content(response, url, user_delimiter=delimiter)
                if extracted_delimiter:
                    delimiter = extracted_delimiter
                if extracted_title:
                    feed_title = extracted_title
            except Exception as e:
                print(f"DEBUG: Request failed with default headers: {e}, retrying with curl...")
                headers_curl = {'User-Agent': 'curl/7.68.0'}
                response = requests.get(url, headers=headers_curl, timeout=30)
                response.raise_for_status()
                content, extracted_delimiter, extracted_title = extract_content(response, url, user_delimiter=delimiter)
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
             # Custom delimiter - could be anything like "---", "***", etc.
             delimiter_char = delimiter
             # Check if it's a multi-line delimiter (contains newlines or is surrounded by newlines in typical usage)
             # For patterns like "---" in markdown, we want to split on "\n---\n" to avoid matching "---" mid-line
             if delimiter_char and not delimiter_char.startswith('\n') and '\n' not in delimiter_char:
                 # Assume it's a line-based delimiter like "---" in markdown
                 # We'll look for it as a standalone line
                 delimiter_char = f'\n{delimiter_char}\n'
                 is_newline_delimiter = True
             elif '\n' in delimiter_char:
                 is_newline_delimiter = True
        indexed_rows = []
        fieldnames = []
        
        # If content starts with JSON array indicating semantic data, force semantic delimiter
        if content.strip().startswith('[') and '"line_content":' in content:
            delimiter = 'semantic'

        if delimiter == 'semantic':
             try:
                 if isinstance(content, str):
                     blocks = json.loads(content)
                 else:
                     blocks = content
                 for i, block in enumerate(blocks, 1):
                     indexed_rows.append((i, block))
                 fieldnames = ['line_content']
                 title_column_name = 'line_content'
             except:
                 # Fallback to newline if JSON fails
                 delimiter = 'newline'
                 is_newline_delimiter = True

        if delimiter != 'semantic' and is_newline_delimiter:
             # Normalize content to use \n for split
             content = content.replace('\r\n', '\n').replace('\r', '\n')
             
             current_line = 1
             delimiter_lines = delimiter_char.count('\n')
             # Split into blocks based on delimiter
             blocks = content.split(delimiter_char)
             for block in blocks:
                 if block.strip():
                     indexed_rows.append((current_line, {'line_content': block.strip()}))
                 # Update line count: lines in current block + lines in the delimiter that follows
                 current_line += block.count('\n') + delimiter_lines
             
             fieldnames = ['line_content']
             title_column_name = 'line_content'
        elif delimiter != 'semantic':
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

        # Build context (Source and Chapter/Line)
        if delimiter == 'semantic' and row.get('chapter'):
            context = f'来源：<a href="{url}" target="_blank">{filename}</a> | 章节：{row["chapter"]}'
        else:
            context = f'来源：<a href="{url}" target="_blank">{filename}</a> 第{line_num}行'

        description_parts = []
        
        # Add previous and next lines if include_context is True
        if include_context:
            # Find the index of the selected item in indexed_rows
            selected_index = indexed_rows.index(selected_item)
            
            # Get previous line if exists
            if selected_index > 0:
                prev_line_num, prev_row = indexed_rows[selected_index - 1]
                prev_content = prev_row.get(title_column_name, '').strip()
                if prev_content:
                    if is_newline_delimiter:
                        prev_content = prev_content.replace('\n', '<br>')
                    description_parts.append(f'<div style="color: #888; font-style: italic;">上一行 (第{prev_line_num}行): {prev_content}</div>')
            
            # Add separator before main content
            if description_parts:
                description_parts.append('<hr style="border: 1px solid #ddd; margin: 10px 0;">')
        # Build description parts
        if is_newline_delimiter:
            # Preserve internal formatting by converting newlines to <br>
            description_parts.append(title.replace('\n', '<br>'))
        else:
            # For tabular data, preserve newlines in values as well
            # The title itself is part of the description if it's not the only column
            if title_column_name not in [fn for fn in fieldnames if fn != title_column_name and fn != 'chapter']:
                description_parts.append(title.replace('\n', '<br>'))

            for fieldname in fieldnames:
                if fieldname == title_column_name or fieldname == 'chapter':
                    continue
                value = row.get(fieldname, '').strip()
                if value:
                    value_formatted = value.replace('\n', '<br>')
                    description_parts.append(f"{fieldname}: {value_formatted}")
        
        main_description = '<br>'.join(description_parts)
        
        # Add next line if include_context is True
        if include_context:
            selected_index = indexed_rows.index(selected_item)
            if selected_index < len(indexed_rows) - 1:
                next_line_num, next_row = indexed_rows[selected_index + 1]
                next_content = next_row.get(title_column_name, '').strip()
                if next_content:
                    if is_newline_delimiter:
                        next_content = next_content.replace('\n', '<br>')
                    main_description += f'<hr style="border: 1px solid #ddd; margin: 10px 0;"><div style="color: #888; font-style: italic;">下一行 (第{next_line_num}行): {next_content}</div>'
        
        if main_description:
            description = f"{context}<br><br>{main_description}"
        else:
            description = context
        
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