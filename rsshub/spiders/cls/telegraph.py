import requests
from rsshub.utils import DEFAULT_HEADERS
import arrow

def parse(post):
    item = {}
    item['title'] = post['title'] if post['title'] != '' else post['content']
    item['description'] = post['content']
    item['link'] = post['shareurl']
    item['pubDate'] = arrow.get(int(post['ctime'])).isoformat()
    return item


def ctx():
    url = f'https://www.cls.cn/nodeapi/telegraphList'
    res = requests.get(url, headers=DEFAULT_HEADERS)
    posts = res.json()['data']['roll_data']
    items = list(map(parse, posts))
    return {
        'title': f'电报 - 财联社',
        'link': f'https://www.cls.cn/telegraph',
        'description': f'财联社电报',
        'author': 'hillerliao',
        'items': items
    }
