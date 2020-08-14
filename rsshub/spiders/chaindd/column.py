from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.chaindd.com'


def parse(post):
    item = {}
    item['title'] = post.css('a::text').extract_first()
    item['description'] = post.css('p::text').extract_first()
    item['link'] = f"{domain}{post.css('a::attr(href)').extract_first()}"
    item['author'] = post.css('a.name::text').extract_first()
    return item


def ctx(category=''):
    DEFAULT_HEADERS.update({'Referer': f'https://www.chaindd.com/column/{category}'}) 
    tree = fetch(f"{domain}/column/{category}")
    posts = tree.css('li .cont')
    return {
        'title': f'链得得栏目{category}最新文章',
        'link': f'{domain}/column/{category}',
        'description': f'链得得栏目{category}最新文章',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }