import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.yfchuhai.com'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['content']
    item['link'] = f"https://www.yfchuhai.com/news/{post['id']}.html"
    #item['pubDate'] = post['createTime']
    item['author'] = post['source']
    return item 


def ctx(category=''):
    DEFAULT_HEADERS.update({'Referer': 'https://www.yfchuhai.com/news/'}) 
    r_url = f'{domain}/api/News/getList'
    print(r_url)
    posts = requests.get(r_url, headers=DEFAULT_HEADERS).json()['data']['list']
    user_name = posts[0]
    return {
        'title': '快讯 - 扬帆出海',
        'link': 'https://www.yfchuhai.com/news/',
        'description': '快讯 - 扬帆出海',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }