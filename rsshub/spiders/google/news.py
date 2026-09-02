# -*- coding: utf-8 -*-
"""Google 新闻搜索 RSS。

把 ``https://news.google.com/rss/search?q=...`` 封装成本站的 RSS 节点，
关键词 / 限定站点 / 语言 / 时间范围全部用 URL 参数配置：

    /google/news/火了|财富密码|流量密码?site=36kr.com&hl=zh-CN&gl=CN&when=7d

**为什么默认按标题排重**

Google News 的 ``<guid>`` 是「文章簇 ID」，同一篇文章被同一站点重复收录时
会拿到**不同**的 guid —— 实测 36 氪的「36氪_让一部分人先看到未来」在同一次
请求里出现了 3 次，3 个 guid 各不相同，所以按 guid 排重抓不到这类重复。

``<link>`` 是 ``news.google.com/rss/articles/<CBMi...>`` 跳转地址，每条唯一，
按 link 排重等于不去重（而且真实原文地址并不在 feed 里，Google 自 2024 年起
改成了需要 batchexecute 才能解出的混淆 ID，服务端强解既慢又易失败）。

因此默认策略是 **归一化标题**：去掉「 - 来源」后缀，忽略大小写、空白、
中英文标点、全角/半角差异后再比对，只把标题完全相同的条目并成一条。

需要注意：标题近似并不等于重复。比如「长汀县气象台发布**暴雨**黄色
预警信号」和「…**雷电**黄色预警信号」句式雷同，但这是两次不同的事件，
不应合并。所以近似标题合并默认**关闭**，需要时再显式开启：
``?similar=0.9`` 会把标题相似度 ≥0.9 的条目并成一条（保留最新），
常用于同一条通稿被多个站点转载、标题略有出入的场景。
"""

import calendar
import re
import unicodedata
from difflib import SequenceMatcher
from html import escape
from urllib.parse import urlencode

import arrow
import feedparser

from rsshub.utils import DEFAULT_HEADERS, fetch_with_deadline

RSS_ENDPOINT = 'https://news.google.com/rss/search'
SEARCH_ENDPOINT = 'https://news.google.com/search'
# Vercel 网关 10s 限制，给抓取留 8s 硬截止
FETCH_DEADLINE = 8.0
FETCH_TIMEOUT = 6.0

DEFAULT_HL = 'zh-CN'
DEFAULT_GL = 'CN'

# 支持的排重策略
DEDUP_MODES = ('title', 'title+source', 'guid', 'link', 'none')

_WHEN_RE = re.compile(r'^\d+[hdwmy]$')
_TITLE_SEPARATORS = (' - ', ' – ', ' — ', ' | ', '｜', ' · ', '・')
# 归一化标题时要剔除的字符：空白、CJK 标点、全角符号、通用标点、ASCII 标点
_NOISE_RE = re.compile(
    '['
    '\\s'
    '\\u3000-\\u303f'  # CJK 标点 、。《》「」
    '\\uff01-\\uff65'  # 全角标点 ！＂＃，．？
    '\\u2010-\\u2027'  # 通用标点 ‐-‧
    '!-/:-@\\[-`{-~'   # ASCII 标点
    ']+'
)
_HL_TO_LANG = (
    ('zh-cn', 'zh-Hans'),
    ('zh-hans', 'zh-Hans'),
    ('zh-sg', 'zh-Hans'),
    ('zh-my', 'zh-Hans'),
    ('zh-tw', 'zh-Hant'),
    ('zh-hk', 'zh-Hant'),
    ('zh-mo', 'zh-Hant'),
    ('zh-hant', 'zh-Hant'),
)


# --------------------------------------------------------------------------
# 查询串构造
# --------------------------------------------------------------------------
def split_terms(value):
    """把 'a|b,c' 拆成 ['a', 'b', 'c']。"""
    if not value:
        return []
    return [term.strip() for term in re.split(r'[|,，、]+', str(value)) if term.strip()]


def _quote(term):
    """含空格的关键词要加引号，否则 Google 会当成多个词。"""
    term = str(term).strip().replace('"', '')
    return '"%s"' % term if re.search(r'\s', term) else term


def _clean_site(site):
    """'https://www.36kr.com/p/1' -> '36kr.com'"""
    site = re.sub(r'^[a-zA-Z]+://', '', str(site).strip())
    site = site.split('/')[0].split('?')[0].strip()
    site = re.sub(r'^www\.', '', site)
    return site


