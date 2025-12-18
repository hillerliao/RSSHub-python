from rsshub.utils import fetch, filter_content

domain = 'https://www.globenewswire.com'

def parse(post):
    item = {}
    title_elem = post.select('title')
    item['title'] = title_elem[0].get_text().strip() if title_elem else ''
    desc_elem = post.select('description')
    item['description'] = desc_elem[0].get_text().strip(']]>') if desc_elem else ''
    guid_elem = post.select('guid')
    item['link'] = guid_elem[0].get_text() if guid_elem else ''
    pubdate_elem = post.select('pubDate')
    item['pubDate'] = pubdate_elem[0].get_text() if pubdate_elem else ''
    return item

def ctx(category=''):
    tree = fetch(f"{domain}/RssFeed/subjectcode/13-Earnings%20Releases%20And%20Operating%20Results/feedTitle/GlobeNewswire%20-%20Earnings%20Releases%20And%20Operating%20Results")
    posts = tree.select('item')
    items = list(map(parse, posts)) 
    items = filter_content(items)
    return {
        'title': 'Earnings Date - Globenewswire',
        'link': f'{domain}/RssFeed/subjectcode/13-Earnings%20Releases%20And%20Operating%20Results/feedTitle/GlobeNewswire%20-%20Earnings%20Releases%20And%20Operating%20Results',
        'description': 'Earnings Date - Globenewswire',
        'author': 'hillerliao',
        'items': items
    }