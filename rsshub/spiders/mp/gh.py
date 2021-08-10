from rsshub.utils import fetch

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
    url = f"{domain}/weixin?query={gh}"
    tree = fetch(url)
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