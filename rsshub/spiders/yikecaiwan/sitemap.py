import requests
from bs4 import BeautifulSoup
import arrow
from concurrent.futures import ThreadPoolExecutor, as_completed
from rsshub.utils import DEFAULT_HEADERS
from . import domain, JOURNAL_RE, WEEKLY_RE, clean_xml, fetch_detail

SITEMAP_URL = f'{domain}/sitemap.xml'


def classify_url(url):
    """Classify a sitemap URL, return (type, title, pubDate or None, sort_key)."""
    path = url.replace(domain, '').rstrip('/')

    m = JOURNAL_RE.search(path)
    if m:
        date_str = m.group(1)
        pub_date = arrow.get(date_str, tzinfo='Asia/Shanghai').format('ddd, DD MMM YYYY HH:mm:ss ZZ')
        return ('journal', f'日报 {date_str}', pub_date, date_str)

    m = WEEKLY_RE.search(path)
    if m:
        week_str = m.group(1)
        try:
            week_date = arrow.get(week_str + '-1', 'YYYY-[W]WW-D', tzinfo='Asia/Shanghai')
            sort_key = week_date.format('YYYY-MM-DD')
            pub_date = week_date.format('ddd, DD MMM YYYY HH:mm:ss ZZ')
        except Exception:
            sort_key = ''
            pub_date = arrow.now().format('ddd, DD MMM YYYY HH:mm:ss ZZ')
        return ('weekly', f'周报 {week_str}', pub_date, sort_key)

    # Wiki articles and other static pages
    title = wiki_title_from_path(path)
    return ('wiki', title, None, '')


def wiki_title_from_path(path):
    """Generate a readable title from a URL path."""
    if not path or path == '/':
        return 'Home'

    segments = [s for s in path.split('/') if s]
    if not segments:
        return 'Home'

    if len(segments) == 1:
        return segments[0].replace('-', ' ')

    return ' / '.join(s.replace('-', ' ') for s in segments)


def ctx():
    empty_feed = {
        'title': '一刻财闻 · 全站 RSS',
        'link': domain,
        'description': 'yikecaiwan.com 全站文章（基于 sitemap.xml）',
        'author': 'yikecaiwan.com',
        'items': [],
    }

    try:
        res = requests.get(SITEMAP_URL, headers=DEFAULT_HEADERS, timeout=15)
        res.raise_for_status()
        try:
            tree = BeautifulSoup(res.text, 'xml')
        except Exception:
            # Vercel 环境的 requirements.txt 未包含 lxml，回退到 html.parser
            tree = BeautifulSoup(res.text, 'html.parser')
    except Exception:
        return empty_feed

    locs = tree.select('url loc')
    if not locs:
        locs = tree.select('loc')

    dated_items = []
    wiki_items = []

    for loc in locs:
        url = loc.get_text(strip=True)
        if not url:
            continue

        item_type, title, pub_date, sort_key = classify_url(url)

        item = {
            'title': title,
            'link': url,
            'description': clean_xml(title),
            'author': 'yikecaiwan.com',
        }
        if pub_date:
            item['pubDate'] = pub_date
            item['_sort_key'] = sort_key
            dated_items.append(item)
        else:
            wiki_items.append(item)

    # Sort: dated items by sort_key (YYYY-MM-DD) descending
    dated_items.sort(key=lambda x: x.get('_sort_key', ''), reverse=True)
    wiki_items.sort(key=lambda x: x.get('link', ''))

    # Fetch full text for dated items in parallel with shared session
    if dated_items:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        try:
            url_to_item = {item['link']: item for item in dated_items}
            urls = list(url_to_item)
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(fetch_detail, session, url): url for url in urls}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        html = future.result()
                        if html and url in url_to_item:
                            url_to_item[url]['description'] = html
                    except Exception:
                        pass
        finally:
            session.close()

    # Remove internal sort key
    for item in dated_items:
        item.pop('_sort_key', None)

    all_items = dated_items + wiki_items

    return {
        'title': '一刻财闻 · 全站 RSS',
        'link': domain,
        'description': 'yikecaiwan.com 全站文章（基于 sitemap.xml），含日报、周报及百科文章',
        'author': 'yikecaiwan.com',
        'items': all_items,
    }
