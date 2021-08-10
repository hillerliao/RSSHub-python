from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://weixin.sogou.com'

def parse(post):
    item = {}

    if dd_num > 1:
        item['description'] = item['title'] = post.css('a::text').get()
        item['link'] = domain + post.css('a::attr(href)').get()
        item['pubDate'] = post.css('script::text').get().split('\'')[-2]
    else:
        item['description'] = item['title'] = '近期没有新文章'
        item['link'] = url
    return item

def ctx(gh=''):
    global url 
    url = f"{domain}/weixin?type=1&s_from=input&query={gh}&ie=utf8&_sug_=n&_sug_type_=&w=01019900&sut=1554&sst0=1628603087755&lkt=0%2C0%2C0"
    tree = fetch(url=url, headers=DEFAULT_HEADERS)
    global dd_num
    dd_num = len( tree.css('dd') )
    posts = [ tree.css('dd')[-1] ]
    mp_name = tree.css('p.tit a::text').get()
    mp_description = tree.css('dd::text')[0].get()
    return {
        'title': f'{mp_name}-公众号',
        'link': url,
        'description': mp_description,
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }