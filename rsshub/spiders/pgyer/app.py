import re
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.pgyer.com'

def parse(post):
    item = {}
    meta_elem = post.select('meta[property="og:description"]')
    item['title'] = meta_elem[0]['content'] if meta_elem else ''
    item['description'] = item['title'] 
    update_desc = post.select('div.update-description')
    if update_desc: 
        item['description'] = update_desc[0].decode_contents()
        item['description']  = re.sub(r'<[^>]*>', '', item['description'] )\
                            .split('备注信息:')[1].split('执行人')[0].strip() 
    qrcode_img = post.select('img.qrcode')
    if qrcode_img:
        link_parts = qrcode_img[0]['src'].split('app/qrcode/')
        item['link'] = link_parts[0] + link_parts[1] if len(link_parts) > 1 else ''
    else:
        item['link'] = ''
    return item

def ctx(category=''):
    url = f"{domain}/{category}"
    tree = fetch(url,headers=DEFAULT_HEADERS)
    posts = tree.select('.container.content.pt-10')
    posts = tree.select('html')
    meta_desc = tree.select('meta[property="og:description"]')
    title = meta_desc[0]['content'] if meta_desc else ''
    title_elem = tree.select('title')
    app_name = title_elem[0].get_text() if title_elem else ''
    return {
        'title': f'{title} - 蒲公英',
        'link': url,
        'description': f'{app_name} 安装包更新 - 蒲公英',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }
    
