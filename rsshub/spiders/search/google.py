import json
import requests
import arrow
from requests.utils import quote, unquote
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.google.com'

REQUEST_TIMEOUT = 5


def parse(word):
    item = {}
    item['title'] = word
    item['description'] = word
    item['link'] = f'{domain}/search?q=' + quote(word)
    item['pubDate'] = arrow.now().isoformat()
    item['author'] = 'Google'
    return item


def ctx(keyword=''):
    keyword = unquote(keyword)  # 防御 Vercel runtime 传入未解码的 URL 编码
    items = []
    try:
        url = f'https://suggestqueries.google.com/complete/search?client=firefox&q={quote(keyword)}'
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = json.loads(resp.text)
        for word in data[1]:
            items.append(parse(word))
    except Exception as e:
        print(f'[Google Suggest Error] {e}')
    return {
        'title': f'{keyword} - 搜索提示 - Google',
        'link': f'{domain}/search?q={quote(keyword)}',
        'description': 'Google 搜索提示',
        'author': 'hillerliao',
        'items': items
    }
