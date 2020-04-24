import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.infoq.cn'


def parse(post):
    item = {}
    item['title'] = post['article_title']
    item['description'] = f"{post['article_summary']}<br><img referrerpolicy='no-referrer' src={post.get('article_cover')}>"
    item['link'] = f"{domain}/article/{post['uuid']}"
    item['pubDate'] = post['publish_time']
    return item


def ctx(category=''):
    referer = f'{domain}/topic/{category}'
    DEFAULT_HEADERS.update({'Referer': referer}) 
    url = f'{domain}/public/v1/article/getList'
    import json
    posts = requests.post(url, json={'size': 20, 'id': category, 'type': 0}, headers=DEFAULT_HEADERS)

    posts = json.loads(posts.text)['data']
    return {
        'title': f'{category} - Topic - InfoQ',
        'link': referer,
        'description': 'InfoQ - 促进软件开发领域知识与创新的传播',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }