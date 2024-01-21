import json
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www3.nhk.or.jp'


def date_format(pubDate):
    date = arrow.get(pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
    iso = date.isoformat()
    return iso

def parse(post):
    item = {}
    item['title'] = post['title'] 
    item['description'] = post['title']
    item['link'] = domain + post['link']
    item['pubDate'] = date_format(post['pubDate'])
    item['author'] = 'NHK'
    return item 


def ctx(category=''):
    url = f'{domain}/news/json16/word/{category}_001.json?_=1705840617679'
    posts = requests.get(url)
    word = json.loads(posts.text)['channel']['word']  
    posts = json.loads(posts.text)['channel']['item']  
    return {
        'title': f'{word} - NHK News',
        'link': f'{domain}/news/word/{category}.html',
        'description': f'{word}の最新ニュース・特集一覧',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }