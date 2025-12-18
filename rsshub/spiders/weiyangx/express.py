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
    scripts = soup.select('script')
    if len(scripts) < 4:
        raise ValueError("Not enough script tags found")
    posts = scripts[-4].text.split('=')[-1]
    posts = json.loads(posts)
    items = list(map(parse, posts))
    return {
        'title': f'快讯 - 未央网',
        'description': f'快讯 - 未央网',
        'link': f'{domain}/category/express',
        'author': f'hillerliao',
        'items': items
    }
