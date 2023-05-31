from rsshub.spiders.xinhuanet.utils import parse_html as parse
from rsshub.utils import DEFAULT_HEADERS, fetch

domain = 'http://www.news.cn'


def ctx():
    url = f'{domain}'
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.xpath('//div[@id=\'latest\']//li/a')
    return {
        'title': '新华网 - 最新播报',
        'link': url,
        'description': '新华网 - 最新播报',
        'author': 'flyingicedragon',
        'items': list(map(parse, posts)),
    }
