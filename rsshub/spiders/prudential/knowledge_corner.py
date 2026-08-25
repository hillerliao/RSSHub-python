import arrow
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from rsshub.utils import DEFAULT_HEADERS
from . import domain, clean_xml, fetch_article_config, fetch_articles, fetch_detail

BASE = f'{domain}/sc/knowledge-corner'


def ctx(category='understanding-insurance'):
    """Prudential Hong Kong 保险知识（Knowledge Corner）RSS。

    category: 分类 URL 段，默认 understanding-insurance（保险入门）。
    """
    page_url = f'{BASE}/{category}/'

    empty_feed = {
        'title': f'Prudential 保险知识 · {category}',
        'link': page_url,
        'description': 'Prudential Hong Kong Knowledge Corner 保险知多啲',
        'author': 'Prudential Hong Kong',
        'items': [],
    }

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    try:
        config_url = fetch_article_config(session, page_url)
        if not config_url:
            return empty_feed
        articles = fetch_articles(session, config_url)
    except Exception:
        return empty_feed

    items = []
    for art in articles:
        path = art.get('path') or ''
        heading = art.get('heading') or ''
        category_name = art.get('category') or ''
        creation_date = art.get('creationDate') or ''
        if not path or not heading:
            continue

        link = domain + path if path.startswith('/') else path
        item = {
            'title': clean_xml(heading),
            'link': link,
            'author': 'Prudential Hong Kong',
            'description': clean_xml(category_name),
        }

        # 发布日期：model.json 中 creationDate 为 DD-MM-YYYY
        try:
            d = arrow.get(creation_date, 'DD-MM-YYYY', tzinfo='Asia/Hong_Kong')
            item['pubDate'] = d.format('ddd, DD MMM YYYY HH:mm:ss ZZ')
        except Exception:
            pass

        item['_order'] = creation_date
        items.append(item)

    # 抓取详情页正文，填入 description
    if items:
        try:
            url_to_item = {item['link']: item for item in items}
            urls = list(url_to_item)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(fetch_detail, session, url): url for url in urls}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        html, pub_date = future.result()
                        item = url_to_item[url]
                        if html:
                            item['description'] = f'<p><strong>{item["description"]}</strong></p>' + html
                        if pub_date:
                            try:
                                item['pubDate'] = arrow.get(pub_date, tzinfo='Asia/Hong_Kong').format('ddd, DD MMM YYYY HH:mm:ss ZZ')
                            except Exception:
                                pass
                    except Exception:
                        pass
        finally:
            session.close()

    # 按日期倒序（DD-MM-YYYY 无法直接排序，转为 ISO）
    def sort_key(item):
        try:
            return arrow.get(item.get('_order', ''), 'DD-MM-YYYY').format('YYYY-MM-DD')
        except Exception:
            return '0000-00-00'

    items.sort(key=sort_key, reverse=True)
    for item in items:
        item.pop('_order', None)

    return {
        'title': f'Prudential 保险知识 · {category}',
        'link': page_url,
        'description': 'Prudential Hong Kong Knowledge Corner 保险知多啲',
        'author': 'Prudential Hong Kong',
        'items': items,
    }
