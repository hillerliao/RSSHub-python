import re
import arrow
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from rsshub.utils import fetch, DEFAULT_HEADERS
from . import domain, DATE_RE, clean_xml, fetch_detail

JOURNAL_URL = f'{domain}/journal/'


def parse_item(li):
    """Parse a <li> element from journal page, handling 4 format variants:
    1. <li><a href="...">YYYY-MM-DD</a><br>description</li>
    2. <li><p>...YYYY-MM-DD...</p></li>
    3. <li>YYYY-MM-DD plain text no link</li>
    4. <li><a href="...">YYYY-MM-DD</a></li>  (link only, no description)
    """
    text = li.get_text(strip=True)
    link_elem = li.find('a')
    href = link_elem.get('href') if link_elem else None

    # Extract date from link text first, fallback to full text
    date_match = None
    if link_elem:
        date_match = DATE_RE.search(link_elem.get_text(strip=True))
    if not date_match:
        date_match = DATE_RE.search(text)

    if not date_match:
        return None

    date_str = date_match.group(1)
    title = f'日报 {date_str}'
    link = f'{domain}{href}' if href and href.startswith('/') else None
    if link is None:
        return None  # Skip items without a valid article link
    pub_date = arrow.get(date_str, tzinfo='Asia/Shanghai').format('ddd, DD MMM YYYY HH:mm:ss ZZ')

    # Short description fallback: everything after the date
    desc = text.replace(date_str, '', 1).strip()
    desc = re.sub(r'^[\s,，、。.·•\-\—\|]+', '', desc).strip()

    return {
        'title': title,
        'link': link,
        'description': clean_xml(desc),
        'pubDate': pub_date,
        'author': 'Yikecaiwan',
    }


def ctx():
    tree = fetch(JOURNAL_URL, headers=DEFAULT_HEADERS)
    empty_feed = {
        'title': '一刻财闻 · 美股晨报',
        'link': JOURNAL_URL,
        'description': '一刻财闻每日美股晨报',
        'author': 'yikecaiwan.com',
        'items': [],
    }

    if not tree:
        return empty_feed

    lis = tree.select('.vp-doc._journal_ ul li')
    items = []
    for li in lis:
        parsed = parse_item(li)
        if parsed:
            items.append(parsed)

    # Sort by link (which contains date) descending
    items.sort(key=lambda x: x.get('link', ''), reverse=True)

    # Fetch full text for each item in parallel with shared session
    if items:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        try:
            url_to_item = {item['link']: item for item in items}
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
                        pass  # Keep fallback description
        finally:
            session.close()

    return {
        'title': '一刻财闻 · 美股晨报',
        'link': JOURNAL_URL,
        'description': '一刻财闻每日美股晨报',
        'author': 'yikecaiwan.com',
        'items': items,
    }
