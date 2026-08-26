import json
import requests
import arrow
from requests.utils import quote, unquote
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.bing.com'

REQUEST_TIMEOUT = 5


def parse(word):
    item = {}
    item['title'] = word
    item['description'] = word
    item['link'] = f'{domain}/search?q=' + quote(word)
    item['pubDate'] = arrow.now().isoformat()
    item['author'] = 'Bing'
    return item


def ctx(keyword=''):
    keyword = unquote(keyword)  # 防御 Vercel runtime 传入未解码的 URL 编码
    items = []
    try:
        url = f'https://api.bing.com/osjson.aspx?query={quote(keyword)}'
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = json.loads(resp.text)
        for word in data[1]:
            items.append(parse(word))
    except Exception as e:
        print(f'[Bing Suggest Error] {e}')
    return {
        'title': f'{keyword} - 搜索提示 - Bing',
        'link': f'{domain}/search?q={quote(keyword)}',
        'description': 'Bing 搜索提示',
        'author': 'hillerliao',
        'items': items
    }
