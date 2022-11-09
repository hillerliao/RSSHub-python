import json
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://api.bbwc.cn'


def parse(post):
    item = {}
    item['title'] = post['title'] 
    item['description'] = post['content']
    item['link'] = post['link']
    item['pubDate'] = arrow.get(int(post['inputtime'])).isoformat()
    item['author'] = 'Bloomberg'
    return item 


def ctx(category=''):
    url = f'{domain}/web/Newsflash/articlelist/l/{category}/device/30/appid/1/p/1/ps/100'
    posts = requests.get(url)
    print(posts)
    posts = json.loads(posts.text)['data']['list']           
    return {
        'title': f'{category} - 即时新闻 - 商业周刊',
        'link': f'{domain}/realtime/index.html',
        'description': f'抓取彭博商业周刊即时新闻栏目的快讯',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }