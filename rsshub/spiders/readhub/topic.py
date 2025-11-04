import requests
import json
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://readhub.cn'
api_domain = 'https://api.readhub.cn'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['summary']
    item['link'] = f"{domain}/topic/{post['uid']}"
    item['author'] = post['siteNameDisplay']
    item['pubDate'] = post['publishDate']
    return item


def ctx(type='', uid=''):
    referer = f'{domain}/entity_topics?type=22&uid={uid}&tb=0'
    DEFAULT_HEADERS.update({'Referer': referer}) 
    type_name = 'entity' if type == '10' else 'tag'
    url = f'{api_domain}/topic/list_pro?{type_name}_id={uid}&size=10' 
    posts = requests.get(url, headers=DEFAULT_HEADERS)
    topic_name = json.loads(posts.text)['data']['self'][f'{type_name}List'][0]['name'] 

    posts = json.loads(posts.text)['data']['items']
    return {
        'title': f'{topic_name} - 主题 - Readhub',
        'link': referer,
        'description': f'"{topic_name}"动态',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }