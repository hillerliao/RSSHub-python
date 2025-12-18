import requests
import json
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.weiyangx.com'


def parse(post):
    item = {}
    item['title'] = post['post_title']
    item['description'] = post['post_content']
    post_id = post['post_id']
    item['link'] = f'{domain}/{post_id}.html'
    item['pubDate'] = post['post_date'][0] + '-' + \
        post['post_date'][1] + '-' + \
        post['post_date'][2]
    return item


def ctx():
    url = f'https://www.weiyangx.com/category/express'
    res = requests.get(url, headers=DEFAULT_HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    import re
    scripts = soup.select('script')
    posts = []
    for script in scripts:
        if 'window.__INITIAL_STATE__' in script.text:
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(.*?)(;|$)', script.text, re.S)
            if match:
                try:
                    content = match.group(1).strip()
                    posts = json.loads(content)
                    break
                except (json.JSONDecodeError, IndexError):
                    continue
    
    if not posts:
        raise ValueError("Could not find or parse window.__INITIAL_STATE__ in script tags")

    items = list(map(parse, posts))
    return {
        'title': f'快讯 - 未央网',
        'description': f'快讯 - 未央网',
        'link': f'{domain}/category/express',
        'author': f'hillerliao',
        'items': items
    }
