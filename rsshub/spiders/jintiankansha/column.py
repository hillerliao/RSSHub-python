from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'http://www.jintiankansha.me'


def parse(post):
    item = {}
    a_elem = post.select('a')
    if a_elem:
        item['description'] = item['title'] = a_elem[0].get_text()
        item['link'] = a_elem[0]['href']
    return item


def ctx(category=''):
    url = f'{domain}/column/{category}'
    DEFAULT_HEADERS.update({'Host': 'www.jintiankansha.me'})
    tree = fetch(url, headers=DEFAULT_HEADERS)
    # posts = tree.select('.cell.item')
    posts = tree.select('.item_title')
    items = list(map(parse, posts))

    title_elem = tree.select('title')
    column_title = title_elem[0].get_text() if title_elem else ''
    return {
        'title': f'{column_title}',
        'description': f'{category}',
        'link': url,
        'author': f'hillerliao',
        'items': items
    }
