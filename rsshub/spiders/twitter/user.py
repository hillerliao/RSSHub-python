# -*- coding: utf-8 -*-
"""Twitter / X 用户 RSS（通过 Google News RSS 搜索，无需登录 cookie）。

核心思路：把 ``site:x.com/<username>`` 当成查询词，
丢给 Google News 的 RSS 端点 ``https://news.google.com/rss/search``，
让已被 Google News 索引的推文直接以 RSS 形式返回。

为什么能这样干
=============

Google News 的 RSS 端点（区别于 google.com/search HTML）：

- 直接返回 XML，**无需 JS 渲染**，普通 requests 就能拿到
- 不强制登录、不要求 cookie、无频率审计
- 复用了项目里 ``google/news.py`` 的底层（feedparser 解析、entry 抽取）

**关键坑：地区桶**
------------------

实测发现 Google News 的 ``ceid`` / ``hl`` / ``gl`` 三元组决定返回哪份索引。
同一个查询，桶不同结果天差地别：

- 中文内容账号（如 wangwatchworld）：
  ``ceid=CN:zh-Hans`` 拿 100 条最新推文，``ceid=US:en`` 只有几个月前的 6 条
- 英文内容账号（如 elonmusk）：
  ``ceid=US:en`` 拿 100 条最新推文，``ceid=CN:zh-Hans`` 滞后严重

所以默认同时查两个桶再合并去重，规避单边索引滞后。

代价与局限
==========

- 实时性受 Google News 索引速度制约：**中文桶通常 0–7 天延迟，
  英文桶可接近实时**（取决于账号内容语种）
- 不被 Google News 收录的推文（如被作者删除、账号受限）抓不到
- 链接形式：entry 里偶尔会露出真实的 ``x.com/.../status/...``，
  本 spider 会把它提到 link 字段；其余仍是 ``news.google.com/rss/articles/CBMi...`` 跳转

为什么不用 ``google/news.py.ctx`` 而是直接调底层
==============================================

``ctx`` 会用 ``(site:x.com/<username>)`` 形式构造 query（包一层括号），
这个写法 Google News 不认，返回空；直接传裸 ``site:x.com/<username>`` 才有效。
所以这里绕开 ``build_query``，自己拼参数，HTTP 抓取和 entry 解析仍然
复用 ``fetch_feed`` 和 ``parse``。

路由与参数
==========

``/x/<username>``，可选参数：

- ``when``  时间窗 ``24h`` / ``7d`` / ``30d``（默认 ``7d``）
- ``editions`` 用哪几个桶，逗号分隔，默认 ``cn,us``（双桶合并）
  可选值：``cn`` / ``us`` / ``gb`` / ``jp`` / ``tw``
- ``limit`` 最多返回多少条，默认 30

示例：

- ``/x/elonmusk?editions=us`` —— 强制只用 US 桶
- ``/x/wangwatchworld`` —— 默认 cn+us 双桶，中文桶新鲜时优先
"""

import re
from html import escape
from urllib.parse import unquote, urlencode

from rsshub.spiders.google.news import (
    DEFAULT_HEADERS,
    FETCH_DEADLINE,
    FETCH_TIMEOUT,
    fetch_feed,
    parse as gnews_parse,
)

# x.com 链接（不含 www.）出现在标题里时，把它提到 link 字段
_X_URL_RE = re.compile(
    r'https?://(?:www\.)?(?:twitter|x)\.com/[A-Za-z0-9_./?=&%-]+',
    re.IGNORECASE,
)

_WHEN_RE = re.compile(r'^(\d+)([hdwmy])$')
_WHEN_UNITS = {'h': 'hours', 'd': 'days', 'w': 'weeks', 'm': 'months', 'y': 'years'}

# 不同地区桶：(hl, gl, ceid) 三元组
EDITION_PRESETS = {
    'cn': ('zh-CN', 'CN', 'CN:zh-Hans'),    # 中文桶
    'us': ('en-US', 'US', 'US:en'),         # 美/英桶（默认实时性最好）
    'gb': ('en-GB', 'GB', 'GB:en'),         # 英桶（与 us 高度重叠，保留备用）
    'jp': ('ja',    'JP', 'JP:ja'),
    'tw': ('zh-TW', 'TW', 'TW:zh-Hant'),
}


def _promote_real_url(item):
    """如果标题里藏着 x.com 链接，把它当 link；标题里清掉 URL 和源名后缀。

    Google News 的 entry 标题偶尔是 ``https://x.com/i/status/123 - x.com``
    这种「permalink tweet」——真实推文 URL 在标题里，而 entry.link 是
    ``news.google.com/rss/articles/CBMi...`` 跳转。本函数把真实 URL 提到
    ``item['link']`` 和 ``item['guid']``，同时清理标题。

    如果清完只剩源域名（典型 permalink 推文），给个兜底标题，避免空标题。
    """
    raw_title = item.get('title', '') or ''
    cleaned = re.sub(r'\s*[-–—|·｜・]\s*x\.com\s*$', '', raw_title).strip()
    match = _X_URL_RE.search(cleaned)
    real_url = None
    if match:
        real_url = match.group(0).rstrip('.,;:)]')
        cleaned = (cleaned[:match.start()] + cleaned[match.end():]).strip(' -–—|·')
    if not cleaned:
        cleaned = '查看推文原文'
    item['title'] = cleaned
    if real_url:
        item['link'] = real_url
        item['guid'] = real_url
    return item


def _query_edition(username, edition_key, when):
    """对单个桶发起一次 Google News 查询，返回 entries 列表。"""
    hl, gl, ceid = EDITION_PRESETS[edition_key]
    params = {
        'q': 'site:x.com/%s' % username,
        'hl': hl,
        'gl': gl,
        'ceid': ceid,
    }
    if when:
        params['tbs'] = 'qdr:%s' % when
    try:
        entries = fetch_feed(params, deadline=FETCH_DEADLINE, timeout=FETCH_TIMEOUT)
        return edition_key, entries, None
    except Exception as e:
        return edition_key, [], str(e)


def _empty_ctx(username, message):
    return {
        'title': '@%s - Twitter (via Google News)' % username,
        'link': 'https://x.com/%s' % username if username else 'https://x.com',
        'description': message,
        'author': 'Google News',
        'items': [],
    }


def ctx(username='', when='7d', editions='cn,us', limit=30, auto=False):
    """构造 Twitter 用户时间线的 RSS 上下文。

    :param username: Twitter / X 用户名（不含 ``@``），1–15 位
    :param when: 时间窗 ``24h`` / ``7d`` / ``30d``，默认 ``7d``
    :param editions: 逗号分隔的桶列表，默认 ``cn,us``
                     可选：cn / us / gb / jp / tw
    :param limit: 最多返回多少条
    :param auto: 自动选桶 —— 把请求的桶都查一遍,选「返回最新推文」的桶。
                 用户不用关心账号是中文还是英文,代价是多 N 倍请求。
    """
    username = unquote(str(username or '')).strip().lstrip('@')
    if not re.match(r'^[A-Za-z0-9_]{1,15}$', username):
        return _empty_ctx('', '用户名不合法（需 1–15 位字母数字下划线）。')

    when = str(when or '').strip().lower()
    if when and not _WHEN_RE.match(when):
        when = ''

    # 解析 editions 参数
    requested = []
    for token in str(editions or 'cn,us').split(','):
        key = token.strip().lower()
        if key in EDITION_PRESETS and key not in requested:
            requested.append(key)
    if not requested:
        requested = ['cn', 'us']

    # 顺序查询每个桶（并发会更复杂，对小量端点串行足够）
    hits = {}          # dedup_key -> item
    edition_stats = []
    per_edition = {}   # key -> (entries_count, newest_pubDate_str)

    for key in requested:
        edition_key, entries, err = _query_edition(username, key, when)
        if err:
            print('[Twitter/Google News] edition=%s err: %s' % (key, err))
            edition_stats.append('%s=失败' % key)
            continue
        edition_stats.append('%s=%d' % (key, len(entries)))
        # 记录该桶的最早条目时间戳,用于 auto 选桶
        newest = ''
        for entry in entries:
            ts = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
            if ts:
                import calendar as _cal
                import arrow as _arrow
                iso = _arrow.get(_cal.timegm(ts)).isoformat()
                if iso > newest:
                    newest = iso
        per_edition[key] = (len(entries), newest)
        for entry in entries:
            item = gnews_parse(entry, keep_source=True)
            _promote_real_url(item)
            dedup_key = item.get('link') or item.get('guid') or id(item)
            if dedup_key and dedup_key not in hits:
                hits[dedup_key] = item

    # auto 模式:挑出「返回最新推文」的桶,只用那一桶的结果
    chosen_edition = None
    if auto and per_edition:
        best_key = max(per_edition.keys(),
                       key=lambda k: (per_edition[k][1], per_edition[k][0]))
        chosen_edition = best_key
        # 只保留 best_key 桶的条目
        # 找出 best_key 桶 entry 的 link 集合
        _, best_entries, _ = _query_edition(username, best_key, when)
        best_keys = set()
        for entry in best_entries:
            tmp = gnews_parse(entry, keep_source=True)
            _promote_real_url(tmp)
            k = tmp.get('link') or tmp.get('guid')
            if k:
                best_keys.add(k)
        hits = {k: v for k, v in hits.items() if k in best_keys}

    items = list(hits.values())
    items.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    if limit and len(items) > limit:
        items = items[:limit]

    if not items:
        return _empty_ctx(username,
            'Google News 各桶（%s）都没有返回 %s 的结果。可能：账号不存在、内容未被'
            'Google News 索引、或该账号近期无活动。' % (','.join(requested), username))

    return {
        'title': '@%s - Twitter (via Google News)' % username,
        'link': 'https://x.com/%s' % username,
        'description': (
            '通过 Google News RSS 端点查询 site:x.com/%s（when=%s），'
            '桶：%s%s；共 %d 条。无需 X 登录、无封号风险；'
            '延迟取决于 Google News 各桶索引速度。'
        ) % (
            username, when or 'all',
            ','.join(edition_stats),
            '，auto 选中 %s' % chosen_edition if chosen_edition else '',
            len(items),
        ),
        'author': 'Google News',
        'items': items,
    }
