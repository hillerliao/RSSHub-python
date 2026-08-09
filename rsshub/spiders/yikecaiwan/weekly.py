import re
from datetime import date
from concurrent.futures import ThreadPoolExecutor

import requests

from rsshub.utils import fetch, DEFAULT_HEADERS
from . import domain, clean_xml, fetch_detail

# 周报链接形如 /weekly/2026-W30（兼容 VitePress 的 .html 后缀）
week_re = re.compile(r'/weekly/(\d{4})-W(\d{2})(?:\.html)?/?$')
# 标题中的日期区间，如 "2026年30周(7.27-7.31)"
range_re = re.compile(
    r'(\d{4})\s*年(?:第)?\s*(\d+)\s*周\s*[（(]\s*(\d{1,2})\.(\d{1,2})\s*[-~–]\s*(\d{1,2})\.(\d{1,2})\s*[)）]'
)


def parse_pubdate(title, year, week):
    """从标题的日期区间提取结束日；解析失败时按 ISO 周号推算周五日期"""
    m = range_re.search(title)
    if m:
        y = int(m.group(1))
        sm, em, ed = int(m.group(3)), int(m.group(5)), int(m.group(6))
        if em < sm:  # 12月~1月跨年
            y += 1
        return f'{y:04d}-{em:02d}-{ed:02d}'
    try:
        return date.fromisocalendar(int(year), int(week), 5).isoformat()
    except ValueError:
        return ''


def ctx():
    url = f'{domain}/weekly/'
    feed = {
        'title': '一颗财丸 - 周报',
        'link': url,
        'description': '一颗财丸(yikecaiwan.com)每周投资周报',
        'author': 'hillerliao',
        'items': []
    }
    tree = fetch(url)
    if not tree:
        return feed

    issues = {}
    # 周报链接在 VitePress 侧边栏中；导航/分页器里也有同链接但文本不规范，仅在无侧边栏时兜底
    anchors = tree.select('aside.VPSidebar a[href]') or tree.select('a[href]')
    for a in anchors:
        m = week_re.search(a.get('href', ''))
        if not m:
            continue
        key = (int(m.group(1)), int(m.group(2)))
        title = clean_xml(a.get_text(strip=True))
        # 侧边栏标题最长（含周数和日期区间），导航等处的短标题跳过
        if key in issues and len(title) <= len(issues[key]['title']):
            continue
        issues[key] = {
            'title': title or f'{key[0]}年第{key[1]}周周报',
            'link': f'{domain}/weekly/{key[0]:04d}-W{key[1]:02d}',
            'pubDate': parse_pubdate(title, key[0], key[1]),
            'author': '一颗财丸'
        }

    keys = sorted(issues, reverse=True)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    try:
        def enrich(key):
            item = issues[key]
            html = fetch_detail(session, item['link'])
            item['description'] = html or clean_xml(item['title'])
            return item

        with ThreadPoolExecutor(max_workers=5) as executor:
            feed['items'] = list(executor.map(enrich, keys))
    finally:
        session.close()
    return feed
