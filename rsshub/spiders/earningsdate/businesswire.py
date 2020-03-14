from rsshub.utils import fetch, filter_content
from rsshub.utils import DEFAULT_HEADERS

domain = 'businesswire.com'


def parse(post):
    item = {}
    item['title'] = post.css('title::text').extract_first().strip()
    item['description'] = post.css('description::text').extract_first()
    item['link'] = post.extract().split('      ')[-2].split('>')[-1].strip()
    item['pubDate'] = post.css('pubDate::text').extract_first()
    return item


def ctx(category=''):
    tree = fetch(f"https://feed.{domain}/rss/home/?rss=G1QFDERJXkJeGVtYWA==", 
                headers=DEFAULT_HEADERS)
    posts = tree.css('item')
    items = list(map(parse, posts))
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Businesswire',
        'link': f'https://www.{domain}/portal/site/home/news/subject/?vnsId=31407',
        'description': 'Earnings Date - Businesswire',
        'author': 'hillerliao',
        'items': items
    }
