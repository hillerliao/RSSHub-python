from rsshub.spiders.xinhuanet.utils import parse_html as parse
from rsshub.utils import DEFAULT_HEADERS, fetch

domain = 'http://www.news.cn/world/index.html'


def ctx():
    url = f'{domain}'
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.xpath('//div[@id=\'recommendDepth\']//a')
    return {
        'title': '新华网 - 国际要闻',
        'link': url,
        'description': '新华网 - 国际要闻',
        'author': 'flyingicedragon',
        'items': list(map(parse, posts)),
    }
