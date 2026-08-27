from datetime import datetime, timezone
import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://news.moomoo.com'

# 对应 moomoo 站点语言前缀: /hans/news (简中), /hant/news (繁中), /news (英文), /ja/news, /th/news
LANG_MAP = {
    'zh-cn': '0',
    'zh-hk': '1',
    'en-us': '2',
    'ja': '5',
    'th': '4',
}


def parse_news(news):
    title = news.get('title', '') or ''
    abstract = news.get('abstract', '') or ''
    pic = news.get('pic', '') or ''
    source = news.get('source', '') or ''
    url = news.get('url', '') or ''
    timestamp = news.get('timestamp', '')
    if timestamp:
        pubDate = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        pubDate = ''

    desc = ''
    if pic:
        desc += f'<p><img src="{pic}" referrerpolicy="no-referrer"/></p>'
    if abstract:
        desc += f'<p>{abstract}</p>'
    if source:
        desc += f'<p>来源：{source}</p>'

    return {
        'title': title,
        'description': desc,
        'link': url,
        'author': source,
        'pubDate': pubDate,
    }


def ctx(lang='zh-cn'):
    """
    抓取 moomoo 新闻主频道(市场要闻)列表。
    对应页面: https://www.moomoo.com/hans/news/main
    """
    lang_header = LANG_MAP.get(lang, '0')
    url = f'{domain}/news-site-api/main/get-market-list?size=50&isSupportWebp=true'

    headers = dict(DEFAULT_HEADERS)
    headers['x-news-site-lang'] = lang_header
    headers['news-nuxt-host'] = 'www.moomoo.com'
    headers['Referer'] = 'https://www.moomoo.com/hans/news/main'

    response = requests.get(url, headers=headers, timeout=10)
    data = response.json()

    if data.get('code') != 0:
        raise Exception(f'Moomoo API error: {data}')

    news_list = data.get('data', {}).get('list', [])
    items = [parse_news(news) for news in news_list if news.get('title')]

    return {
        'title': 'Moomoo 市场要闻',
        'link': 'https://www.moomoo.com/hans/news/main',
        'description': 'Moomoo 新闻主频道 - 市场要闻',
        'author': 'moomoo',
        'items': items,
    }
