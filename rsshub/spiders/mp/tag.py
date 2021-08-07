from rsshub.utils import fetch

domain = 'https://mp.weixin.qq.com'


def parse(post):
    item = {}
    item['description'] = item['title'] = post.css('span.album__item-title-wrp::text').extract_first()
    link = f"{post.css('li::attr(data-link)').extract_first()}"
    item['link'] = link 
    item['pubDate'] = post.css('span.js_article_create_time::text').extract_first()
    return item


def ctx(biz='', tag=''):
    url = f"{domain}/mp/appmsgalbum?__biz={biz}==&action=getalbum&album_id={tag}"
    tree = fetch(url)
    posts = tree.css('.js_album_list li')
    mp_name = tree.css('div.album__author-name::text').extract_first()
    tag_name = tree.css('div#js_tag_name::text').extract_first()
    return {
        'title': f'{tag_name} - {mp_name}',
        'link': url,
        'description': f'{tag_name} - {mp_name}',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }