from rsshub.utils import fetch, filter_content, DEFAULT_HEADERS

domain = 'https://www.prnewswire.com'

def parse(post):
    item = {}
    h3_elems = post.select('h3')
    item['title'] = h3_elems[1].get_text() if len(h3_elems) > 1 else ''
    p_elem = post.select('p')
    item['description'] = p_elem[0].get_text() if p_elem else ''
    a_elem = post.select('a')
    item['link'] = f"{domain}{a_elem[0]['href']}" if a_elem else ''
    small_elem = post.select('small')
    item['pubDate'] = small_elem[0].get_text() if small_elem else ''
    return item

def ctx(category=''):
    # DEFAULT_HEADERS.update({'upgrade-insecure-requests': 1})
    url = f"{domain}/news-releases/financial-services-latest-news/earnings-list/?page=1&pagesize=100"
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.select('.card-list-hr .row')
    items = list(map(parse, posts)) 
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Prnewswire',
        'link': f'{domain}/news-releases/financial-services-latest-news/earnings-list/',
        'description': 'Earnings Date - Prnewswire',
        'author': 'hillerliao',
        'items': items
    }
