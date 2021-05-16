from rsshub.utils import fetch, filter_content, DEFAULT_HEADERS

domain = 'https://www.prnewswire.com'

def parse(post):
    item = {}
    item['title'] = post.css('h3::text').getall()[1]
    item['description'] = post.css('p::text').extract_first()
    item['link'] = f"{domain}{post.css('a::attr(href)').extract_first()}"
    item['pubDate'] = post.css('small::text').extract_first()
    return item

def ctx(category=''):
    # DEFAULT_HEADERS.update({'upgrade-insecure-requests': 1})
    url = f"{domain}/news-releases/financial-services-latest-news/earnings-list/?page=1&pagesize=100"
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.css('.card-list-hr .row')
    items = list(map(parse, posts)) 
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Prnewswire',
        'link': f'{domain}/news-releases/financial-services-latest-news/earnings-list/',
        'description': 'Earnings Date - Prnewswire',
        'author': 'hillerliao',
        'items': items
    }
