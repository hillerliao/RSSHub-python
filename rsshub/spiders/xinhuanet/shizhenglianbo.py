import json

import requests

from rsshub.utils import DEFAULT_HEADERS

domain = 'http://www.news.cn'


def parse(post):
    item = {}
    item['title'] = post['Title']
    item['description'] = post['Abstract']
    item['link'] = post['LinkUrl']
    return item


def ctx():
    url = 'http://da.wa.news.cn/nodeart/page'
    posts = requests.get(
        url,
        params={'nid': '113351', 'pgnum': '1', 'cnt': '20'},
        headers=DEFAULT_HEADERS,
    ).text
    posts = json.loads(posts)['data']['list']
    return {
        'title': '新华网 - 时政联播',
        'link': url,
        'description': '新华网 - 时政联播',
        'author': 'flyingicedragon',
        'items': list(map(parse, posts)),
    }
