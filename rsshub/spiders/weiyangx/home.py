import requests
import json
from parsel import Selector
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.weiyangx.com'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['content']
    post_id = post['id']
    item['link'] = f'{domain}/{post_id}.html'
    return item


def ctx():
    url = f'https://www.weiyangx.com/'
    res = requests.get(url, headers=DEFAULT_HEADERS)
    res = Selector(res.text)
    posts = res.css('script::text')[-5].extract().split('=')[-1]
    posts = json.loads(posts)
    items = list(map(parse, posts))
    return {
        'title': f'快讯 - 未央网',
        'description': f'快讯 - 未央网',
        'link': f'{domain}/category/express',
        'author': f'hillerliao',
        'items': items
    }
