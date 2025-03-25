import json
import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://api.nasdaq.com'


def parse(post):
    item = {}
    item['title'] = post['effective'] + '，' + post['oldSymbol'] + ' -> ' + post['newSymbol']
    item['description'] = item['title'] + '。公司：' + post['companyName']
    item['link'] = post['url']
    return item


def ctx(category=''):
    url = f'https://www.nasdaq.com/market-activity/stocks/symbol-change-history'
    DEFAULT_HEADERS.update({'Referer': f'https://www.chaindd.com/column/{category}'}) 
    print(url)
    posts = requests.get(
        url,
        headers=DEFAULT_HEADERS,
    ).text
    posts = json.loads(posts)['data']['rows']
    return {
        'title': 'Stock Symbol Change History - Nasdaq',
        'link': f'https://www.nasdaq.com/market-activity/stocks/symbol-change-history',
        'description': 'View the history of stock symbol changes on Nasdaq. Stay informed on corporate actions, mergers, and rebrandings that result in symbol updates',
        'author': 'hillerliao',
        'items': list(map(parse, posts)),
    }
