import json
import requests
from rsshub.utils import DEFAULT_HEADERS
from cachetools import TTLCache

domain = 'https://www.nasdaq.com'

# 缓存数据，设置缓存大小为 1，TTL 为 300 秒（5 分钟）
cache = TTLCache(maxsize=1, ttl=300)


def parse(post):
    item = {}
    item['title'] = post['effective'] + '，' + post['oldSymbol'] + ' -> ' + post['newSymbol']
    item['description'] = "代码变更：" + item['title'] + '。公司：' + post['companyName']
    item['link'] = domain +  post['url'] + f'?mark={post["oldSymbol"]}2{post["newSymbol"]}'
    return item


def ctx(category=''):
    if 'cached_data' in cache:
        return cache['cached_data']  # 返回缓存数据

    url = 'https://api.nasdaq.com/api/quote/list-type-extended/symbolchangehistory'
    DEFAULT_HEADERS.update({
        'Referer': 'https://www.nasdaq.com/market-activity/stocks/symbol-change-history',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)  # 设置超时时间为 10 秒
        response.raise_for_status()
        posts = json.loads(response.text)['data']['symbolChangeHistoryTable']['rows']
    except requests.exceptions.RequestException as e:
        return {
            'title': 'Stock Symbol Change History - Nasdaq',
            'link': 'https://www.nasdaq.com/market-activity/stocks/symbol-change-history',
            'description': f'Error fetching data: {e}',
            'author': 'hillerliao',
            'items': [],
        }

    result = {
        'title': 'Stock Symbol Change History - Nasdaq',
        'link': 'https://www.nasdaq.com/market-activity/stocks/symbol-change-history',
        'description': 'View the history of stock symbol changes on Nasdaq. Stay informed on corporate actions, mergers, and rebrandings that result in symbol updates',
        'author': 'hillerliao',
        'items': list(map(parse, posts)),
    }

    cache['cached_data'] = result  # 缓存结果
    return result
