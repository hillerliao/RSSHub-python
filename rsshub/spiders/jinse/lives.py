import base64
import hashlib
import hmac
import random
import string
import time

import arrow
import requests
from rsshub.utils import DEFAULT_HEADERS

# 金色财经(jinse2.com)快讯
# 全部快讯: https://www.jinse2.com/lives
#   -> GET https://api.jinse2.com/noah/v2/lives?limit=&reading=&source=&flag=&id=&category=
# 分类列表: GET https://api.jinse2.com/noah/v2/live/categorys
# 接口需要签名请求头 X-JINSE-SIGNATURE = base64(HMAC-SHA256('v1'+time+nonce+appkey, secret))
# 分页: flag=down 且 id 传上一次响应的 bottom_id, 首次传 0

REQUEST_TIMEOUT = 8
DEFAULT_LIMIT = 50

API_BASE = 'https://api.jinse2.com'
LIVES_URL = f'{API_BASE}/noah/v2/lives'
CATEGORY_URL = f'{API_BASE}/noah/v2/live/categorys'
SOURCE_URL = 'https://www.jinse2.com/lives'

APPKEY = 'jTlYphIBUyKBvUIJ'
SECRET = '070YrDGny4iM6WVzMaX7SsdEtIT07tuOxzvEYcOH'

# 金色财经分类: id -> 名称 (来自 /noah/v2/live/categorys)
CATEGORIES = {
    '0': '全部',
    '1': '精选',
    '7': '政策',
    '2': '数据',
    '5': 'AI',
    '9': 'Alpha',
}

# 名称 -> id 反向映射
_NAME_TO_ID = {name: cid for cid, name in CATEGORIES.items()}

# 模块级分类缓存, 避免每次请求都重新拉取分类接口
_CATEGORY_CACHE = {}


def _sign(nonce, ts):
    raw = f'v1{ts}{nonce}{APPKEY}'
    sig = hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).digest()
    return base64.b64encode(sig).decode()


def _headers():
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    ts = int(time.time())
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Referer': SOURCE_URL,
        'Origin': 'https://www.jinse2.com',
        'source': 'web',
        'token': '',
        'X-JINSE-API-VERSION': 'v1',
        'X-JINSE-TIME': str(ts),
        'X-JINSE-NONCE': nonce,
        'X-JINSE-APPKEY': APPKEY,
        'X-JINSE-SIGNATURE': _sign(nonce, ts),
    })
    return headers


def fetch_categorys():
    """获取分类列表, 返回 id -> 名称 映射"""
    if _CATEGORY_CACHE:
        return dict(_CATEGORY_CACHE)
    try:
        res = requests.get(CATEGORY_URL, headers=_headers(), timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        data = res.json().get('data') or []
        cats = {str(x.get('id')): x.get('name', '') for x in data if x.get('id') is not None}
        if cats:
            _CATEGORY_CACHE.clear()
            _CATEGORY_CACHE.update(cats)
            return dict(cats)
    except Exception as e:
        print(f'[jinse/lives] Fetch categorys failed: {e}')
    return dict(CATEGORIES)


def fetch_lives(category_id='0', limit=DEFAULT_LIMIT):
    """获取快讯列表, category_id 为 0 时返回全部"""
    posts = []
    last_id = 0
    while len(posts) < limit:
        params = {
            'limit': limit,
            'reading': 'false',
            'source': 'web',
            'flag': 'down',
            'id': last_id,
            'category': category_id,
        }
        try:
            res = requests.get(LIVES_URL, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            print(f'[jinse/lives] API failed: {e}')
            break
        if not data or not data.get('list'):
            print(f'[jinse/lives] API error: {res.status_code}')
            break
        batch = []
        for day in data.get('list') or []:
            for live in day.get('lives') or []:
                batch.append(live)
        posts.extend(batch)
        next_id = data.get('bottom_id')
        if not batch or next_id is None or next_id == last_id:
            break
        last_id = next_id
    return posts[:limit]


def parse(live):
    item = {}
    content = live.get('content') or ''
    title = live.get('content_prefix') or ''
    if not title:
        title = (content[:40] + '…') if len(content) > 40 else content
    item['title'] = title
    description = content
    for img in live.get('images') or []:
        src = img.get('url') if isinstance(img, dict) else img
        if src:
            description += f'<br><img src="{src}">'
    item['description'] = description
    item['link'] = live.get('link') or ''
    item['author'] = '金色财经'
    ts = live.get('created_at') or 0
    try:
        # 接口 created_at 为秒级 Unix 时间戳
        item['pubDate'] = arrow.get(int(ts)).isoformat()
    except (ValueError, TypeError):
        item['pubDate'] = arrow.now().isoformat()
    return item


def ctx(category=''):
    category = (category or '').strip()
    cats = fetch_categorys()
    _NAME_TO_ID.clear()
    for cid, name in cats.items():
        _NAME_TO_ID.setdefault(name, cid)

    # 支持分类 id、中文名称以及 all 别名
    category_id = '0'
    if category and category != 'all':
        if category in cats:
            category_id = category
        elif category in _NAME_TO_ID:
            category_id = _NAME_TO_ID[category]
        else:
            print(f'[jinse/lives] Unknown category: {category}')

    try:
        posts = fetch_lives(category_id)
    except Exception as e:
        print(f'[jinse/lives] Fetch failed: {e}')
        posts = []

    items = []
    for post in posts:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f'[jinse/lives] Skipping bad item: {e}')

    cat_name = cats.get(category_id, '全部')
    if category_id == '0':
        title = '金色财经 快讯'
        description = '金色财经 7x24 小时快讯'
    else:
        title = f'{cat_name} - 金色财经'
        description = f'金色财经 - {cat_name} 分类快讯'

    if not items:
        description += ' (数据获取失败或暂无内容)'

    return {
        'title': title,
        'link': SOURCE_URL,
        'description': description,
        'author': 'hillerliao',
        'items': items,
    }
