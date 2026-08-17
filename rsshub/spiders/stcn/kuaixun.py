import requests
import arrow
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS

# 证券时报网(stcn.com)快讯
# 全部快讯: https://www.stcn.com/article/list/kx.html
#   -> GET /article/list.html?type=kx (JSON)
# Tag 快讯: https://www.stcn.com/article/kx-tag-detail.html?tag=<TAG>
#   -> GET /article/kx-tag-detail-list.html?tag=<TAG> (JSON)
# 分页: 首次不带 page_time/last_time, 之后用响应中的 page_time/last_time 继续
# 注意: 接口依赖会话 Cookie 与 X-Requested-With 请求头, 需先用 Session 访问对应页面

REQUEST_TIMEOUT = 8
DEFAULT_LIMIT = 50  # 接口每页 30 条, 默认抓 2 页

LIST_URL = 'https://www.stcn.com/article/list.html'
TAG_LIST_URL = 'https://www.stcn.com/article/kx-tag-detail-list.html'
LIST_PAGE = 'https://www.stcn.com/article/list/kx.html'
TAG_PAGE = 'https://www.stcn.com/article/kx-tag-detail.html'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 模块级 tag 名称缓存, 避免每次请求都重新解析页面
_TAG_NAME_CACHE = {}


def fetch_tag_name(tag):
    """从 tag 详情页解析 tag 名称, 失败时回退为 tag 本身"""
    if tag in _TAG_NAME_CACHE:
        return _TAG_NAME_CACHE[tag]
    name = tag
    try:
        headers = DEFAULT_HEADERS.copy()
        headers.update({'User-Agent': USER_AGENT})
        url = f'{TAG_PAGE}?tag={tag}'
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        el = soup.select_one('.tag-page-top-text span')
        if el:
            name = el.get_text(strip=True) or name
    except Exception as e:
        print(f"[stcn/kuaixun] Fetch tag name for {tag} failed: {e}")
    _TAG_NAME_CACHE[tag] = name
    return name


def fetch_list(tag='', limit=DEFAULT_LIMIT):
    """获取快讯列表, 支持可选 tag, 返回原始数据列表"""
    session = requests.Session()
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.stcn.com',
        'X-Requested-With': 'XMLHttpRequest',
    })

    if tag:
        api_url = TAG_LIST_URL
        page_url = f'{TAG_PAGE}?tag={tag}'
        headers['Referer'] = page_url
    else:
        api_url = LIST_URL
        page_url = LIST_PAGE
        headers['Referer'] = page_url

    # 先访问页面建立会话(Cookie), 否则接口返回 HTML 而非 JSON
    try:
        session.get(page_url, headers=headers, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[stcn/kuaixun] Page {page_url} failed: {e}")

    params = {'tag': tag} if tag else {'type': 'kx'}
    posts = []
    while len(posts) < limit:
        try:
            res = session.get(api_url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            print(f"[stcn/kuaixun] API {api_url} failed: {e}")
            break
        if data.get('state') != 1:
            print(f"[stcn/kuaixun] API error: {data.get('msg')}")
            break
        batch = data.get('data') or []
        posts.extend(batch)
        page_time = data.get('page_time')
        last_time = data.get('last_time')
        if not batch or page_time is None or last_time is None:
            break
        params['page_time'] = page_time
        params['last_time'] = last_time
    return posts[:limit]


def parse(post):
    item = {}
    title = post.get('title') or ''
    content = post.get('content') or ''
    if not title:
        # 无标题时截取内容前 40 字作为标题
        title = (content[:40] + '…') if len(content) > 40 else content
    item['title'] = title
    source = post.get('source') or '证券时报'
    item['description'] = content
    link = post.get('web_url') or post.get('url') or ''
    if link and not link.startswith('http'):
        link = f'https://www.stcn.com{link}'
    item['link'] = link
    item['author'] = source
    ts = post.get('time') or 0
    try:
        # 接口 time 为毫秒时间戳
        item['pubDate'] = arrow.get(int(ts) / 1000).isoformat()
    except (ValueError, TypeError):
        item['pubDate'] = arrow.now().isoformat()
    return item


def ctx(tag=''):
    tag = (tag or '').strip()
    tag_name = fetch_tag_name(tag) if tag else ''
    try:
        posts = fetch_list(tag)
    except Exception as e:
        print(f"[stcn/kuaixun] Fetch failed: {e}")
        posts = []

    items = []
    for post in posts:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f"[stcn/kuaixun] Skipping bad item: {e}")

    if tag:
        title = f'{tag_name} 快讯 - 证券时报网' if tag_name else '快讯 - 证券时报网'
        link = f'{TAG_PAGE}?tag={tag}'
        description = f'证券时报网{tag_name}快讯' if tag_name else '证券时报网快讯'
    else:
        title = '快讯 - 证券时报网'
        link = LIST_PAGE
        description = '证券时报网快讯'

    if not items:
        description += ' (数据获取失败或暂无内容)'

    return {
        'title': title,
        'link': link,
        'description': description,
        'author': 'hillerliao',
        'items': items
    }
