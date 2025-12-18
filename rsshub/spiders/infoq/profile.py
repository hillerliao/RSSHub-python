import requests
import json
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.infoq.cn'


def parse(post):
    item = {}
    item['title'] = post['article_title']
    item['description'] = f"{post['article_summary']}<br><img referrerpolicy='no-referrer' src={post.get('article_cover')}>"
    item['link'] = f"{domain}/article/{post['uuid']}"
    item['pubDate'] = post['publish_time']
    return item


def ctx(category=''):
    referer = f'{domain}/profile/{category}/publish'
    headers = DEFAULT_HEADERS.copy()
    headers.update({'Referer': referer}) 
    url = f'{domain}/public/v1/user/getListByAuthor'
    posts = requests.post(url, json={'size': 12, 'id': category, 'type': 0}, headers=headers)
    tree = fetch(referer,headers=headers)
    title_elem = tree.select('title') if tree else []
    feed_title = title_elem[0].get_text() if title_elem else ''
    posts = json.loads(posts.text)['data']
    return {
        'title': f'{feed_title} - Profile - InfoQ',
        'link': referer,
        'description': 'InfoQ - 促进软件开发领域知识与创新的传播',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }