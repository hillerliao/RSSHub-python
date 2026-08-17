import json
import re

import arrow
import requests

from rsshub.utils import DEFAULT_HEADERS

# 同花顺 7x24 实时新闻 https://news.10jqka.com.cn/realtimenews.html
# 页面新闻列表通过 thsRss JS 变量异步加载,接口返回 GBK 编码
API_MAP = {
    'news': (
        'https://stock.10jqka.com.cn/thsgd/ywjh.js',
        '要闻直播',
        'https://news.10jqka.com.cn/realtimenews.html',
    ),
    'econ': (
        'https://stock.10jqka.com.cn/thsgd/jjsj.js',
        '经济数据',
        'https://news.10jqka.com.cn/realtimenews.html',
    ),
}

# 接口超时(避免上游慢导致网关 504)
REQUEST_TIMEOUT = 8


def fetch(category='news'):
    """获取指定分类的快讯列表,返回 thsRss.item 列表"""
    url = API_MAP[category][0]
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Referer': 'https://news.10jqka.com.cn/realtimenews.html',
        'Accept': 'application/javascript, */*;q=0.8',
    })
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    # 接口为 GBK 编码(含中文),按字节解码,失败则回退 utf-8
    raw = res.content
    try:
        text = raw.decode('gbk')
    except UnicodeDecodeError:
        text = raw.decode('utf-8', errors='ignore')
    match = re.search(r'item:(\[.*\])', text, re.S)
    if not match:
        return []
    return json.loads(match.group(1))


def parse(post):
    item = {}
    item['title'] = (post.get('title') or '').strip()
    item['description'] = post.get('content') or post.get('title') or ''
    item['link'] = post.get('curl') or post.get('url') or ''
    item['author'] = post.get('source') or '同花顺'
    pub = post.get('pubDate') or ''
    try:
        item['pubDate'] = arrow.get(pub, 'YYYY/MM/DD HH:mm').isoformat()
    except (ValueError, TypeError):
        try:
            item['pubDate'] = arrow.get(pub).isoformat()
        except (ValueError, TypeError):
            item['pubDate'] = arrow.now().isoformat()
    return item


def ctx(category='news'):
    if category not in API_MAP:
        category = 'news'
    url, name, page = API_MAP[category]

    try:
        posts = fetch(category)
    except Exception as e:
        print(f'[ths/realtimenews] Fetch failed: {e}')
        posts = []

    items = []
    for post in posts:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f'[ths/realtimenews] Skipping bad item: {e}')

    return {
        'title': f'{name} - 同花顺7x24实时',
        'link': page,
        'description': f'同花顺 7x24 实时新闻 - {name}',
        'author': '同花顺',
        'items': items,
    }
