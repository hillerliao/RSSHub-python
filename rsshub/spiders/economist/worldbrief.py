import re
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.economist.com'

def parse(post):
    item = {}
    item['title'] = post.css('div').css('p').get()
    item['description'] = item['title'] 
    item['title'] = re.sub(r'<[^>]*>', '', item['title']).strip()
    item['link'] =  f"{domain}/the-world-in-brief" + '?from=' + item['title'][:30] 
    return item

def ctx(category=''):
    url = f"{domain}/the-world-in-brief"
    tree = fetch(url,headers=DEFAULT_HEADERS)
    posts = tree.css('._gobbet')
    
    return {
        'title': f'World Brief - Economist',
        'link': url,
        'description': f'The world in brief: Catch up quickly on the global stories that matter',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }
    
