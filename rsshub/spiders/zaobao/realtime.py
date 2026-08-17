from rsshub.utils import fetch
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.zaobao.com.sg'

# 旧版即时新闻分类映射到新版 news 栏目
# 旧的 /realtime/{category} 已迁移为 /news/{category}（realtime/sea、realtime/sports 等返回 404）
CATEGORY_MAP = {
    'china': 'china',
    'singapore': 'singapore',
    'world': 'world',
    'sea': 'sea',
    'sports': 'sports',
    'realtime': 'china',  # 兜底
}


def parse(post):
    item = {}
    title_elem = post.select_one('div.content-header a h2')
    title_text = title_elem.get_text(strip=True) if title_elem else ''
    # Decode unicode escapes if present
    try:
        item['description'] = item['title'] = title_text.encode('latin1').decode('utf-8')
    except:
        item['description'] = item['title'] = title_text
    link_elem = post.select_one('div.content-header a[href]')
    if link_elem and link_elem.get('href'):
        item['link'] = domain + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
    else:
        item['link'] = ''
    return item


def ctx(category=''):
    category = CATEGORY_MAP.get(category, category or 'china')
    url = f"{domain}/news/{category}"
    headers = DEFAULT_HEADERS.copy()
    tree = fetch(url, headers=headers)
    if tree is None:
        return {
            'title': f'{category} - 早报网即时新闻',
            'link': url,
            'description': f'{category} - 早报网即时新闻',
            'author': 'hillerliao',
            'items': []
        }
    posts = tree.select('div.card.vertical-article-card')
    return {
        'title': f'{category} - 早报网即时新闻',
        'link': url,
        'description': f'{category} - 早报网即时新闻',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }
