import re
import json
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.economist.com'

def parse_gobbet(gobbet):
    item = {}
    # Remove HTML tags but keep the text
    item['title'] = BeautifulSoup(gobbet, 'html.parser').get_text()
    item['description'] = gobbet  # Keep HTML formatting for description
    item['link'] = f"{domain}/the-world-in-brief?from={item['title'][:30]}"
    return item

def ctx(category=''):
    url = f"{domain}/the-world-in-brief"
    html = fetch(url, headers=DEFAULT_HEADERS).get()
    
    # Find the __NEXT_DATA__ script
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        return {
            'title': 'World Brief - Economist',
            'link': url,
            'description': 'The world in brief: Catch up quickly on the global stories that matter',
            'author': 'hillerliao',
            'items': []
        }
    
    data = json.loads(match.group(1))
    gobbets = data.get('props', {}).get('pageProps', {}).get('content', {}).get('gobbets', [])
    
    return {
        'title': 'World Brief - Economist',
        'link': url,
        'description': 'The world in brief: Catch up quickly on the global stories that matter',
        'author': 'hillerliao',
        'items': list(map(parse_gobbet, gobbets))
    }
