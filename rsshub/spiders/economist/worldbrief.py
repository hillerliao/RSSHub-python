import re
import json
import time
import asyncio
from bs4 import BeautifulSoup
from rsshub.spiders.utils.browser import browser_pool, HAS_PLAYWRIGHT

domain = 'https://www.economist.com'


def extract_news_html(data):
    """
    从 __NEXT_DATA__ 的 content 中提取新闻段落 HTML 列表。
    新版页面有两种结构：
    - GOBBETS: content.component.gobbets
    - CHUNK:   content.component.components
    """
    content = data.get('props', {}).get('pageProps', {}).get('content', {})
    component = content.get('component', {})
    if component.get('type') == 'GOBBETS':
        raw = component.get('gobbets', [])
    else:
        raw = component.get('components', [])
    return raw


def parse_news_page(data, page_url):
    """解析单个分页页面，生成一条新闻 item。"""
    content = data.get('props', {}).get('pageProps', {}).get('content', {})
    component = content.get('component', {})

    headline = component.get('headline') or component.get('metadataTitle') or 'World in Brief'
    raw = extract_news_html(data)

    description = ''
    # ZINGER 类型（Quote of the day）：内容在 component.zinger 里
    if not raw and component.get('type') == 'ZINGER' and isinstance(component.get('zinger'), dict):
        zinger = component['zinger']
        quote = zinger.get('quote') or ''
        author = zinger.get('author') or ''
        description = f'<blockquote><p>{quote}</p><footer>— {author}</footer></blockquote>'
        if headline.startswith('Quote of the day') and author and author not in headline:
            headline = f'{headline}: {author}'

    for gobbet in raw:
        text_html = gobbet.get('textHtml')
        if text_html:
            description += text_html
        elif gobbet.get('text'):
            description += f"<p>{gobbet['text']}</p>"

    # 给链接做相对→绝对转换，方便阅读
    soup = BeautifulSoup(description or '', 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].startswith('/'):
            a['href'] = domain + a['href']

    item = {
        'title': re.sub(r'\s+', ' ', headline).strip(),
        'description': str(soup) if description else '',
        'link': page_url,
        'pubDate': content.get('twib', {}).get('datePublished') or component.get('dateModified'),
    }
    return item


async def get_page_json(page, url, retries=3):
    """打开页面并返回 __NEXT_DATA__ 解析后的 dict。
    性能要点：__NEXT_DATA__ 是 SSR 注入的，等页面 commit 后即可读取，
    无需等 DOMContentLoaded（该站点第三方 JS 极重，domcontentloaded 需 ~24s）。
    连续翻页可能触发 DataDome 反爬（挑战页没有 __NEXT_DATA__），重试等待自动通过。
    """
    # Block unnecessary resources
    await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, wait_until='commit', timeout=60000)
            # DataDome 挑战页没有 __NEXT_DATA__，等待它出现（会因无 JS 挑战而失败）
            try:
                await page.wait_for_selector('script#__NEXT_DATA__', state='attached', timeout=20000)
            except Exception:
                pass
            html = await page.content()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', id="__NEXT_DATA__", type="application/json")
        if script_tag:
            return json.loads(script_tag.string)

        # 触发反爬或页面未就绪，稍等后重试
        if attempt < retries:
            wait = attempt * 5
            print(f"[worldbrief] Anti-bot on {url}, retry {attempt}/{retries} after {wait}s")
            await asyncio.sleep(wait)
        else:
            print(f"[worldbrief] Could not find __NEXT_DATA__ in {url}")
    return None


def ctx(category=''):
    """
    解析 The world in brief，通过分页 nextPage 遍历全部新闻。
    """
    url = f"{domain}/the-world-in-brief"

    if not HAS_PLAYWRIGHT:
        return {
            'title': 'World Brief - Economist (Not supported on Vercel)',
            'link': url,
            'description': 'Playwright is not available in this environment. Please use the self-hosted version for this feed.',
            'author': 'hillerliao',
            'items': [{
                'title': 'Playwright not supported on Vercel',
                'description': 'This feed requires Playwright, which is not supported on Vercel. Please use the self-hosted scraper image.',
                'link': url
            }]
        }

    items = []
    current_url = url
    visited = set()

    for _ in range(20):  # 安全上限，防止死循环
        data = browser_pool.run(lambda page, u=current_url: get_page_json(page, u))
        if not data:
            break

        content = data.get('props', {}).get('pageProps', {}).get('content', {})
        component = content.get('component', {})
        raw = extract_news_html(data)
        if component.get('type') in ('GOBBETS', 'ZINGER') or raw:
            items.append(parse_news_page(data, current_url))

        # 找出下一页链接
        pagination = content.get('pageNavigation', {}).get('pagination', {})
        next_page = pagination.get('nextPage')
        if not next_page or next_page in visited:
            break
        if next_page.startswith('/'):
            next_page = domain + next_page
        visited.add(next_page)
        current_url = next_page
        # 翻页间稍作停顿，避免连续快速请求触发 DataDome
        time.sleep(3)

    if not items:
        raise ValueError("Failed to retrieve content from The Economist")

    return {
        'title': 'World Brief - Economist',
        'link': url,
        'description': 'The world in brief: Catch up quickly on the global stories that matter',
        'author': 'hillerliao',
        'items': items
    }
