from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.zaobao.com'


def parse(post):
    item = {}
    item['description'] = item['title'] = post.css('div.f18.m-eps::text').extract_first()
    item['link'] = domain + post.css('a::attr(href)').extract_first()
    return item


def ctx(category=''):
    url = f"{domain}/realtime/{category}"
    tree = fetch(url,headers=DEFAULT_HEADERS)
    posts = tree.css('.col-lg-4.col-12.list-block.no-gutters')
    # print(posts)
    return {
        'title': f'{category} - 早报网即时新闻',
        'link': url,
        'description': f'{category} - 早报网即时新闻',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }