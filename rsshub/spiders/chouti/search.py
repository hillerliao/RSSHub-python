import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://dig.chouti.com'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['title']
    item['link'] = 'https://dig.chouti.com/link/' + str(post['id'])
    item['pubDate'] = str(post['created_time'])[0:10]
    item['author'] = post['submitted_user']['nick']
    return item 


def ctx(category=''):
    DEFAULT_HEADERS.update({'Referer': domain}) 
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
