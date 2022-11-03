import requests
import json
import re
from urllib.parse import unquote 
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://s.geekbang.org'


def parse(post):
    item = {}
    item['title'] = re.sub(r'<[^>]*>', '', post['title']).strip()
    item['description'] = re.sub(r'<[^>]*>', '', post['simple_content']).strip()
    item['link'] = post['content_url']
    item['author'] = post['author']
    item['pubDate'] = post['release_time']
    return item


def ctx(category='', type=''):
    category1 = category.encode("utf-8").decode("latin-1")
    referer = f'{domain}/search/c=0/k={category1}/t={type}'
    DEFAULT_HEADERS.update({'Referer': referer}) 
    url = f'{domain}/api/gksearch/search'
    category = unquote(category, 'utf-8')
    payload = {"q":category,"t": type,"s":20,"p":1}
    posts = requests.post(url, json=payload, headers=DEFAULT_HEADERS)
    posts = json.loads(posts.text)['data']['list']
    return {
        'title': f'{category} - 搜索 - InfoQ',
        'link': f'{domain}/search/c=0/k={category}/t=0',
        'description': f'{category} - 极客邦搜索 - InfoQ',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }