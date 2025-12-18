from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.zaobao.com'


def parse(post):
    item = {}
    title_elem = post.select('a.article-link')
    title_text = title_elem[0].get_text() if title_elem else ''
    # Decode unicode escapes if present
    try:
        item['description'] = item['title'] = title_text.encode('latin1').decode('utf-8')
    except:
        item['description'] = item['title'] = title_text
    link_elem = post.select('a.article-link')
    item['link'] = domain + link_elem[0]['href'] if link_elem else ''
    return item


def ctx(category=''):
    url = f"{domain}/realtime/{category}"
    headers = DEFAULT_HEADERS.copy()
    tree = fetch(url, headers=headers)
    if tree is None:
        return {
            'title': f'{category} - 早报网即时新闻',
            'link': url,
            'description': f'{category} - 早报网即时新闻',
            'author': 'hillerliao',
            'items': []
        }
    posts = tree.select('div.peer-hover\\:text-blue-900')
    # print(posts)
    return {
        'title': f'{category} - 早报网即时新闻',
        'link': url,
        'description': f'{category} - 早报网即时新闻',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }