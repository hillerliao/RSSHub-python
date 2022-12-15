import re
import json

from bs4 import BeautifulSoup    
import undetected_chromedriver as uc

from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.producthunt.com'


def parse(post):
    item = {}
    item['title'] = post['name']
    item['description'] = post['tagline']
    item['link'] = post['url']
    return item 


def ctx2(keyword='', period=''):
    DEFAULT_HEADERS.update({'Referer': domain}) 
    r_url = f'{domain}' + f'/search?q={keyword}&postedAfter={period}:days'    
    browser = uc.Chrome()
    browser.get(r_url)
    import time
    time.sleep(3)
    html = browser.page_source

    soup = BeautifulSoup(html, 'html.parser')
    script = soup.find('script', id='__NEXT_DATA__')
    data = json.loads(script.text)['props']['apolloState']
    browser.quit()
    posts = [ v for k, v in data.items() if k.startswith('Product')] 
    
    items = list(map(parse, posts))
    
    return {
        'title': f'{keyword} - Producthunt',
        'link': r_url,
        'description': f'{keyword} - Producthunt',
        'author': 'hillerliao',
        'items': items
    }