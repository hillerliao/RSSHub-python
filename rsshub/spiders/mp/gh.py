"""
gh.py — 公众号文章搜索 RSS 生成器（v3）

说明：
- 搜狗微信 type=1（公众号搜索）已于 2024 年后基本失效（返回"未搜索到"提示页）
- 改用 type=2（文章搜索），按"关键词"或"公众号名"返回相关文章
- 借鉴 wechat-article-search skill 的反爬思路：
  * 先访问 v.sogou.com 拿 SNUID cookie
  * 20 个 UA 池轮换
  * 请求间随机延迟
  * 真实 URL 解析（meta refresh / location.href / url+= 拼接），失败降级
  * 时间戳 10 位转 UTC+8 ISO8601

输出 RSS 项：title / link / description / pubDate / author（公众号名）
"""
import random
import re
import time as _time
import requests
from bs4 import BeautifulSoup
import arrow

try:
    from rsshub.utils import fetch, DEFAULT_HEADERS
except Exception:
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    def fetch(url, headers=None, **kwargs):  # noqa: F811
        sess = requests.Session()
        merged = {**DEFAULT_HEADERS, **(headers or {})}
        resp = sess.get(url, headers=merged, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')


domain = 'https://weixin.sogou.com'

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/123.0.0.0 Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/122.0.0.0 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Mi 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
]

DESKTOP_USER_AGENTS = [ua for ua in USER_AGENTS if 'Mobile' not in ua and 'iPhone' not in ua and 'iPad' not in ua]

SOGOU_BASE_COOKIES = 'ABTEST=7|1716888919|v1; IPLOC=CN5101; ariaDefaultTheme=default; ariaFixed=true; ariaReadtype=1; ariaStatus=false'

GH_ALIASES = {
    # 搜狗文章搜索不适合直接用微信号检索；这个 ID 常出现在旧文正文里，会导致结果偏旧。
    'xinhuashefabu1': {'query': '新华社', 'source_filter': '新华社'},
}


def cleanText(value):
    """Remove Unicode/XML characters that cannot be emitted in an RSS response."""
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return ''.join(
        ch for ch in value
        if not (0xD800 <= ord(ch) <= 0xDFFF)
        and (
            ord(ch) in (0x09, 0x0A, 0x0D)
            or 0x20 <= ord(ch) <= 0xD7FF
            or 0xE000 <= ord(ch) <= 0xFFFD
            or 0x10000 <= ord(ch) <= 0x10FFFF
        )
    )


def cleanItem(item):
    return {
        key: cleanText(value) if isinstance(value, str) else value
        for key, value in item.items()
    }


def getRandomUserAgent(desktop_only=False):
    pool = DESKTOP_USER_AGENTS if desktop_only else USER_AGENTS
    return random.choice(pool)


def getSogouCookie():
    try:
        sess = requests.Session()
        resp = sess.get(
            'https://v.sogou.com/v?ie=utf8&query=&p=40030600',
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'User-Agent': getRandomUserAgent(),
            },
            timeout=10,
        )
        cookies = []
        for raw in resp.headers.get('set-cookie', []):
            first = raw.split(';')[0]
            if first:
                cookies.append(first)
        cookie_str = '; '.join(cookies)
        m = re.search(r'SNUID=([^;]+)', cookie_str)
        snuid = m.group(1) if m else ''
        return f"{SOGOU_BASE_COOKIES}; SNUID={snuid}" if snuid else SOGOU_BASE_COOKIES
    except Exception:
        return SOGOU_BASE_COOKIES


