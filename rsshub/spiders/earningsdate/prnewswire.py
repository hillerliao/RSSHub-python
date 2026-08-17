from rsshub.utils import fetch, filter_content, DEFAULT_HEADERS

domain = 'https://www.prnewswire.com'

def parse(post):
    item = {}
    h3 = post.select_one('h3')
    small_elem = h3.select_one('small') if h3 else None
    item['pubDate'] = small_elem.get_text().strip() if small_elem else ''
    if small_elem:
        small_elem.extract()
    item['title'] = h3.get_text().strip() if h3 else ''
    p_elem = post.select('p')
    item['description'] = p_elem[0].get_text() if p_elem else ''
    a_elem = post.select_one('a.newsreleaseconsolidatelink')
    item['link'] = f"{domain}{a_elem['href']}" if a_elem else ''
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
