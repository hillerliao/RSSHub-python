import re
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://dig.chouti.com'


def parse(post):
    item = {}
    item['title'] = re.sub(r'<[^>]*>', '', post['title']).strip()
    chouti_link = domain + '/link/' + str(post['id'])
    item['description'] = post['title']  + '<br /> <br />'  + f'<a href="{chouti_link}" target="_blank">抽屉链接</a>'
    item['link'] = post['originalUrl']
    item['pubDate'] = arrow.get(post['created_time']).isoformat()
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