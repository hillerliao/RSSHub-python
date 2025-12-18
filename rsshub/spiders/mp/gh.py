from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://weixin.sogou.com'

def parse(post, dd_num, url):
    item = {}

    if dd_num > 1:
        a_elem = post.select('a')
        if a_elem:
            item['description'] = item['title'] = a_elem[0].get_text()
            item['link'] = domain + a_elem[0]['href']
        script_elem = post.select('script')
        if script_elem:
            item['pubDate'] = script_elem[0].get_text().split('\'')[-2]
    else:
        item['description'] = item['title'] = '近期没有新文章'
        item['link'] = url
    return item

def ctx(gh=''):
    url = f"{domain}/weixin?type=1&s_from=input&query={gh}&ie=utf8&_sug_=n&_sug_type_=&w=01019900&sut=1554&sst0=1628603087755&lkt=0%2C0%2C0"
    tree = fetch(url=url, headers=DEFAULT_HEADERS)
    dd_elems = tree.select('dd')
    dd_num = len(dd_elems)
    posts = [dd_elems[-1]] if dd_elems else []
    title_elem = tree.select('p.tit a')
    mp_name = title_elem[0].get_text() if title_elem else ''
    desc_elems = tree.select('dd')
    mp_description = desc_elems[0].get_text() if desc_elems else ''
    return {
        'title': f'{mp_name}-公众号',
        'link': url,
        'description': mp_description,
        'author': 'hillerliao',
        'items': [parse(post, dd_num, url) for post in posts] 
    }