from rsshub.utils import fetch

domain = 'http://www.bjnews.com.cn'


def parse(post):
    item = {}
    item['description'] = item['title'] = post.get_text()
    item['link'] = post['href']
    return item


def ctx(category=''):
    r_url = f"{domain}/{category}"
    tree = fetch(r_url)
    posts = tree.select('#waterfall-container .pin_demo > a')
    channel_title = tree.select('.cur')[0].get_text().strip()
    return {
        'title': f'{channel_title} - 新京报',
        'link': r_url,
        'description': f'新京报「{channel_title}」频道新闻',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }
