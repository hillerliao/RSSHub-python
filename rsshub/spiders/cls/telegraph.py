import requests
from rsshub.utils import DEFAULT_HEADERS
import arrow

def parse(post):
    item = {}
    item['title'] = post['title'] if post['title'] != '' else post['content']
    item['description'] = post['content']
    item['link'] = post['shareurl']
    item['pubDate'] = arrow.get(int(post['ctime'])).isoformat()
    return item


def ctx():
    url = f'https://www.cls.cn/nodeapi/telegraphList'
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.cls.cn/telegraph'
    })
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    try:
        data = res.json()
        posts = data['data']['roll_data']
    except (ValueError, KeyError) as e:
        print(f"Error decoding JSON from {url}: {e}")
        print(f"Response snippet: {res.text[:200]}")
        return {
            'title': f'电报 - 财联社',
            'link': f'https://www.cls.cn/telegraph',
            'description': f'财联社电报 (数据获取失败)',
            'author': 'hillerliao',
            'items': []
        }
    items = list(map(parse, posts))
    return {
        'title': f'电报 - 财联社',
        'link': f'https://www.cls.cn/telegraph',
        'description': f'财联社电报',
        'author': 'hillerliao',
        'items': items
    }