def build_query(keywords, sites=(), intitle=True, exclude=(), when=''):
    """拼出 Google News 的 q 参数。

    >>> build_query(['火了', '财富密码'], ['36kr.com'], when='7d')
    '(intitle:火了 OR intitle:财富密码) site:36kr.com when:7d'
    """
    keywords = [_quote(k) for k in keywords if str(k).strip()]
    if not keywords:
        raise ValueError('缺少关键词：请通过路径或 ?q= 传入')

    if intitle:
        chunks = ['(%s)' % ' OR '.join('intitle:%s' % k for k in keywords)]
    else:
        chunks = ['(%s)' % ' OR '.join(keywords)]

    sites = [_clean_site(s) for s in sites if str(s).strip()]
    if len(sites) == 1:
        chunks.append('site:%s' % sites[0])
    elif len(sites) > 1:
        chunks.append('(%s)' % ' OR '.join('site:%s' % s for s in sites))

    for term in exclude:
        term = _quote(term)
        if term:
            chunks.append('-%s' % term)

    if when:
        when = str(when).strip().lower()
        if not _WHEN_RE.match(when):
            raise ValueError('when 参数格式应为「数字+单位」，单位取 h/d/w/m/y，如 7d、24h')
        chunks.append('when:%s' % when)

    return ' '.join(chunks)


def build_ceid(gl, hl):
    """由地区 + 语言推导 ceid，如 ('CN', 'zh-CN') -> 'CN:zh-Hans'。"""
    gl = (str(gl) or DEFAULT_GL).strip().upper()
    hl = (str(hl) or DEFAULT_HL).strip().lower()
    lang = next((code for prefix, code in _HL_TO_LANG if hl.startswith(prefix)), None)
    if lang is None:
        lang = hl.split('-')[0] or 'zh'
    return '%s:%s' % (gl, lang)


# --------------------------------------------------------------------------
# 标题归一化 / 排重
# --------------------------------------------------------------------------
def normalize_title(title):
    """归一化标题用于排重：全角转半角、去标点空白、统一小写。"""
    text = unicodedata.normalize('NFKC', title or '').strip().lower()
    return _NOISE_RE.sub('', text)


def split_source(title, source=''):
    """拆出 '文章标题 - 来源' 里的来源名。

    优先用 feed 里给出的 source 名称去匹配后缀，匹配不到再按分隔符兜底。
    """
    title = (title or '').strip()
    source = (source or '').strip()
    if source:
        for sep in _TITLE_SEPARATORS:
            suffix = sep + source
            if title.endswith(suffix) and len(title) > len(suffix):
                return title[: -len(suffix)].strip(), source
    for sep in _TITLE_SEPARATORS:
        head, found, tail = title.rpartition(sep)
        if found and head.strip() and 0 < len(tail.strip()) <= 40:
            return head.strip(), tail.strip()
    return title, ''


def _dedup_key(item, strategy):
    if strategy == 'guid':
        return ('guid', item['guid'] or item['link'])
    if strategy == 'link':
        return ('link', item['link'])
    if strategy == 'title+source':
        return ('title+source', item['source'], item['_title_key'])
    return ('title', item['_title_key'])


def dedup_items(items, strategy='title', similar=0.0):
    """排重，重复项保留发布时间最新的那条。

    :param strategy: title / title+source / guid / link / none
    :param similar: >0 且策略为 title 时启用近似标题合并
                    （SequenceMatcher 相似度阈值），跨来源比较
    """
    strategy = normalize_dedup(strategy)
    if strategy == 'none':
        return list(items)

    kept = {}
    for item in items:
        key = _dedup_key(item, strategy)
        previous = kept.get(key)
        if previous is None or item['_ts'] > previous['_ts']:
            kept[key] = item
    result = list(kept.values())

    if similar and similar > 0 and strategy == 'title':
        result = _fuzzy_dedup(result, similar)
    return result


def normalize_dedup(value):
    value = (str(value) or 'title').strip().lower().replace(',', '+')
    if value.startswith('guid'):
        return 'guid'
    if value.startswith('link') or value in ('url',):
        return 'link'
    if 'source' in value:
        return 'title+source'
    if value in ('0', 'off', 'false', 'no', 'none'):
        return 'none'
    return 'title'


def _fuzzy_dedup(items, threshold):
    """近似标题合并：标题相似度达到阈值的条目并成一条，保留最新。

    归一化标题已去掉「 - 来源」后缀，因此同一条通稿/快讯被不同站点收录、
    标题略有出入也能识别（不再限制必须同源）。
    """
    result = []
    for item in items:
        duplicate_of = None
        for index, kept in enumerate(result):
            ratio = SequenceMatcher(None, item['_title_key'], kept['_title_key']).ratio()
            if ratio >= threshold:
                duplicate_of = index
                break
        if duplicate_of is None:
            result.append(item)
        elif item['_ts'] > result[duplicate_of]['_ts']:
            result[duplicate_of] = item
    return result


# --------------------------------------------------------------------------
# 抓取 / 解析
# --------------------------------------------------------------------------
def fetch_feed(params, deadline=FETCH_DEADLINE, timeout=FETCH_TIMEOUT):
    """抓取 Google News RSS，返回 feedparser entries。

    单独抽出来方便测试时打桩（mock）掉网络请求。
    """
    res = fetch_with_deadline(
        '%s?%s' % (RSS_ENDPOINT, urlencode(params)),
        headers=DEFAULT_HEADERS,
        deadline=deadline,
        timeout=timeout,
    )
    feed = feedparser.parse(res.text)
    if not feed.entries:
        raise ValueError('Google 新闻没有返回任何条目')
    return feed.entries


def _timestamp(entry):
    parsed = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
    if parsed:
        try:
            return calendar.timegm(parsed)
        except Exception:
            pass
    return 0


def _iso_date(entry, timestamp):
    if timestamp:
        return arrow.get(timestamp).isoformat()
    return arrow.now().isoformat()


def parse(entry, keep_source=True):
    raw_title = (getattr(entry, 'title', '') or '').strip()
    source_entry = getattr(entry, 'source', None) or {}
    source = (source_entry.get('title') or '').strip()
    site = (source_entry.get('href') or '').strip()

    title, tail = split_source(raw_title, source)
    if not source:
        source = tail

    link = (getattr(entry, 'link', '') or '').strip()
    guid = (getattr(entry, 'id', '') or getattr(entry, 'guid', '') or '').strip()
    timestamp = _timestamp(entry)

    item = {
        'title': raw_title if keep_source else title,
        'description': '',
        'link': link,
        'guid': guid,
        'pubDate': _iso_date(entry, timestamp),
        'author': source,
        'source': source,
        'site': site,
        '_title_key': normalize_title(title),
        '_ts': timestamp,
    }
    shown = escape(item['title'])
    meta = ' · '.join([part for part in (source, site) if part])
    item['description'] = '<a href="%s" target="_blank">%s</a><br/><font color="#6f6f6f">%s</font>' % (
        escape(link, quote=True),
        shown,
        escape(meta),
    )
    return item


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def empty_ctx(title, query, message):
    return {
        'title': title,
        'link': '%s?q=%s' % (SEARCH_ENDPOINT, query),
        'description': message,
        'author': 'Google News',
        'items': [],
    }


def ctx(keyword='', site='', intitle=True, exclude='', when='',
        hl=DEFAULT_HL, gl=DEFAULT_GL, ceid='', dedup='title', similar=0.0,
        keep_source=True, sort=True):
    """构造 Google 新闻搜索的 RSS 上下文。

    :param keyword: 关键词，多个用 | 或 , 分隔
    :param site: 限定站点，多个用 | 或 , 分隔
    :param intitle: 关键词是否只匹配标题
    :param exclude: 排除词，多个用 | 或 , 分隔
    :param when: 时间范围，如 24h / 7d / 1m
    :param hl: 界面语言，如 zh-CN / en-US
    :param gl: 地区，如 CN / US
    :param ceid: 语种地区标识，留空则由 gl + hl 推导
    :param dedup: 排重策略 title / title+source / guid / link / none
    :param similar: 近似标题合并阈值 0~1；默认 0 关闭，需要时如 0.9
    :param keep_source: 标题是否保留「 - 来源」后缀
    :param sort: 是否按发布时间倒序输出
    """
    try:
        query = build_query(split_terms(keyword), split_terms(site),
                            intitle, split_terms(exclude), when)
    except ValueError as e:
        return empty_ctx('Google 新闻', '', str(e))

    hl = str(hl or DEFAULT_HL)
    gl = str(gl or DEFAULT_GL)
    ceid = str(ceid or '').strip() or build_ceid(gl, hl)
    params = {'q': query, 'hl': hl, 'gl': gl, 'ceid': ceid}

    try:
        similar = float(similar)
    except (TypeError, ValueError):
        similar = 0.0
    similar = max(0.0, min(1.0, similar))

    try:
        entries = fetch_feed(params)
    except Exception as e:
        print('[Google News Error] %s' % e)
        return empty_ctx(query, query, '抓取 Google 新闻失败：%s' % e)

    items = [parse(entry, keep_source) for entry in entries]
    items = [item for item in items if item['link']]
    total = len(items)

    strategy = normalize_dedup(dedup)
    if strategy != 'none' and similar > 0 and strategy == 'title':
        # 先精确后近似，便于在描述里说明各自去掉多少
        exact = dedup_items(items, dedup, similar=0.0)
        exact_count = len(exact)
        final = _fuzzy_dedup(exact, similar)
        extra = '，其中相似标题(≥%.2f)再合并 %d 条' % (similar, exact_count - len(final))
    else:
        final = dedup_items(items, dedup, similar)
        extra = ''

    if sort:
        final.sort(key=lambda item: item['_ts'], reverse=True)
    for item in final:
        item.pop('_ts', None)
        item.pop('_title_key', None)

    return {
        'title': '%s - Google 新闻' % query,
        'link': '%s?%s' % (SEARCH_ENDPOINT, urlencode(params)),
        'description': 'Google 新闻搜索「%s」，原始 %d 条，排重后 %d 条（策略：%s%s）。'
                       % (query, total, len(final), strategy, extra),
        'author': 'Google News',
        'items': final,
    }
