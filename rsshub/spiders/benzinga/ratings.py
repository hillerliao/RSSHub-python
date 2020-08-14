from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.benzinga.com'

def ctx(category=''):

    stock = category
    
    def parse(post):
        item = {}
        item['description'] = item['title'] = stock.upper() + '的评级：' +  ', '.join(post.css('td::text').extract())
        item['link'] = url
        return item    

    
    url = f'{domain}/stock/{category}/ratings'
    tree = fetch(url, headers=DEFAULT_HEADERS)
    posts = tree.css('tbody tr')
    items = list(map(parse, posts))

    column_title = tree.css('title::text').extract_first()
    return {
        'title': f'{column_title} - benzinga',
        'description': f'{column_title} - benzinga',
        'link': url,
        'author': f'hillerliao',
        'items': items
    }
