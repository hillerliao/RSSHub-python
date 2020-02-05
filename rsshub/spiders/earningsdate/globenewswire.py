from rsshub.utils import fetch, filter_content

domain = 'https://www.globenewswire.com'

def parse(post):
    item = {}
    item['title'] = post.css('title::text').extract_first().strip()
    item['description'] = post.css('description::text').extract_first().strip(']]>')
    item['link'] = post.css('guid::text').extract_first()
    item['pubDate'] = post.css('pubDate::text').extract_first()
    return item

def ctx(category=''):
    tree = fetch(f"{domain}/RssFeed/subjectcode/13-Earnings%20Releases%20And%20Operating%20Results/feedTitle/GlobeNewswire%20-%20Earnings%20Releases%20And%20Operating%20Results")
    posts = tree.css('item')
    items = list(map(parse, posts)) 
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Globenewswire',
        'link': f'{domain}/RssFeed/subjectcode/13-Earnings%20Releases%20And%20Operating%20Results/feedTitle/GlobeNewswire%20-%20Earnings%20Releases%20And%20Operating%20Results',
        'description': 'Earnings Date - Globenewswire',
        'author': 'hillerliao',
        'items': items
    }