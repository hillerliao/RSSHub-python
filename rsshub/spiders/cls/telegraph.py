import requests
from rsshub.utils import DEFAULT_HEADERS
import arrow
import hashlib
import urllib.parse

# Keep the timeout below typical serverless gateway limits (e.g. Vercel default 10s)
# so a slow/unreachable upstream returns an error feed instead of a 504.
REQUEST_TIMEOUT = 8


def generate_sign(params):
    """Generate sign for CLS API using SHA1+MD5"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    query_string = urllib.parse.urlencode(sorted_params)
    sha1_hash = hashlib.sha1(query_string.encode('utf-8')).hexdigest()
    return hashlib.md5(sha1_hash.encode('utf-8')).hexdigest()


def parse(post):
    item = {
        'title': '',
        'description': '',
        'link': '',
        'author': '财联社',
        'pubDate': ''
    }
    title = post.get('title') or ''
    item['title'] = title if title != '' else post.get('content') or ''
    item['description'] = post.get('content') or ''
    item['link'] = post.get('shareurl') or ''
    ctime = post.get('ctime') or 0
    try:
        item['pubDate'] = arrow.get(int(ctime)).isoformat()
    except (ValueError, TypeError):
        item['pubDate'] = arrow.now().isoformat()
    return item


# www.cls.cn (main site) is reachable from domestic networks but its IP range
# is blocked from overseas/cloud hosts (e.g. Vercel), which caused 504s.
# m.cls.cn (mobile) is served from different Huawei Cloud WAF nodes and works
# with the same API + signature algorithm, so try it first, then fall back.
HOSTS = ['m.cls.cn', 'www.cls.cn']


def ctx():
    params = {
        'app': 'CailianpressWeb',
        'category': '',
        'os': 'web',
        'rn': '50',
        'last_time': '0'
    }
    params['sign'] = generate_sign(params)

    errors = []
    posts = []
    for host in HOSTS:
        headers = DEFAULT_HEADERS.copy()
        headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'https://{host}/telegraph'
        })
        try:
            res = requests.get(
                f'https://{host}/v1/roll/get_roll_list',
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()
            posts = (data.get('data') or {}).get('roll_data') or []
            if posts:
                print(f"[cls/telegraph] Fetched {len(posts)} items from {host}")
                break
        except Exception as e:
            errors.append(f'{host}: {e}')
            print(f"[cls/telegraph] Host {host} failed: {e}")

    if not posts:
        detail = '; '.join(errors) or 'empty response'
        return {
            'title': '电报 - 财联社',
            'link': 'https://www.cls.cn/telegraph',
            'description': f'财联社电报 (数据获取失败: {detail})',
            'author': 'hillerliao',
            'items': []
        }

    items = []
    for post in posts:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f"[cls/telegraph] Skipping bad item: {e}")
    return {
        'title': '电报 - 财联社',
        'link': 'https://www.cls.cn/telegraph',
        'description': '财联社电报',
        'author': 'hillerliao',
        'items': items
    }
