from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.chaindd.com'


def parse(post):
    item = {}
    a = post.select_one('a')
    p = post.select_one('p')
    item['title'] = a.get_text() if a else ''
    item['description'] = p.get_text() if p else ''
    item['link'] = f"{domain}{a.get('href', '')}" if a else ''
    name_el = post.select_one('a.name')
    item['author'] = name_el.get_text() if name_el else ''
    return item


def ctx(category=''):
    DEFAULT_HEADERS.update({'Referer': f'https://www.chaindd.com/column/{category}'}) 
    url = f"{domain}/column/{category}"
    tree = fetch(url)
    if not tree:
         return {
            'title': f'链得得栏目{category}最新文章',
            'link': url,
            'description': f'链得得栏目{category}最新文章',
            'author': 'hillerliao',
            'items': []
        }
    posts = tree.select('li .cont')
    return {
        'title': f'链得得栏目{category}最新文章',
        'link': url,
        'description': f'链得得栏目{category}最新文章',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }