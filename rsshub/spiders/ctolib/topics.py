from rsshub.utils import fetch

domain = 'https://www.ctolib.com'


def parse(post):
    item = {}
    item['title'] = post.css('a.title::text').extract_first()
    item['description'] = post.css('p.abstract::text').extract_first()
    item['link'] = f"{domain}{post.css('a.title::attr(href)').extract_first()}"
    return item


def ctx(category=''):
    tree = fetch(f'{domain}/python/topics/{category}')
    posts = tree.css('ul.note-list li')
    return {
        'title': 'CTOLib码库',
        'link': domain,
        'description': 'Python开发社区',
        'author': 'alphardex',
        'items': list(map(parse, posts))
    }