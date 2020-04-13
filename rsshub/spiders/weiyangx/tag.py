from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.weiyangx.com'


def parse(post):
    item = {}
    item['title'] = post.css('h2::text').extract_first()
    item['description'] = post.css('p::text').extract_first()
    item['link'] = post.css('a::attr(href)').extract_first()
    return item


def ctx(category=''):
    url = f'https://www.weiyangx.com/tag/{category}'
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.css('.category-post-node')
    items = list(map(parse, posts))
    return {
        'title': f'{category} - 文章 - 未央网',
        'description': f'文章 - 未央网',
        'link': f'{domain}/tag/{category}',
        'author': f'hillerliao',
        'items': items
    }
