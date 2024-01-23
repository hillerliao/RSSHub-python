#!/usr/bin/env python3

import re

import json
import requests

from rsshub.utils import DEFAULT_HEADERS, fetch

domain = 'https://www.chncpa.org/yshd/yshd_7376/zmyyh_7377/'


def parse(post) -> dict:
    item = {}
    item['title'] = post.xpath('a/@title').get()
    link_end = post.xpath('a/@href').get()
    item['link'] = f'https:{link_end}'
    detail_id = re.search(r'\d+', item['link'])
    assert detail_id is not None
    detail_id = detail_id[0]
    detail_url = f'https://openapi.chncpa.org/product/detail?productId={detail_id}&channel=pc'
    try:
        res = requests.get(detail_url, headers=DEFAULT_HEADERS)
        res.raise_for_status()
    except Exception as e:
        raise e
    else:
        json_text = res.text
    item['description'] = json.loads(json_text)['data']['productSaleStatus']
    return item


def ctx() -> dict:
    url = f'{domain}'
    tree = fetch(url)
    assert tree is not None, "can't get web page"
    posts = tree.xpath('//div[@class="mainbox zx"]/div[@class="item"]')
    items = list(map(parse, posts))
    return {
        'title': '国家大剧院 - 艺术活动 - 周末音乐会',
        'link': url,
        'description': '周末音乐会是国家大剧院联手名家名团，于每周末推出的艺术活动品牌。周末音乐会涉及交响乐、民族管弦乐、室内乐、歌剧、合唱、独唱等多种艺术形式，荟萃一系列优秀的中外交响乐作品，以“演讲结合、赏析并重”为特点，实行“名家、名团、低票价”的亲民政策，为音乐爱好者提供全方位的音乐视角，为广大艺术爱好者提供近距离接触音乐经典的机会，感受高雅艺术带给心灵的震撼。',
        'author': 'icedragon',
        'items': items,
    }
