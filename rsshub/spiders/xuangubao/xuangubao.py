import requests
import json
from rsshub.utils import DEFAULT_HEADERS


def parse(post):
    item = {}
    item['title'] = post['Title']
    item['description'] = post['Summary'] if post['Summary'] != '' \
                           else post['Title']
    item['link'] = post['OriginalUrl'] if post['OriginalUrl'] != '' else \
                    post['Url'] if post['Url'] != '' else post['ShareUrl2']
    item['author'] = post['Source'] + post['DisplayAuthor']
    item['pubDate'] = post['CreatedAt']
    return item


def ctx(type='', category=''):
    api_subpath = 'bkjMsgs' if type == 'theme' else 'subj'
    url = f'https://api.xuangubao.cn/api/pc/{api_subpath}/{category}?limit=20'
    print(url)
    res = requests.get(url, headers=DEFAULT_HEADERS)
    res = json.loads(res.text)
    posts = res['Messages']
    theme_name = res['BkjName'] if type == 'theme' else res['Subject']['Title']
    items = list(map(parse, posts))
    sub_path = '/bkj' if type == 'theme' else ''
    return {
        'title': f'{theme_name} - 主题 - 选股宝',
        'link': f'https://xuangubao.cn/subject{sub_path}/{category}',
        'description': f'{theme_name} 板块/主题动态 - 选股宝',
        'author': 'hillerliao',
        'items': items
    }
