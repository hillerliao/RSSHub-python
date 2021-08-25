from icecream import ic
from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS


domain = 'https://youwuqiong.com'

def get_content(url):
    tree = fetch(url=url,headers=DEFAULT_HEADERS)
    content = tree.css('.single-content').get()
    return content

def parse(post):
    item = {}
    item['description'] = post.css('p::text').get()
    item['title'] = post.css('a::text')[1].get()
    item['link'] = post.css('a::attr(href)')[1].get()
    item['pubDate'] = post.css('time::text').extract_first()
    # item['description'] = get_content(item['link'])
    # ic(item['description'])
    return item


def ctx(author=''):
    url = f"{domain}/author/{author}"
    tree = fetch(url=url,headers=DEFAULT_HEADERS)
    html = tree.css('body')
    mp_name = html.css('h1::text').get().split('：')[-1] 
    mp_description = html.css('.archive-description::text').get()
    posts = html.css('.entry-content-wrap')
    return {
        'title': f'{mp_name} - 公众号',
        'link': url,
        'description': mp_description,
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }