import re
import requests
from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.producthunt.com'


def parse(post):
    item = {}
    item['title'] = post.css('h3 a::text').extract_first()
    item['description'] = post.css('.styles_font__m46I_.styles_grey__YlBrh.styles_small__lLD08.styles_normal__FGFK7.styles_tagline__j29pO.styles_lineHeight__kGlRn::text').extract_first()
    item['link'] = domain + post.css('a::attr(href)').extract_first()
    return item 


def ctx(keyword='', period=''):
    DEFAULT_HEADERS.update({'Referer': domain}) 
    r_url = f'{domain}' + f'/search?q={keyword}&postedAfter={period}:days'
    print(r_url)
    tree = fetch(r_url,headers=DEFAULT_HEADERS)
    posts = tree.css('.styles_item__Sn_12')
    print(posts)
    return {
        'title': f'{keyword} - Producthunt',
        'link': r_url,
        'description': f'Producthunt - {r_url}',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }
