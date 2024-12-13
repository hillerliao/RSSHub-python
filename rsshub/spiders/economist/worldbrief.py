import re
import json
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

domain = 'https://www.economist.com'

def extract_text(node):
    if isinstance(node, dict):
        if 'data' in node:
            return node['data']
        elif 'children' in node:
            return ''.join(extract_text(child) for child in node['children'])
    elif isinstance(node, list):
        return ''.join(extract_text(child) for child in node)
    return '' 

def parse_news(gobbet):
    """
    生成单条 news 的新闻内容，提取标题和正文。
    """   
    title = gobbet.strip()
    item = {
        'title': title,  
        'description': title,   # 简单设置正文为描述
        'link': f"{domain}/the-world-in-brief?from={title[:30]}"  # 生成链接
    }
    return item

def ctx(category=''):
    """
    解析 JSON 数据，提取所有brief news的内容。
    """
    url = f"{domain}/"
    html = fetch(url, headers=DEFAULT_HEADERS).get()
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', id="__NEXT_DATA__", type="application/json")

    if not script_tag:
        raise ValueError("Could not find __NEXT_DATA__ script tag.")

    # Load JSON content
    data = json.loads(script_tag.string)

    news_list = data.get('props', {}).get('pageProps', {}).get('worldInBrief', {}).get('text', [])[:-2]
    
    news_list_new = []
    for item in news_list:
        if item['type'] == 'tag' and item['name'] == 'p':  # 确保是段落
            news_list_new.append(extract_text(item['children']))    

    # 使用 parse_gobbet 解析每一条新闻
    items = [parse_news(news) for news in news_list_new]

    return {
        'title': 'World Brief - Economist',
        'link': url,
        'description': 'The world in brief: Catch up quickly on the global stories that matter',
        'author': 'hillerliao',
        'items': items
    }
