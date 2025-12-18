import re
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://dig.ichouti.cn'

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
    headers = DEFAULT_HEADERS.copy()
    headers.update({'Referer': domain}) 
    post_data = {'sectionId': category}
    r_url = f'{domain}/section/links'
    try:
        response = requests.post(r_url, data=post_data, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            posts = data.get('data', [])
        else:
            print(f'API error: {data.get("msg", "Unknown error")}')
            posts = []
    except requests.RequestException as e:
        print(f'Request error: {e}')
        posts = []
    except ValueError as e:
        print(f'JSON decode error: {e}')
        posts = []
    
    return {
        'title': f'{category} - 抽屉热榜',
        'link': r_url,
        'description': f'抽屉热榜 - {r_url}',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }