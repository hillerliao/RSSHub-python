import requests
import json
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
    url = f'https://www.weiyangx.com/wp-admin/admin-ajax.php'
    q_data = {"action": "load_more_express",
              "offset": "00",
              "category": "29817",
              "_ajax_nonce": "235111d38c"}

    res = requests.post(url, data=q_data, headers=DEFAULT_HEADERS)
    posts = json.loads(res.text)['expressList']
    items = list(map(parse, posts))
    return {
        'title': f'快讯 - 未央网',
        'description': f'快讯 - 未央网',
        'link': f'{domain}/category/express',
        'author': f'hillerliao',
        'items': items
    }
