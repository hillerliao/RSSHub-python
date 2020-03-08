import requests
import json
from parsel import Selector
from datetime import datetime, date
from rsshub.utils import DEFAULT_HEADERS


def parse(post):
    item = {}
    if post['stockName']!='':
        post['stockName'] = '[' + post['stockName'] + '] '
    item['title'] =  post['stockName'] + ' ' + post['title']
    item['title'] = item['title'].strip()
    item['description'] = item['title']
    item['link'] = f"http://data.eastmoney.com/report/zw_industry.jshtml?encodeUrl={post['encodeUrl']}"
    item['author'] = post['orgSName'] + ' ' + post['researcher']
    item['pubDate'] = post['publishDate']
    return item


def ctx(type='', category=''):
    qTypes = {'industry': '1', 'stock': '0'}
    qType = qTypes[type]
    url = f'http://reportapi.eastmoney.com/report/list?\
      cb=&industryCode={category}\
      &pageSize=50&industry=*&rating=*&ratingChange=*\
      &beginTime=&endTime=&pageNo=1&fields=&qType={qType}&orgCode=&rcode=&_=1583647953800'
    res = requests.get(url)
    posts = json.loads(res.text)['data']
    items = list(map(parse, posts))
    return {
        'title': f'{category} {type}研报 - 东方财富网',
        'link': f'http://data.eastmoney.com/report/{type}.jshtml?hyid={category}',
        'description': f'{category} {type} 研报 - 东方财富网',
        'author': 'hillerliao',
        'items': items
    }
