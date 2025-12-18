import re
import json
import requests
from datetime import datetime
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://news.futunn.com'

def parse_news(news):
    title = news.get('content', '') if news.get('title', '')=='' else news.get('title', '')

    content = news.get('content', '')
    detail_url = news.get('detailUrl', '')
    time = datetime.utcfromtimestamp(int(news['time'])).strftime('%Y-%m-%dT%H:%M:%SZ')

    item = {
        'title': title,
        'description': content,
        'link': detail_url,
        'pubDate': time
    }
    
    return item

def ctx(lang=''):
    """
    解析 JSON 数据，提取所有live news的内容。
    """
    url = f"{domain}/news-site-api/main/get-flash-list?pageSize=50&lang={lang}"
    response = requests.get(url, headers=DEFAULT_HEADERS)
    data = response.json()

    # 检查数据是否有效
    if data['code'] != 0 or not data['data']['data']['news']:
        return Response("No data available", mimetype='text/plain')

    news_list = data.get('data', {}).get('data', {}).get('news', [])

    # 使用 parse_gobbet 解析每一条新闻
    items = [parse_news(news) for news in news_list]

    return {
        'title': 'Futunn Live News',
        'link': url,
        'description': 'Futunn Live News',
        'author': 'hillerliao',
        'items': items
    }
