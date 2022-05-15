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
    from urllib.parse import unquote
    category = unquote(category, 'utf-8')
    r_url = f'{domain}/search/show'
    post_data = {'words':category,'searchType':'2','linkType':'ALL', 'subjectId':'-1'}
    posts = requests.post(r_url, data=post_data, headers=DEFAULT_HEADERS).json()['data']['linksList']
    return {
        'title': f'{category} - 抽屉热榜',
        'link': r_url,
        'description': f'抽屉热榜 - {r_url}',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }
