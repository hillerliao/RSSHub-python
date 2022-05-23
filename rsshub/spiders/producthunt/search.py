import re
import requests
from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.producthunt.com'


def parse(post):
    item = {}
    item['title'] = post.css('a[class*="styles_title__"]::text').extract_first()
    item['description'] = post.css('a[class*="styles_tagline__"]::text').extract_first()
    item['link'] = domain + post.css('a::attr(href)').extract_first()
    return item 


def ctx(keyword='', period=''):
    DEFAULT_HEADERS.update({'Referer': domain}) 
    r_url = f'{domain}' + f'/search?q={keyword}&postedAfter={period}:days'
    tree = fetch(r_url,headers=DEFAULT_HEADERS)
    posts = tree.css('.style_layoutMain___pXHk').css('.style_px-mobile-1__DSM5j.style_px-tablet-1__R5dkv.style_pt-mobile-0__lBXpV.style_pt-desktop-6__eNi8V.style_pt-tablet-6__BJU9d.style_pt-widescreen-6__SWPD_.style_pb-mobile-7__OX0Sz.style_pb-desktop-6__EZ3zm.style_pb-tablet-6__F61Qx.style_pb-widescreen-6__UB2pW')
    print(posts)
    items = list(map(parse, posts))
    items = [item for item in items if item['title']!=None]
    return {
        'title': f'{keyword} - Producthunt',
        'link': r_url,
        'description': f'Producthunt - {r_url}',
        'author': 'hillerliao',
        'items': items
    }
