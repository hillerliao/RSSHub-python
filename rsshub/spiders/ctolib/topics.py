from rsshub.utils import fetch

domain = 'https://www.ctolib.com'


def parse(post):
    item = {}
    title_elem = post.select('a.title')
    item['title'] = title_elem[0].get_text() if title_elem else ''
    abstract_elem = post.select('p.abstract')
    item['description'] = abstract_elem[0].get_text() if abstract_elem else ''
    if title_elem:
        item['link'] = f"{domain}{title_elem[0]['href']}"
    return item


def ctx(category=''):
    tree = fetch(f'{domain}/python/topics/{category}')
    posts = tree.select('ul.note-list li')
    return {
        'title': 'CTOLib码库',
        'link': domain,
        'description': 'Python开发社区',
        'author': 'alphardex',
        'items': list(map(parse, posts))
    }