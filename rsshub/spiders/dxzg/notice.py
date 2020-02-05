from rsshub.utils import fetch

domain = 'http://www.dxzq.net'


def parse(post):
    item = {}
    item['description'] = item['title'] = post.css('a::text').extract_first()
    link = f"{domain}{post.css('a::attr(href)').extract_first()}"
    item['link'] = link 
    item['pubDate'] = post.css('span.time::text').extract_first()
    return item


def ctx(category=''):
    tree = fetch(f"{domain}/main/zcgl/zxgg/index.shtml?catalogId=1,5,228")
    posts = tree.css('.news_list li')
    return {
        'title': '东兴资管产品最新公告',
        'link': f'{domain}/main/zcgl/zxgg/index.shtml?catalogId=1,5,228',
        'description': '东兴资管产品最新公告',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }