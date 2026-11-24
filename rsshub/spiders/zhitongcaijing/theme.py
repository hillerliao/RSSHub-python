import arrow
import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.zhitongcaijing.com'
API = f'{domain}/theme/article-list.html'

REQUEST_TIMEOUT = 8
PAGE_LIMIT = 2


def _fetch_page(theme_id, page):
    res = requests.get(
        API,
        params={'id': theme_id, 'page': page},
        headers=DEFAULT_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    res.raise_for_status()
    payload = res.json()
    return payload.get('data', {}).get('list') or []


def parse(post):
    pub = post.get('create_time')
    pub_iso = arrow.get(int(pub)).isoformat() if pub else (post.get('create_time_desc') or '')
    link = post.get('url') or f"/content/detail/{post.get('content_id')}.html"
    if link.startswith('/'):
        link = f"{domain}{link}"
    desc = post.get('digest') or ''
    if post.get('image'):
        sep = '<br>' if desc else ''
        desc = f"{desc}{sep}<img referrerpolicy='no-referrer' src='{post['image']}'>"
    return {
        'title': (post.get('title') or '').strip(),
        'description': desc,
        'link': link,
        'pubDate': pub_iso,
        'author': '智通财经',
    }


def ctx(theme_id=''):
    items, errors = [], []
    for page in range(1, PAGE_LIMIT + 1):
        try:
            posts = _fetch_page(theme_id, page)
        except Exception as e:
            errors.append(f'page {page}: {e}')
            break
        if not posts:
            break
        for post in posts:
            try:
                items.append(parse(post))
            except Exception as e:
                errors.append(f'item skip: {e}')
    return {
        'title': f'智通财经 - 主题 {theme_id}',
        'link': f'{domain}/theme/detail/{theme_id}.html',
        'description': '智通财经主题聚合' + ('（部分页面获取失败）' if errors else ''),
        'author': 'hillerliao',
        'items': items,
    }