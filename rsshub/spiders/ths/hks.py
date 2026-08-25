# -*- coding: utf-8 -*-
"""同花顺港股频道栏目列表页 RSS

栏目页均为服务端渲染的 GBK 编码 HTML,列表结构:
<div class="list-con">
  <ul>
    <li>
      <span class="arc-title">
        <a class="news-link" title="标题" href="http://stock.10jqka.com.cn/hks/20260825/cxxxx.shtml">标题</a>
        <span>08月25日 19:59</span>
      </span>
      <a class="arc-cont news-link" href="...">摘要</a>
    </li>
  </ul>
</div>
"""
import re

import arrow
import requests
from bs4 import BeautifulSoup

from rsshub.utils import DEFAULT_HEADERS

# 港股频道主页(聚合头条+各栏目最新内容)
HOME_URL = 'https://stock.10jqka.com.cn/hks/'

# 港股频道子栏目 -> (列表页 URL, 栏目名)
CATEGORY_MAP = {
    'hknews': ('https://stock.10jqka.com.cn/hks/hknews_list/', '要闻'),
    'ggfx': ('https://stock.10jqka.com.cn/hks/ggfx_list/', '盘面综述'),
    'ggdt': ('https://stock.10jqka.com.cn/hks/ggdt_list/', '公司新闻'),
    'ggyj': ('https://stock.10jqka.com.cn/hks/ggyj_list/', '研报精选'),
    'ahdt': ('https://stock.10jqka.com.cn/hks/ahdt_list/', 'AH动态'),
    'ggxg': ('https://stock.10jqka.com.cn/hks/ggxg_list/', '新股'),
    'ggydg': ('https://stock.10jqka.com.cn/hks/ggydg_list/', '异动股'),
    'wlzx': ('https://stock.10jqka.com.cn/hks/wlzx_list/', '权证'),
    'ggmj': ('https://stock.10jqka.com.cn/hks/ggmj_list/', '名家'),
}

# 接口超时(避免上游慢导致网关 504)
REQUEST_TIMEOUT = 8

# 页面时间格式: 08月25日 19:59
TIME_RE = re.compile(r'(\d{2})月(\d{2})日\s+(\d{2}):(\d{2})')
# 文章链接中的日期目录: /20260825/c679274125.shtml
URL_DATE_RE = re.compile(r'/(20\d{2})(\d{2})(\d{2})/')


def fetch_list(url):
    """抓取列表页 HTML 并解码为文本(优先 GBK,页面含个别非法字节时用 replace 兜底)"""
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Referer': 'https://stock.10jqka.com.cn/hks/',
        'Accept': 'text/html, */*;q=0.8',
    })
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    raw = res.content
    try:
        return raw.decode('gbk', errors='replace')
    except (UnicodeDecodeError, LookupError):
        return raw.decode('utf-8', errors='replace')


def parse_item(li):
    """从单个 li 解析出 (title, link, summary, time_str, url_date)"""
    a = li.select_one('a.news-link[title]')
    if a is None:
        a = li.select_one('a.arc-title')
    if a is None:
        return None
    title = (a.get('title') or a.get_text(strip=True) or '').strip()
    link = (a.get('href') or '').strip()
    if not title or not link:
        return None
    summary_el = li.select_one('a.arc-cont')
    summary = summary_el.get_text(strip=True) if summary_el else ''
    time_el = li.select_one('span.arc-title span')
    time_str = time_el.get_text(strip=True) if time_el else ''
    return title, link, summary, time_str


def build_pubdate(time_str, link):
    """由页面时间(08月25日 19:59)与链接中的日期目录拼出完整时间"""
    m = URL_DATE_RE.search(link)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        now = arrow.now()
        year, month, day = now.year, now.month, now.day
    hour = minute = 0
    tm = TIME_RE.search(time_str)
    if tm:
        month, day, hour, minute = int(tm.group(1)), int(tm.group(2)), int(tm.group(3)), int(tm.group(4))
    try:
        return arrow.get(year, month, day, hour, minute).isoformat()
    except (ValueError, TypeError):
        return arrow.now().isoformat()


def fetch_home_items(html):
    """主页聚合: 提取全部文章链接+标题(去重),头条区块带摘要"""
    soup = BeautifulSoup(html, 'html.parser')
    # 头条区(div.headList)的摘要,按链接映射
    head_summaries = {}
    for blk in soup.select('div.headList'):
        a = blk.select_one('h2 a[href]')
        p = blk.select_one('p.f14')
        if a and p and a.get('href'):
            head_summaries[a['href'].strip()] = p.get_text(strip=True)

    # 收集全部文章链接(同一链接多区块标题截断,取最长)
    merged = {}
    for a in soup.select('a[href]'):
        href = (a.get('href') or '').strip()
        if '10jqka.com.cn' not in href or not re.search(r'/c\d+\.shtml$', href):
            continue
        title = (a.get('title') or a.get_text(strip=True) or '').strip()
        if not title or len(title) < 4:
            continue
        if href not in merged or len(title) > len(merged[href]):
            merged[href] = title

    items = []
    for href, title in merged.items():
        items.append({
            'title': title,
            'link': href,
            'description': head_summaries.get(href, title),
            'author': '同花顺',
            'pubDate': build_pubdate('', href),
        })
    return items


def ctx(category='home'):
    if category in ('home', '') or category not in CATEGORY_MAP:
        url, name = HOME_URL, '港股主页'
        try:
            html = fetch_list(url)
        except Exception as e:
            print(f'[ths/hks] Fetch failed: {e}')
            html = ''
        items = fetch_home_items(html) if html else []
    else:
        url, name = CATEGORY_MAP[category]
        try:
            html = fetch_list(url)
        except Exception as e:
            print(f'[ths/hks] Fetch failed: {e}')
            html = ''
        items = []
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for li in soup.select('div.list-con ul li'):
                try:
                    parsed = parse_item(li)
                    if not parsed:
                        continue
                    title, link, summary, time_str = parsed
                    if '10jqka.com.cn' not in link or not link.endswith('.shtml'):
                        continue
                    items.append({
                        'title': title,
                        'link': link,
                        'description': summary or title,
                        'author': '同花顺',
                        'pubDate': build_pubdate(time_str, link),
                    })
                except Exception as e:
                    print(f'[ths/hks] Skipping bad item: {e}')

    return {
        'title': f'同花顺港股-{name}',
        'link': url,
        'description': f'同花顺港股频道-{name}',
        'author': '同花顺',
        'items': items,
    }
