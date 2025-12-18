import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.caixin.com'


def parse(post):
    item = {}
    item['title'] = post.get('title', '')
    item['description'] = post.get('summary', '')
    item['link'] = post.get('url', '')
    item['pubDate'] = arrow.get(int(post.get('time', 0)) / 1000).isoformat()
    item['author'] = post.get('author', post.get('mediaName', ''))
    return item


def ctx(category=''):
    channel = category if category else '0'
    api_url = f"https://gateway.caixin.com/api/dataplatform/scroll/index?page=1&size=20&date=&channel={channel}"
    res = requests.get(api_url, headers=DEFAULT_HEADERS)
    res.raise_for_status()
    data = res.json()
    posts = data.get('data', {}).get('articleList', [])
    return {
        'title': '财新网滚动新闻',
        'link': 'https://www.caixin.com/search/newscroll',
        'description': '财新网滚动新闻',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }