from rsshub.utils import DEFAULT_HEADERS
import requests
import json
from bs4 import BeautifulSoup

domain = 'https://www.weiyangx.com'


def parse(post):
    item = {}
    item['title'] = post['post_title']
    item['description'] = post['post_content']
    post_id = post['post_id']
    item['link'] = f'{domain}/{post_id}.html'
    return item


def ctx(category=''):
    url = f'https://www.weiyangx.com/tag/{category}'
    res = requests.get(url, headers=DEFAULT_HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    scripts = soup.select('script')
    if len(scripts) < 4:
        raise ValueError("Not enough script tags found")
    posts = scripts[-4].text.split('=')[-1] 
    posts = json.loads(posts)   
    # posts = tree.css('script::text')[-5].extract().split('=')[-1]
    items = list(map(parse, posts))
    return {
        'title': f'{category} - 文章 - 未央网',
        'description': f'文章 - 未央网',
        'link': f'{domain}/tag/{category}',
        'author': f'hillerliao',
        'items': items
    }
