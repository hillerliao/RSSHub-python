import requests
import csv
import io
import random
from urllib.parse import quote
from rsshub.utils import DEFAULT_HEADERS
from rsshub.extensions import cache

def ctx():
    url = "https://raw.githubusercontent.com/HenryLoveMiller/ja/refs/heads/main/raz.csv"
    
    try:
        # Check cache first
        cache_key = 'raz_csv_content'
        content = cache.get(cache_key)
        
        if not content:
            # Use direct request with proper timeout if cache miss
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
            response.raise_for_status()
            content = response.text
            # Cache the CSV content for 60 minutes
            cache.set(cache_key, content, timeout=3600)
    except Exception as e:
        return {
            'title': 'RAZ Random Sentence',
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
                'title': 'RAZ Random Sentence',
                'link': url,
                'description': 'Empty content received',
                'items': []
            }
        
        # Use csv.reader first to check structure
        lines = content.splitlines()
        if len(lines) < 2:
            return {
                'title': 'RAZ Random Sentence',
                'link': url,
                'description': 'Insufficient data in CSV',
                'items': []
            }
        
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return {
                'title': 'RAZ Random Sentence',
                'link': url,
                'description': 'No valid rows found in CSV',
                'items': []
            }

        # Randomly select one row
        row = random.choice(rows)
        sentence = row.get('sentence', '').strip()
        book = row.get('book', '').strip()
        
        if not sentence:
            # Try again with another random row
            row = random.choice(rows)
            sentence = row.get('sentence', '').strip()
            book = row.get('book', '').strip()

        # Build item
        title = sentence
        description = f"{sentence} {book}" if sentence and book else sentence or book or "Random RAZ sentence"
        link = f"{url}?sentence={quote(sentence[:100])}"

        item = {
            'title': title,
            'description': description,
            'link': link,
            'pubDate': '',  # No date in CSV
        }

        return {
            'title': 'RAZ Random Sentence',
            'link': url,
            'description': 'Random sentence from RAZ CSV',
            'items': [item]
        }
    except Exception as e:
        return {
            'title': 'RAZ Random Sentence',
            'link': url,
            'description': f'Error processing data: {str(e)}',
            'items': []
        }