from urllib.parse import quote, unquote
from rsshub.utils import fetch, DEFAULT_HEADERS


domain = 'https://www.aisixiang.com'


def parse(post):
    item = {}
    item['description'] = item['title'] = post.css('a::text').getall()[-1]
    item['link'] = f"{domain}{post.css('a::attr(href)').getall()[-1]}"
    item['pubDate'] = post.css('span::text').extract_first()
    return item


def ctx(category='', keywords=''):
    keywords = unquote(keywords,encoding='utf-8')
    keywords_gbk = quote(keywords, encoding='gbk')
    url = f"{domain}/data/search.php?keyWords={keywords_gbk}&searchfield={category}"
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.css('.search_list').css('li')
    return {
        'title': f'{keywords} - {category}搜索 - 爱思想',
        'link': url,
        'description': f'{keywords} - {category}搜索 - 爱思想',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }
