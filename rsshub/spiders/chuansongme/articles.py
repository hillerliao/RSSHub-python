from rsshub.utils import fetch

domain = 'https://chuansongme.com'


def parse(post):
    item = {}
    item['title'] = post.css('a.question_link::text').extract()[-1].strip()
    link = f"{domain}{post.css('a.question_link::attr(href)').extract_first()}"
    item['link'] = link
    return item


def ctx(category=''):
    tree = fetch(f"{domain}/{category}")
    posts = tree.css('.feed_body .pagedlist_item')
    return {
        'title': '传送门',
        'link': domain,
        'description': '传送门：微信公众号订阅',
        'author': 'alphardex',
        'items': list(map(parse, posts))
    }