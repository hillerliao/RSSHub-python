from rsshub.utils import fetch

domain = 'http://www.caixin.com'


def parse(post):
    item = {}
    item['title'] = post.css('a::text').extract_first()
    item['description'] = post.css('p::text').extract_first()
    item['link'] = post.css('a::attr(href)').extract_first()
    item['pubDate'] = post.css('span::text').extract_first()
    return item


def ctx(category=''):
    tree = fetch(f"{domain}/search/scroll/{category}.jsp")
    posts = tree.css('dl')
    channel_title = tree.css('b').css('b::text').extract_first()
    return {
        'title': channel_title,
        'link': f'{domain}/search/scroll/{category}.jsp',
        'description': '财新网滚动新闻',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }