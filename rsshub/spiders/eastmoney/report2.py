import json
import re
import typing

import requests
from parsel import Selector
from rsshub.utils import DEFAULT_HEADERS, fetch


def parse(post) -> dict:
    item = {}
    item['title'] = post['title']
    item[
        'link'
    ] = f'https://data.eastmoney.com/report/zw_macresearch.jshtml?encodeUrl={post["encodeUrl"]}'
    item['description'] = item['title']
    item['author'] = post['researcher']
    item['pubDate'] = post['publishDate']
    return item


def fetch_xml(url: str, headers: dict = DEFAULT_HEADERS) -> typing.Optional[Selector]:
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
    except Exception as e:
        print(f'[Err] {e}')
    else:
        html = res.text
        tree = Selector(text=html, type='xml')
        return tree


def ctx(type='') -> dict:
    url = f'https://data.eastmoney.com/report/{type}.jshtml'
    tree = fetch_xml(url)
    assert tree is not None
    tree_script = tree.xpath('//script/text()').getall()[4]
    tree_json = re.search('var initdata = (.*);', tree_script)
    assert tree_json is not None
    tree_json = tree_json.group(1)
    posts = json.loads(tree_json)['data']
    items = list(map(parse, posts))
    type_strs = {'macresearch': '宏观研报', 'strategyreport': '策略报告'}
    type_str = type_strs[type]
    return {
        'title': f'{type_str} - 东方财富网',
        'link': f'http://data.eastmoney.com/report/{type_str}.jshtml',
        'description': f'{type_str}  - 东方财富网',
        'author': 'icedragon',
        'items': items,
    }
