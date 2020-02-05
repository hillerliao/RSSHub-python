from rsshub.utils import fetch, filter_content

domain = 'https://www.prnewswire.com'

def parse(post):
    item = {}
    item['title'] = post.css('a::text').extract_first()
    item['description'] = post.css('p::text').extract_first()
    item['link'] = f"{domain}{post.css('a::attr(href)').extract_first()}"
    item['pubDate'] = post.css('small::text').extract_first()
    return item

def ctx(category=''):
    tree = fetch(f"{domain}/news-releases/financial-services-latest-news/earnings-list/?page=5&pagesize=100")
    posts = tree.css('.card-list-hr .col-sm-8')
    items = list(map(parse, posts)) 
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Prnewswire',
        'link': f'{domain}/news-releases/financial-services-latest-news/earnings-list/',
        'description': 'Earnings Date - Prnewswire',
        'author': 'hillerliao',
        'items': items
    }