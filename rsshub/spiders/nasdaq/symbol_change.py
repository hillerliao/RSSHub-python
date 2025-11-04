import json
import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.nasdaq.com'


def parse(post):
    item = {}
    item['title'] = post['effective'] + '，' + post['oldSymbol'] + ' -> ' + post['newSymbol']
    item['description'] = "代码变更：" + item['title'] + '。公司：' + post['companyName']
    item['link'] = domain +  post['url'] + f'?mark={post["oldSymbol"]}2{post["newSymbol"]}'
    return item


def ctx(category=''):
    url = 'https://api.nasdaq.com/api/quote/list-type-extended/symbolchangehistory'
    DEFAULT_HEADERS.update({
        'Referer': 'https://www.nasdaq.com/market-activity/stocks/symbol-change-history',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    response = requests.get(url, headers=DEFAULT_HEADERS)
    response.raise_for_status()  # 确保请求成功
    posts = json.loads(response.text)['data']['symbolChangeHistoryTable']['rows']
    
    return {
        'title': 'Stock Symbol Change History - Nasdaq',
        'link': 'https://www.nasdaq.com/market-activity/stocks/symbol-change-history',
        'description': 'View the history of stock symbol changes on Nasdaq. Stay informed on corporate actions, mergers, and rebrandings that result in symbol updates',
        'author': 'hillerliao',
        'items': list(map(parse, posts)),
    }
