from rsshub.utils import fetch, filter_content
from rsshub.utils import DEFAULT_HEADERS

domain = 'businesswire.com'


def parse(post):
    item = {}
    title_elem = post.select('title')
    item['title'] = title_elem[0].get_text().strip() if title_elem else ''
    desc_elem = post.select('description')
    item['description'] = desc_elem[0].get_text() if desc_elem else ''
    item['link'] = post.decode_contents().split('      ')[-2].split('>')[-1].strip()
    pubdate_elem = post.select('pubDate')
    item['pubDate'] = pubdate_elem[0].get_text() if pubdate_elem else ''
    return item


def ctx(category=''):
    tree = fetch(f"https://feed.{domain}/rss/home/?rss=G1QFDERJXkJeGVtYWA==", 
                headers=DEFAULT_HEADERS)
    posts = tree.select('item')
    items = list(map(parse, posts))
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Businesswire',
        'link': f'https://www.{domain}/portal/site/home/news/subject/?vnsId=31407',
        'description': 'Earnings Date - Businesswire',
        'author': 'hillerliao',
        'items': items
    }