def buildHeaders(cookie=None):
    headers = {
        **DEFAULT_HEADERS,
        'User-Agent': getRandomUserAgent(desktop_only=True),
        'Host': 'weixin.sogou.com',
        'Referer': 'https://weixin.sogou.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    if cookie:
        headers['Cookie'] = cookie
    return headers


def isVerifyPage(soup):
    text = soup.get_text(' ', strip=True)
    return 'VerifyCode' in text or '验证码用于确认这些请求是您的正常行为' in text


def fetchSearchPage(session, url, headers):
    r = session.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    if isVerifyPage(soup):
        fallback_headers = buildHeaders(cookie=None)
        r = session.get(url, headers=fallback_headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
    if isVerifyPage(soup):
        raise RuntimeError('Sogou Weixin returned a verification page')
    return soup


def parsePubDate(post):
    src = post.select_one('.s-p script')
    if not src:
        return ''
    m = re.search(r'(\d{10})', src.get_text() or '')
    if not m:
        return ''
    # 搜狗返回的时间戳是 UTC+8 中国时区，直接标记时区输出 ISO8601
    return arrow.get(int(m.group(1))).replace(tzinfo='+08:00').isoformat()


def extractRealUrl(html):
    m = re.search(
        r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']\d+;\s*url=([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if m and 'mp.weixin.qq.com' in m.group(1):
        return m.group(1)
    for pat in [
        r'location\.href\s*=\s*["\']([^"\']+)["\']',
        r'location\s*=\s*["\']([^"\']+)["\']',
        r'window\.location\s*=\s*["\']([^"\']+)["\']',
    ]:
        m = re.search(pat, html, re.IGNORECASE)
        if m and 'mp.weixin.qq.com' in m.group(1):
            return m.group(1)
    parts = re.findall(r'url\s*\+=\s*[\'"]([^\'"]*)[\'"]', html)
    if parts:
        joined = ''.join(parts)
        if 'mp.weixin.qq.com' in joined:
            return joined
    return None


def resolveRealUrl(sogou_url, session=None, retries=2):
    if 'mp.weixin.qq.com' in sogou_url:
        return sogou_url
    sess = session or requests.Session()
    for _ in range(retries):
        try:
            resp = sess.get(
                sogou_url,
                headers={
                    'User-Agent': getRandomUserAgent(),
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                },
                timeout=8,
                allow_redirects=False,
            )
            if 300 <= resp.status_code < 400:
                loc = resp.headers.get('location', '')
                if 'mp.weixin.qq.com' in loc:
                    return loc
                return sogou_url
            if resp.status_code == 200:
                real = extractRealUrl(resp.text)
                if real and 'mp.weixin.qq.com' in real:
                    return real
                return sogou_url
        except Exception:
            pass
        _time.sleep(0.3 + random.random() * 0.4)
    return sogou_url


def parseArticle(post, sess=None, resolve_url=True):
    title_a = post.select_one('h3 a')
    if not title_a:
        return None
    title = cleanText(title_a.get_text().strip())
    href = cleanText(title_a.get('href') or '')
    if href.startswith('/'):
        href = f"{domain}{href}"

    pubDate = parsePubDate(post)

    sp = post.select_one('.s-p')
    source = ''
    if sp:
        acc = sp.select_one('.all-time-y2') or sp.select_one('a.account')
        if acc:
            source = cleanText(acc.get_text().strip())

    summary = post.select_one('p.txt-info')
    summary_text = cleanText(summary.get_text().strip()) if summary else ''

    final_link = cleanText(href)
    url_resolved = False
    if resolve_url and '/link?' in href:
        final_link = resolveRealUrl(href, session=sess)
        url_resolved = 'mp.weixin.qq.com' in final_link

    desc_parts = []
    if source:
        desc_parts.append(f'<p><b>公众号:</b> {source}</p>')
    if pubDate:
        desc_parts.append(f'<p><b>发布时间:</b> {pubDate}</p>')
    if summary_text:
        desc_parts.append(f'<p>{summary_text}</p>')
    if resolve_url and url_resolved:
        desc_parts.append(f'<p><a href="{final_link}" target="_blank">阅读原文</a></p>')

    return cleanItem({
        'title': title,
        'link': final_link,
        'description': ''.join(desc_parts) or title,
        'pubDate': pubDate,
        'author': source,
    })


def ctx(gh='', pages=2, resolve_url=True, source_filter=None):
    """
    :param gh: 搜索关键词（公众号名/通用关键词）
    :param pages: 翻页数（默认 2 = 最多 20 条）
    :param resolve_url: 是否尝试解析为 mp.weixin.qq.com 真实链接
    :param source_filter: 若提供，仅保留公众号名包含该关键字的文章（用于按公众号过滤）
    """
    gh = cleanText(gh)
    original_gh = gh
    alias = GH_ALIASES.get(gh.lower())
    if alias:
        gh = alias.get('query', gh)
        source_filter = source_filter or alias.get('source_filter')
    source_filter = cleanText(source_filter) if source_filter else None
    cookie = getSogouCookie()
    headers = buildHeaders(cookie)

    base_url = (
        f"{domain}/weixin?type=2&s_from=input&query={requests.utils.quote(gh)}"
        f"&ie=utf8&_sug_=n&_sug_type_=&w=01019900&sut=1554&lkt=0%2C0%2C0"
    )

    sess = requests.Session()
    all_items = []
    fetch_error = ''
    for p in range(1, max(1, pages) + 1):
        try:
            page_url = f"{base_url}&page={p}"
            soup = fetchSearchPage(sess, page_url, headers)
            li_list = soup.select('ul.news-list li')
            if not li_list:
                break
            for li in li_list:
                item = parseArticle(li, sess=sess, resolve_url=resolve_url)
                if item:
                    if source_filter and source_filter not in (item.get('author') or ''):
                        continue
                    all_items.append(item)
            if p < pages:
                _time.sleep(0.5 + random.random() * 1.0)
        except Exception as exc:
            fetch_error = cleanText(str(exc))
            break

    # 按发布时间倒序
    all_items.sort(key=lambda x: x.get('pubDate') or '', reverse=True)

    filter_note = f'（公众号过滤: {source_filter}）' if source_filter else ''
    alias_note = f'（由 {original_gh} 映射）' if original_gh != gh else ''
    feed_title = f'{original_gh} - 微信公众号文章{filter_note}'

    if not all_items:
        empty_title = '搜狗微信触发验证码，暂时无法抓取' if fetch_error else '近期没有新文章'
        empty_description = (
            f'抓取 "{original_gh}" 时失败: {fetch_error}. 请稍后重试，或改用更可靠的数据源。'
            if fetch_error else f'未找到与 "{original_gh}" 相关的微信公众号文章{alias_note}'
        )
        return {
            'title': feed_title,
            'link': base_url,
            'description': empty_description,
            'author': 'hillerliao',
            'items': [{
                'title': empty_title,
                'description': empty_description,
                'link': base_url,
                'pubDate': '',
                'author': '',
            }],
        }

    return {
        'title': feed_title,
        'link': base_url,
        'description': f'搜狗微信文章搜索结果: {gh}{alias_note}',
        'author': 'hillerliao',
        'items': all_items,
    }
