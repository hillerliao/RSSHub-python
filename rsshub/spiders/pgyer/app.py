import re
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.pgyer.com'

def parse(post):
    item = {}
    item['title'] = post.xpath('//meta[@property="og:description"]').attrib['content']
    item['description'] = item['title'] 
    if post.css('div.update-description').extract_first(): 
        item['description'] = post.css('div.update-description').extract_first()
        item['description']  = re.sub(r'<[^>]*>', '', item['description'] )\
                            .split('备注信息:')[1].split('执行人')[0].strip() 
    link =  post.css('img.qrcode').attrib['src'].split('app/qrcode/')
    item['link'] = link[0] + link[1]
    return item

def ctx(category=''):
    url = f"{domain}/{category}"
    tree = fetch(url,headers=DEFAULT_HEADERS)
    posts = tree.css('.container.content.pt-10')
    posts = tree.css('html')
    title = tree.xpath('//meta[@property="og:description"]').attrib['content']
    app_name = tree.css('title::text').get()
    return {
        'title': f'{title} - 蒲公英',
        'link': url,
        'description': f'{app_name} 安装包更新 - 蒲公英',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }
    
