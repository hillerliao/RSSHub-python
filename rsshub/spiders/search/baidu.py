import json
import re
import requests
import arrow
from concurrent.futures import ThreadPoolExecutor
from requests.utils import quote, unquote
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://baidu.com'

REQUEST_TIMEOUT = 3  # 必须远小于 Vercel 函数超时（10s），含冷启动余量


def parse(post):
    item = {}
    item['title'] = post['q'] 
    item['description'] = post['q']
    item['link'] = f'{domain}/s?ie=UTF-8&wd=' + quote(post['q'])
    item['pubDate'] =  arrow.now().isoformat()
    item['author'] = '百度'
    return item 


def _fetch_suggestion(category):
    """建议专用域名（轻量 CDN 接口），返回非严格 JSONP，用正则提取"""
    url = f'https://suggestion.baidu.com/su?wd={quote(category)}&cb=cb'
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    m = re.search(r's:\[(.*?)\]', resp.text)
    if not m:
        return []
    return [{'q': w} for w in re.findall(r'"([^"]*)"', m.group(1))]


def _fetch_sugrec(category):
    url = f'{domain}/sugrec?wd={quote(category)}&pre=1&p=3&ie=utf-8&json=1&prod=pc&from=pc_web&req=2&csor=3'
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = json.loads(resp.text)
    return data.get('g', [])


def ctx(keyword=''):
    keyword = unquote(keyword)  # 防御 Vercel runtime 传入未解码的 URL 编码
    items = []
    # 并发请求两个接口，谁先成功用谁，总耗时受限于最长超时，避免 Vercel 10s 函数超时
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(_fetch_suggestion, keyword),
            executor.submit(_fetch_sugrec, keyword),
        ]
        for future in futures:
            try:
                posts = future.result()
                if posts:
                    items = list(map(parse, posts))
                    break
            except Exception as e:
                print(f'[Baidu Suggest] fetch failed: {e}')
    return {
        'title': f'{keyword} - 搜索提示 - 百度',
        'link': f'https://www.baidu.com/s?ie=UTF-8&wd={quote(keyword)}',
        'description': '百度搜索提示',
        'author': 'hillerliao',
        'items': items
    }
