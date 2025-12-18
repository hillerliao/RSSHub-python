import re
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://tadoku.org'

def parse(post):
    item = {}
    title_elem = post.select('.bl-title a')
    item['title'] = title_elem[0].get_text() if title_elem else ''
    thumb_elem = post.select('.bl-thumb')
    title_full_elem = post.select('.bl-title')
    item['description'] = (thumb_elem[0].decode_contents() if thumb_elem else '') + (title_full_elem[0].decode_contents() if title_full_elem else '')
    item['link'] = title_elem[0]['href'] if title_elem else ''
    return item

def ctx(category=''):
    category = category  if category != '0' else ''
    url = f"{domain}/japanese/book-search?level={category}"
    tree = fetch(url,headers=DEFAULT_HEADERS)
    posts = tree.select('.col-6.col-sm-4.col-md-3.col-lg-2.bl-wrap-small')
    return {
        'title': f'{category} Books - TADOKU.ORG',
        'link': url,
        'description': f'Book searching result - TADOKU.ORG',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }
    
