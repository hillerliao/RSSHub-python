#!/usr/bin/env python3

import json

import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.sztv.com.cn'


def parse(post) -> dict:
    item = {}
    item['title'] = post['title']
    item['link'] = post['url']
    video_poster = post['logo']
    video_url = post['video'][0]['formats'][0]['url']
    html = f'<video preload="none" poster="{video_poster}" controls="" src="{video_url}" width="471"></video>'
    item['description'] = html
    return item


def ctx(id='') -> dict:
    url = f'https://api.scms.sztv.com.cn/api/com/article/getArticleList?tenantId=ysz&specialtype=1&banner=1&catalogId={id}&page=1'
    try:
        res = requests.get(url, headers=DEFAULT_HEADERS)
        res.raise_for_status()
    except Exception as e:
        raise e
    else:
        post = res.text
    content = json.loads(post)
    title = content['returnData']['news'][0]['refername']
    items = list(map(parse, content['returnData']['news']))
    return {
        'title': title,
        'link': domain,
        'description': '壹深圳，每天开启新深圳',
        'author': 'icedragon',
        'items': items,
    }
