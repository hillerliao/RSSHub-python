from icecream import ic
from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS


domain = 'https://youwuqiong.com'

def get_content(url):
    tree = fetch(url=url,headers=DEFAULT_HEADERS)
    content_elem = tree.select('.single-content')
    content = content_elem[0].decode_contents() if content_elem else ''
    return content

def parse(post):
    item = {}
    p_elem = post.select('p')
    item['description'] = p_elem[0].get_text() if p_elem else ''
    a_elems = post.select('a')
    if len(a_elems) > 1:
        item['title'] = a_elems[1].get_text()
        item['link'] = a_elems[1]['href']
    time_elem = post.select('time')
    item['pubDate'] = time_elem[0].get_text() if time_elem else ''
    # item['description'] = get_content(item['link'])
    # ic(item['description'])
    return item


def ctx(author=''):
    url = f"{domain}/author/{author}"
    tree = fetch(url=url,headers=DEFAULT_HEADERS)
    html = tree.select('body')[0]
    h1_elem = html.select('h1')
    mp_name = h1_elem[0].get_text().split('：')[-1] if h1_elem else ''
    desc_elem = html.select('.archive-description')
    mp_description = desc_elem[0].get_text() if desc_elem else ''
    posts = html.select('.entry-content-wrap')
    return {
        'title': f'{mp_name} - 公众号',
        'link': url,
        'description': mp_description,
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }