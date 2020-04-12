import requests
import json
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.weiyangx.com'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['content']
    item['link'] = post['url']
    item['author'] = post['authorMeta']
    return item


def ctx(category=''):
    url = f'https://www.weiyangx.com/wp-admin/admin-ajax.php'
    q_data = {"action": "home_load_more_news",
              "postOffset": "00",
              "tagId": category,
              "_ajax_nonce": "1846edad4e"}

    res = requests.post(url, data=q_data, headers=DEFAULT_HEADERS)
    posts = json.loads(res.text)['data']
    items = list(map(parse, posts))
    return {
        'title': f'快讯 - 未央网',
        'description': f'快讯 - 未央网',
        'link': f'{domain}/category/express',
        'author': f'hillerliao',
        'items': items
    }
