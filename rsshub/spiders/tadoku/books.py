import re
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://tadoku.org'

def parse(post):
    item = {}
    item['title'] = post.css('.bl-title').css('a::text').extract_first()
    item['description'] = post.css('.bl-thumb').extract_first() + post.css('.bl-title').extract_first()
    item['link'] =  post.css('.bl-title').css('a::attr(href)').extract_first()
    return item

def ctx(category=''):
    category = category  if category != '0' else ''
    url = f"{domain}/japanese/book-search?level={category}"
    tree = fetch(url,headers=DEFAULT_HEADERS)
    posts = tree.css('.col-6.col-sm-4.col-md-3.col-lg-2.bl-wrap-small')
    return {
        'title': f'{category} Books - TADOKU.ORG',
        'link': url,
        'description': f'Book searching result - TADOKU.ORG',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }
    
