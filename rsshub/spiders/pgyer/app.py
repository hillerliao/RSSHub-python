from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.pgyer.com'

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
    
def parse(post):
    item = {}
    item['title'] = post.xpath('//meta[@property="og:description"]').attrib['content']
    item['description'] =   item['title'] + '；' \
                            + post.css('ul.breadcrumb > li::text').getall()[1] + '；' \
                            + post.css('ul.breadcrumb > li::text').getall()[2]
    item['link'] =  post.css('img.qrcode').attrib['src']
    return item