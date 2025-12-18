from rsshub.utils import fetch

domain = 'https://chuansongme.com'


def parse(post):
    item = {}
    a = post.select('a.question_link')
    if a:
        item['title'] = a[-1].get_text().strip()
        item['link'] = f"{domain}{a[-1].get('href', '')}"
    return item


def ctx(category=''):
    url = f"{domain}/{category}"
    tree = fetch(url)
    if not tree:
         return {
            'title': '传送门',
            'link': domain,
            'description': '传送门：微信公众号订阅',
            'author': 'alphardex',
            'items': []
        }
    posts = tree.select('.feed_body .pagedlist_item')
    return {
        'title': '传送门',
        'link': domain,
        'description': '传送门：微信公众号订阅',
        'author': 'alphardex',
        'items': list(map(parse, posts))
    }