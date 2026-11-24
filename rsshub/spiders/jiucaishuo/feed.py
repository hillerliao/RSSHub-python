"""Public broadcasts from Jiucaishuo's research workbench."""
import re
from datetime import datetime
from html import escape
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from rsshub.utils import DEFAULT_HEADERS, fetch_with_deadline

FEED_URL = 'https://jiucaishuo.com/feed'
API_URL = 'https://ai2.jiucaishuo.com/api/ai/feed'
XML_INVALID = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]')


def clean(value):
    return XML_INVALID.sub('', str(value or ''))


def parse_item(post):
    """Keep API IDs stable; upstream timestamps are local to Shanghai."""
    item_id = int(post['id'])
    agent_id = int(post['agent_id'])
    date = datetime.strptime(
        f"{post['publish_date']} {post['publish_at'][-5:]}", '%Y-%m-%d %H:%M'
    ).replace(tzinfo=ZoneInfo('Asia/Shanghai')).isoformat()
    body = escape(clean(post.get('body'))).replace('\n', '<br>')
    description = f'<p>{body}</p>'
    for chip in post.get('chips') or []:
        description += f'<p>{escape(clean(chip.get("k")))}: {escape(clean(chip.get("v")))}</p>'
    for media in post.get('media') or []:
        url = clean(media.get('url'))
        parts = urlsplit(url)
        if media.get('type') == 'image' and parts.scheme in ('http', 'https') and parts.netloc:
            description += f'<p><img src="{escape(url, quote=True)}" alt=""></p>'
    author = clean(post.get('agent_name')) or '韭圈'
    return {
        'title': clean(post.get('title')) or f'{author} · {post["publish_at"]}',
        'link': f'{FEED_URL}?agent_id={agent_id}#feed-{item_id}',
        'description': description,
        'pubDate': date,
        'author': author,
    }


def ctx(agent_id=None, tab='all'):
    params = f'?tab={tab}&days=90&limit=100'
    link = FEED_URL
    if agent_id is not None:
        params += f'&agent_id={agent_id}'
        link += f'?agent_id={agent_id}'
    response = fetch_with_deadline(API_URL + params, headers=DEFAULT_HEADERS,
                                   deadline=8.0, timeout=6.0)
    payload = response.json()
    if not isinstance(payload, dict) or payload.get('code') != 0:
        raise ValueError('Jiucaishuo API returned an unsuccessful response')
    data = payload.get('data')
    if not isinstance(data, dict) or not isinstance(data.get('items'), list):
        raise ValueError('Jiucaishuo API returned an invalid feed')
    items = []
    seen = set()
    for post in data['items']:
        try:
            item = parse_item(post)
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
        if item['link'] not in seen:
            seen.add(item['link'])
            items.append(item)
    if data['items'] and not items:
        raise ValueError('Jiucaishuo feed contains no valid entries')
    items.sort(key=lambda item: item['pubDate'], reverse=True)
    return {
        'title': '韭圈 · 投研工作台',
        'link': link,
        'description': '韭菜说公开播报信息流',
        'author': '韭圈',
        'items': items,
    }
