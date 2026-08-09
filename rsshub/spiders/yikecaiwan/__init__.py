"""Shared utilities for yikecaiwan spiders."""
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://yikecaiwan.com'

# XML 1.0 invalid control characters
_XML_INVALID_RE = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')
# Date pattern YYYY-MM-DD
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')
# Journal URL pattern
JOURNAL_RE = re.compile(r'/journal/(\d{4}-\d{2}-\d{2})$')
# Weekly URL pattern
WEEKLY_RE = re.compile(r'/weekly/(\d{4}-W\d{2})$')


def clean_xml(text):
    """Strip XML 1.0 invalid control characters and escape ]]> for CDATA."""
    return _XML_INVALID_RE.sub('', text).replace(']]>', ']]&gt;')


def fetch_detail(session, url):
    """Fetch a single detail page, return cleaned HTML from .vp-doc.

    Args:
        session: requests.Session with headers already set.
        url: Full URL of the page to fetch.

    Returns:
        HTML string of .vp-doc content with relative links resolved,
        or '' on any failure.
    """
    try:
        res = session.get(url, timeout=15)
        res.raise_for_status()
        tree = BeautifulSoup(res.text, 'html.parser')

        vp_doc = tree.select_one('.vp-doc')
        if not vp_doc:
            return ''

        # Clean up non-content elements
        for tag in vp_doc.select('.header-anchor, nav, script, style'):
            tag.decompose()

        # Resolve relative URLs to absolute
        for tag in vp_doc.select('[href]'):
            href = tag.get('href', '')
            if href and not href.startswith(('#', 'http://', 'https://', 'mailto:', 'javascript:')):
                tag['href'] = urljoin(url, href)
        for tag in vp_doc.select('[src]'):
            src = tag.get('src', '')
            if src and not src.startswith(('http://', 'https://', 'data:')):
                tag['src'] = urljoin(url, src)

        return clean_xml(vp_doc.decode_contents())
    except Exception:
        return ''
