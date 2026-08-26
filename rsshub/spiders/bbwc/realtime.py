import re
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://api.bbwc.cn'


def parse_pubdate(post):
    # 首页流接口提供 inputtime 绝对时间戳
    if post.get('inputtime'):
        return arrow.get(int(post['inputtime'])).isoformat()
    # 栏目接口无 inputtime，从链接 /article/YYYY/MM/DD/ 提取发布日期
    m = re.search(r'/article/(\d{4})/(\d{2})/(\d{2})/', post.get('url', ''))
    if m:
        return arrow.get(*map(int, m.groups())).isoformat()
    return arrow.utcnow().isoformat()


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['outline']
    item['link'] = post['url']
    item['pubDate'] = parse_pubdate(post)
    item['author'] = post.get('author') or 'Bloomberg'
    return item


def fetch_posts(url):
    data = requests.get(url, headers=DEFAULT_HEADERS).json().get('data') or {}
    return data.get('list') or []


def ctx(category=''):
    if category:
        # 支持 /bbwc/realtime/2 或 /bbwc/realtime/cat_11 形式的栏目过滤
        catid = category if category.startswith('cat_') else f'cat_{category}'
        posts = fetch_posts(f'{domain}/web/cmscolumn/articlelist/catid/{catid}/device/30/p/1')
    else:
        posts = []
    if not posts:
        # 分类无效或未指定时回退到首页推荐流，避免空 feed / 404
        posts = fetch_posts(f'{domain}/web/home/articlelist/device/30/p/1')
    return {
        'title': f'即时新闻 - 商业周刊',
        'link': f'{domain}/realtime/index.html',
        'description': f'抓取彭博商业周刊即时新闻栏目的快讯',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }