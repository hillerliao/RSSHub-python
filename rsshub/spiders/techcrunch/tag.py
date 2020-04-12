import requests
import json
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://techcrunch.com'

def parse(post):
    item = {}
    item['title'] = post['title']['rendered']
    item['description'] = post['content']['rendered']
    item['link'] = post['link']
    item['pubDate'] = post['date_gmt']
    return item

def ctx(category=''):
    url = f'{domain}/wp-json/tc/v1/magazine?tags={category}'
    res = requests.get(url, headers=DEFAULT_HEADERS)
    res = json.loads(res.text)
    posts = res 
    items = list(map(parse, posts))
    return {
        'title': f'{category} - tag - Techcrunch',
        'description': f'{category} - tag - Techcrunch',
        'link': f'f{domain}/tag/fintech/',
        'author': f'hillerliao',
        'items': items
    }