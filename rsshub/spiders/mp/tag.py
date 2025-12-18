from rsshub.utils import fetch

domain = 'https://mp.weixin.qq.com'


def parse(post):
    item = {}
    title_elem = post.select('span.album__item-title-wrp')
    item['description'] = item['title'] = title_elem[0].get_text() if title_elem else ''
    li_elem = post.select('li')
    link = li_elem[0]['data-link'] if li_elem and 'data-link' in li_elem[0].attrs else ''
    item['link'] = link 
    time_elem = post.select('span.js_article_create_time')
    item['pubDate'] = time_elem[0].get_text() if time_elem else ''
    return item


def ctx(biz='', tag=''):
    url = f"{domain}/mp/appmsgalbum?__biz={biz}==&action=getalbum&album_id={tag}"
    tree = fetch(url)
    posts = tree.select('.js_album_list li')
    author_elem = tree.select('div.album__author-name')
    mp_name = author_elem[0].get_text() if author_elem else ''
    tag_elem = tree.select('div#js_tag_name')
    tag_name = tag_elem[0].get_text() if tag_elem else ''
    return {
        'title': f'{tag_name} - {mp_name}',
        'link': url,
        'description': f'{tag_name} - {mp_name}',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }