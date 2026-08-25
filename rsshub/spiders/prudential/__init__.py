"""Shared utilities for prudential spiders."""
import re
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.prudential.com.hk'

# XML 1.0 invalid control characters
_XML_INVALID_RE = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')

# model.json 配置路径的正则（data-article-set-config 属性值）
CONFIG_RE = re.compile(r'data-article-set-config="([^"]+)"')

# JSON-LD 中的发布日期
DATE_JSONLD_RE = re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"')


def clean_xml(text):
    """Strip XML 1.0 invalid control characters and escape ]]> for CDATA."""
    return _XML_INVALID_RE.sub('', text).replace(']]>', ']]&gt;')


def fetch_article_config(session, url):
    """从分类页 HTML 中提取 articlelisting.model.json 的完整地址。

    Returns:
        str or None: model.json 绝对 URL
    """
    try:
        res = session.get(url, timeout=15)
        res.raise_for_status()
        m = CONFIG_RE.search(res.text)
        if not m:
            return None
        return urljoin('https://www.prudential.com.hk', m.group(1))
    except Exception:
        return None


def fetch_articles(session, config_url):
    """请求 articlelisting.model.json，返回文章列表 dict。"""
    try:
        res = session.get(config_url, timeout=15)
        res.raise_for_status()
        data = json.loads(res.text)
        return data.get('articles', []) or []
    except Exception:
        return []


def fetch_detail(session, url):
    """抓取单篇文章详情页，返回 (description_html, published_date)。

    description 由正文区域的 cmp-text 与 accordion 内容拼装，
    相对链接全部转为绝对链接。
    """
    try:
        res = session.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        h1 = soup.select_one('h1.article-title')
        if not h1:
            return '', None
        ce = h1.find_parent('div', class_='containerextension')
        if not ce:
            return '', None

        parts = []
        for c in ce.find_all('div', class_='cmp-text'):
            parts.append(c.decode_contents())
        for acc in ce.find_all('div', class_='cmp-accordion'):
            for t in acc.find_all('div', class_='cmp-accordion__title'):
                parts.append(f'<h3>{t.get_text(strip=True)}</h3>')
            for p in acc.find_all('div', class_='cmp-accordion__panel'):
                parts.append(p.decode_contents())

        html = ''.join(parts)
        if not html.strip():
            return '', None

        # 解析相对链接为绝对链接
        frag = BeautifulSoup(html, 'html.parser')
        for tag in frag.select('[href]'):
            href = tag.get('href', '')
            if href and not href.startswith(('#', 'http://', 'https://', 'mailto:', 'javascript:')):
                tag['href'] = urljoin(url, href)
        for tag in frag.select('[src]'):
            src = tag.get('src', '')
            if src and not src.startswith(('http://', 'https://', 'data:')):
                tag['src'] = urljoin(url, src)

        # 发布日期：优先 JSON-LD，回退 meta
        pub_date = None
        m = DATE_JSONLD_RE.search(res.text)
        if m:
            pub_date = m.group(1)
        if not pub_date:
            meta = soup.find('meta', attrs={'name': 'published-date'})
            if meta and meta.get('content'):
                pub_date = meta['content'][:10]

        return clean_xml(frag.decode_contents()), pub_date
    except Exception:
        return '', None
