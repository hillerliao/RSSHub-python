from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.benzinga.com'

def ctx(category=''):

    stock = category
    
    def parse(post):
        item = {}
        tds = post.select('td')
        item['description'] = item['title'] = stock.upper() + '的评级：' +  ', '.join([td.get_text().strip() for td in tds])
        item['link'] = url
        return item    

    
    url = f'{domain}/stock/{category}/ratings'
    tree = fetch(url, headers=DEFAULT_HEADERS)
    if not tree:
         return {
            'title': f'{category} - benzinga',
            'description': f'{category} - benzinga',
            'link': url,
            'author': f'hillerliao',
            'items': []
        }
    posts = tree.select('tbody tr')
    items = list(map(parse, posts))

    title_el = tree.select_one('title')
    column_title = title_el.get_text().strip() if title_el else category
    return {
        'title': f'{column_title} - benzinga',
        'description': f'{column_title} - benzinga',
        'link': url,
        'author': f'hillerliao',
        'items': items
    }
