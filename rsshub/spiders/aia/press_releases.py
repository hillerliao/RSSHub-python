import arrow
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS
from . import clean_xml, parse_cn_date, fetch_detail

BASE = 'https://www.aia.com.hk/zh-hk/about-aia/about-us/media-centre/press-releases'
DOMAIN = 'https://www.aia.com.hk'


def ctx():
    """AIA Hong Kong（友邦香港）新闻稿 RSS。

    列表页服务端渲染当年全部新闻稿，逐篇抓取详情页正文作为 description。
    """
    empty_feed = {
        'title': 'AIA Hong Kong 新闻稿',
        'link': BASE,
        'description': 'AIA Hong Kong（友邦香港）新聞稿 Press Releases',
        'author': 'AIA Hong Kong',
        'items': [],
    }

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    try:
        res = session.get(BASE, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
    except Exception:
        session.close()
        return empty_feed

    items = []
    card_list = soup.select_one('.cmp-cardlistfilter__list.show')
    if card_list:
        for card in card_list.select('.cmp-promotioncard'):
            a = card.select_one('a.cmp-promotioncard__link')
            title_el = card.select_one('.cmp-promotioncard__title')
            date_el = card.select_one('.cmp-promotioncard__date')
            if not a or not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            link = a.get('href', '')
            if not link:
                continue
            if link.startswith('/'):
                link = DOMAIN + link

            item = {
                'title': clean_xml(title),
                'link': link,
                'author': 'AIA Hong Kong',
                'description': '',
            }

            # 发布日期：列表页中文日期「2026年7月24日」
            iso_date = parse_cn_date(date_el.get_text(strip=True))
            if iso_date:
                try:
                    d = arrow.get(iso_date, 'YYYY-MM-DD', tzinfo='Asia/Hong_Kong')
                    item['pubDate'] = d.format('ddd, DD MMM YYYY HH:mm:ss ZZ')
                except Exception:
                    pass
                item['_order'] = iso_date

            items.append(item)

    # 并发抓取详情页正文，填入 description
    if items:
        try:
            url_to_item = {item['link']: item for item in items}
            urls = list(url_to_item)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(fetch_detail, session, url): url for url in urls}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        html = future.result()
                        if html:
                            url_to_item[url]['description'] = html
                    except Exception:
                        pass
        finally:
            session.close()

    # 按日期倒序
    items.sort(key=lambda i: i.get('_order', '0000-00-00'), reverse=True)
    for item in items:
        item.pop('_order', None)

    return {
        'title': 'AIA Hong Kong 新闻稿',
        'link': BASE,
        'description': 'AIA Hong Kong（友邦香港）新聞稿 Press Releases',
        'author': 'AIA Hong Kong',
        'items': items,
    }
