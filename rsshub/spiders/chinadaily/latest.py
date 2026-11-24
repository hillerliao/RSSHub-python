import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from rsshub.utils import fetch_with_deadline

domain = 'https://www.chinadaily.com.cn'

# 默认抓取页面:China 频道 Latest(最新)列表
# https://www.chinadaily.com.cn/china/59b8d010a3108c54ed7dfc23
DEFAULT_SECTION = 'china/59b8d010a3108c54ed7dfc23'

# 抓取预算(秒):页面约 220KB,海外机房通常 1~4s 可完成。
REQUEST_BUDGET = 7.0


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _abs_url(href):
    """把协议相对/站内相对链接补全为 https 绝对链接。"""
    if href.startswith('http'):
        return href
    if href.startswith('//'):
        return 'https:' + href
    return domain + href if href.startswith('/') else href


def _parse_item(block):
    """解析单条 tw3_01_2 块,返回 item dict(或 None)。"""
    a = block.select_one('h4 a[href]')
    if not a:
        return None
    link = _abs_url(a['href'].strip())
    title = _clean(a.get_text())
    if not title:
        return None

    item = {
        'title': title,
        'link': link,
        'description': title,
    }

    # 可选的缩略图,放进 description 便于阅读器展示
    img = block.select_one('img')
    if img and img.get('src'):
        item['description'] = (f'<p><img src="{_abs_url(img["src"].strip())}"/></p>'
                               f'<p>{title}</p>')

    # 发布时间:<b>2026-09-07 16:54</b>,北京时间东八区
    t = block.select_one('b')
    if t:
        try:
            dt = datetime.strptime(t.get_text(strip=True), '%Y-%m-%d %H:%M')
            dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            item['pubDate'] = dt.isoformat()
        except ValueError:
            pass
    return item


def ctx(section=DEFAULT_SECTION):
    section = (section or DEFAULT_SECTION).strip().strip('/')
    url = f'{domain}/{section}'
    res = fetch_with_deadline(url, deadline=REQUEST_BUDGET,
                              timeout=REQUEST_BUDGET + 1.0)
    tree = BeautifulSoup(res.text, 'html.parser')

    # 频道名取自页面 <title>: 如 "Latest - Chinadaily.com.cn"
    channel = 'China Daily'
    if tree.title:
        t = _clean(tree.title.get_text())
        channel = t.split(' - ')[0] if ' - ' in t else t

    items = []
    seen = set()
    for block in tree.select('div.tw3_01_2'):
        item = _parse_item(block)
        if not item or item['link'] in seen:
            continue
        seen.add(item['link'])
        items.append(item)

    if not items:
        raise RuntimeError(f'China Daily 列表解析为空(页面结构可能已变更): {url}')

    return {
        'title': f'{channel} - China Daily',
        'link': url,
        'description': f'China Daily - {channel} 频道新闻列表',
        'author': 'China Daily',
        'items': items,
    }
