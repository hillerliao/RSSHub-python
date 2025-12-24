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
    # API might return createTime or created_time, or nothing
    pub_date = post.get('created_time') or post.get('createTime') or post.get('time')
    if pub_date:
        item['pubDate'] = arrow.get(pub_date).isoformat()
    else:
        item['pubDate'] = arrow.now().isoformat()
        
    user_info = post.get('submitted_user', {})
    item['author'] = user_info.get('nick', 'Unknown')
    return item 

def ctx(category=''):
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Referer': f'{domain}/page/section/links?sectionId={category}',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': domain
    }) 
    r_url = f'{domain}/section/links'
    # Use arrow to get current timestamp in microseconds or strict format if needed, 
    # but based on curl 'lastScore' seems to be a timestamp. 
    # Let's try sending dynamic timestamp or empty if it allows initial load.
    # The curl used 1766541675785.
    post_data = {
        'sectionId': category,
        'lastScore': str(arrow.now().int_timestamp * 1000)
    }
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