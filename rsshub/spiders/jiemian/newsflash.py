import requests
import arrow
from bs4 import BeautifulSoup
from datetime import datetime

domain = 'https://www.jiemian.com'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': domain,
}


def parse(post):
    item = {}
    a_tag = post.select_one('.columns-right-center__newsflash-content h4 a')
    item['title'] = a_tag.text.strip() if a_tag else ''
    item['link'] = a_tag.get('href') if a_tag else ''
    summary = post.select_one('.columns-right-center__newsflash-content__summary')
    item['description'] = summary.text.strip() if summary else ''
    ts = post.get('data-time')
    if ts:
        try:
            item['pubDate'] = arrow.get(int(ts)).isoformat()
        except (ValueError, TypeError):
            item['pubDate'] = arrow.now().isoformat()
    else:
        node = post.select_one('.columns-right-center__newsflash-date-node')
        today = datetime.now().strftime('%Y-%m-%d')
        node_text = node.text.strip() if node else '00:00'
        item['pubDate'] = arrow.get(f'{today} {node_text}', 'YYYY-MM-DD HH:mm').isoformat()
    return item


def ctx(category=''):
    url = f'{domain}/lists/{category}.html'
    res = requests.get(url, headers=HEADERS)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    posts = soup.select('.columns-right-center__newsflash-item')

    # 解析当前分类的中文名称
    # 优先：左侧导航中 href 与当前 URL 精确匹配的项（子栏目页，如 166 -> 金融快讯）
    # 回退：频道头 h2 的频道名（频道主页，如 4 -> 快报）
    name = category
    channel = soup.select_one('#header-nav h2')
    channel_name = ''
    if channel:
        channel_name = channel.get('data-title') or channel.get_text(strip=True) or ''
    nav = soup.select_one('#columns-left-nav__list')
    if nav:
        current = url.rstrip('/')
        for a in nav.select('li a'):
            if (a.get('href') or '').rstrip('/') == current:
                t = a.get_text().strip()
                if t and t != '首页':
                    name = t
                    break
        else:
            if channel_name:
                name = channel_name

    items = list(map(parse, posts))
    return {
        'title': f'{name} - 界面新闻',
        'link': url,
        'description': f'{name} - 界面新闻',
        'author': 'hillerliao',
        'items': items
    }
