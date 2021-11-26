import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://dig.chouti.com'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = f"{item['title']} "
    item['link'] = 'https://dig.chouti.com/link/' + str(post['id'])
    item['pubDate'] = str(post['created_time'])[0:10]
    item['author'] = post['submitted_user']['nick']
    return item 


def ctx(category=''):
    DEFAULT_HEADERS.update({'Referer': domain}) 
    r_url = f'{domain}/publish/links/ajax?userId={category}'
    posts = requests.get(r_url, headers=DEFAULT_HEADERS).json()['data']
    user_name = posts[0]['submitted_user']['nick']
    return {
        'title': f'{user_name} - 个人主页 - 抽屉热榜',
        'link': f'{domain}/publish/links/ctu_{category}',
        'description': f'{user_name} - 个人主页 - 抽屉热榜',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }