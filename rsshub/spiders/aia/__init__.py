"""Shared utilities for aia (友邦香港) spiders."""
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# XML 1.0 invalid control characters
_XML_INVALID_RE = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')

# 中文日期，如「2026年7月24日」
CN_DATE_RE = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')


def clean_xml(text):
    """Strip XML 1.0 invalid control characters and escape ]]> for CDATA."""
    return _XML_INVALID_RE.sub('', text).replace(']]>', ']]&gt;')


def parse_cn_date(text):
    """解析中文日期「2026年7月24日」为 YYYY-MM-DD，失败返回 None。"""
    m = CN_DATE_RE.search(text or '')
    if not m:
        return None
    year, month, day = m.groups()
    return f'{year}-{int(month):02d}-{int(day):02d}'


def fetch_detail(session, url):
    """抓取单篇新闻稿详情页，返回正文 HTML（含图片，相对链接转绝对链接）。

    Returns:
        str: description HTML，失败返回空字符串
    """
    try:
        res = session.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        primary = soup.select_one('div.cmp-flexcolumn--primary')
        if not primary:
            return ''

        parts = []
        # 正文段落、图片说明、備註等；截断固定模板内容（「關於友邦…」及之后）
        for t in primary.select('div.text div.cmp-text'):
            text = t.decode_contents().strip()
            if not text:
                continue
            # 跳过纯分隔符块「#####」
            if '#####' in text and not t.get_text(strip=True).replace('#####', '').strip():
                continue
            idx = text.find('關於友邦')
            if idx != -1:
                head = text[:idx].strip()
                if head:
                    parts.append(head)
                break
            parts.append(text)
        # 正文图片
        for img_wrap in primary.select('div.image'):
            img = img_wrap.select_one('noscript img')
            if img is not None:
                src = img.get('src', '')
                alt = img.get('alt', '')
                if src:
                    parts.append(f'<img src="{src}" alt="{alt}"/>')

        html = '<p></p>'.join(parts) if parts else ''
        if not html.strip():
            return ''

        # 相对链接转绝对链接
        frag = BeautifulSoup(html, 'html.parser')
        for tag in frag.select('[href]'):
            href = tag.get('href', '')
            if href and not href.startswith(('#', 'http://', 'https://', 'mailto:', 'javascript:')):
                tag['href'] = urljoin(url, href)
        for tag in frag.select('[src]'):
            src = tag.get('src', '')
            if src and not src.startswith(('http://', 'https://', 'data:')):
                tag['src'] = urljoin(url, src)

        return clean_xml(frag.decode_contents())
    except Exception:
        return ''
