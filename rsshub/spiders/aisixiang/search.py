from urllib.parse import quote, unquote
from rsshub.utils import fetch, DEFAULT_HEADERS


domain = 'https://www.aisixiang.com'


def parse(post):
    item = {}
    links = post.select('a')
    if links:
        item['description'] = item['title'] = links[-1].get_text()
        item['link'] = f"{domain}{links[-1].get('href', '')}"
    span = post.select_one('span')
    item['pubDate'] = span.get_text() if span else ''
    return item


def ctx(category='', keywords=''):
    keywords = unquote(keywords,encoding='utf-8')
    keywords_gbk = quote(keywords, encoding='gbk')
    url = f"{domain}/data/search.php?keyWords={keywords_gbk}&searchfield={category}"
    tree = fetch(url, headers=DEFAULT_HEADERS)
    if not tree:
        return {
            'title': f'{keywords} - {category}搜索 - 爱思想',
            'link': url,
            'description': f'{keywords} - {category}搜索 - 爱思想',
            'author': 'hillerliao',
            'items': []
        }
    posts = tree.select('.search_list li')
    return {
        'title': f'{keywords} - {category}搜索 - 爱思想',
        'link': url,
        'description': f'{keywords} - {category}搜索 - 爱思想',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }
