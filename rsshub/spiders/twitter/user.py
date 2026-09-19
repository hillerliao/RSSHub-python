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

**关键坑一：地区桶**
--------------------

实测发现 Google News 的 ``ceid`` / ``hl`` / ``gl`` 三元组决定返回哪份索引。
同一个查询，桶不同结果天差地别：

- 中文内容账号（如 wangwatchworld）：
  ``ceid=CN:zh-Hans`` 拿 100 条最新推文，``ceid=US:en`` 只有几个月前的 6 条
- 英文内容账号（如 elonmusk）：
  ``ceid=US:en`` 拿 100 条最新推文，``ceid=CN:zh-Hans`` 滞后严重

所以默认同时查两个桶再合并去重，规避单边索引滞后。

**关键坑二：同一条推文有多个 article id**
----------------------------------------

Google News 会把同一条推文在不同索引分片里重复收录，同一次请求就返回
2~3 条：标题与 pubDate 完全相同，``<id>`` / ``<link>`` 却是
``news.google.com/rss/articles/CBMi...`` 各不相同（实测 wangwatchworld 的
CN 桶 100 条里有 17 条属于这种重复）。所以**按 link/guid 排重等于不去重**，
必须按「归一化标题」比对——正是 ``google/news.py`` 里那套排重的用武之地，
本 spider 直接复用它的 ``dedup_items``。

这些 CBMi ID 是不透明的 ``AU_yqL...`` token（base64 解出来只有 token 本身，
没有原文 URL），不靠 ``batchexecute`` 解不出真实地址，指望不上。

对 permalink 推文（标题里只有 ``x.com/.../status/...`` 链接）要小心：
标题被清成兜底文案后看起来都一样，但排重用的是**清洗前的原始标题**，
不同的 permalink 推文不会因此被误并。

**关键坑三：when 时间窗**
------------------------

``tbs=qdr:7d`` 在 News RSS 上是**空操作**（实测与不带任何时间参数返回
逐条相同），时间窗得写成查询串里的 ``when:7d``。带 when: 时 Google 偶尔
返回空（``google/news.py`` 记录过这类不稳定后端），此时去掉 when: 重查一次，
再用 ``when_window`` 按条目 pubDate 本地过滤。

代价与局限
==========

- 实时性受 Google News 索引速度制约：**中文桶通常 0–7 天延迟，
  英文桶可接近实时**（取决于账号内容语种）
- 不被 Google News 收录的推文（如被作者删除、账号受限）抓不到
- 链接形式：permalink 推文能拿到真实 ``x.com/.../status/...``，
  其余仍是 ``news.google.com/rss/articles/CBMi...`` 跳转
- 排重按标题：同一作者在窗口内重复发一模一样的文案，会被并成一条

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

import calendar
import re
from urllib.parse import unquote

import arrow

from rsshub.spiders.google.news import (
    FETCH_DEADLINE,
    FETCH_TIMEOUT,
    dedup_items,
    fetch_feed,
    parse as gnews_parse,
    when_window,
)

# x.com 链接（不含 www.）出现在标题里时，把它提到 link 字段
_X_URL_RE = re.compile(
    r'https?://(?:www\.)?(?:twitter|x)\.com/[A-Za-z0-9_./?=&%-]+',
    re.IGNORECASE,
)

_WHEN_RE = re.compile(r'^(\d+)([hdwmy])$')

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


def _entry_ts(entry):
    """entry 的发布时间戳（秒）；拿不到返回 0。"""
    parsed = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
    if not parsed:
        return 0
    try:
        return calendar.timegm(parsed)
    except Exception:
        return 0


def _query_edition(username, edition_key, when):
    """对单个桶发起一次 Google News 查询，返回 (桶名, entries, 错误信息)。"""
    hl, gl, ceid = EDITION_PRESETS[edition_key]
    query = 'site:x.com/%s' % username
    params = {'q': query, 'hl': hl, 'gl': gl, 'ceid': ceid}
    if when:
        params['q'] = '%s when:%s' % (query, when)
    try:
        entries = fetch_feed(params, deadline=FETCH_DEADLINE, timeout=FETCH_TIMEOUT)
        return edition_key, entries, None
    except ValueError as e:
        # 「没返回任何条目」：带 when: 时 Google 偶尔会这样，去掉 when: 重查一次
        # 再本地按 pubDate 过滤，保证时间窗语义不变。
        if not when:
            return edition_key, [], str(e)
        try:
            entries = fetch_feed(dict(params, q=query),
                                 deadline=FETCH_DEADLINE, timeout=FETCH_TIMEOUT)
        except Exception as retry_err:
            return edition_key, [], str(retry_err)
        cutoff = when_window(when)
        if cutoff:
            entries = [entry for entry in entries if _entry_ts(entry) >= cutoff]
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
    :param auto: 自动选桶 —— 把请求的桶都查一遍，只用「最新推文最新鲜」的那桶。
                 用户不用关心账号是中文还是英文，代价是多查几个桶。
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

    # 顺序查询每个桶，条目先进「大池子」，最后统一排重（并发会更复杂，串行足够）
    pool = []
    edition_stats = []
    per_edition = {}   # key -> (条目数, 最新推文时间)，auto 选桶用

    for key in requested:
        edition_key, entries, err = _query_edition(username, key, when)
        if err:
            print('[Twitter/Google News] edition=%s err: %s' % (key, err))
            edition_stats.append('%s=失败' % key)
            continue
        newest = ''
        for entry in entries:
            ts = _entry_ts(entry)
            if ts:
                iso = arrow.get(ts).isoformat()
                if iso > newest:
                    newest = iso
            item = gnews_parse(entry, keep_source=True)
            _promote_real_url(item)
            if not item['_title_key']:
                # 标题为空的坏数据退回 guid，免得它们被当成同一条并掉
                item['_title_key'] = item.get('guid') or item.get('link') or ''
            item['_edition'] = key
            pool.append(item)
        per_edition[key] = (len(entries), newest)
        edition_stats.append('%s=%d' % (key, len(entries)))

    # auto 模式：只留「最新推文最新鲜」的那个桶。选桶在第一轮查询时就顺手记下了，
    # 这里不再重复请求——Vercel 下多打一次 Google 很容易撞上 8s 截止而丢掉全部结果。
    chosen_edition = None
    if auto and per_edition:
        chosen_edition = max(per_edition,
                             key=lambda k: (per_edition[k][1], per_edition[k][0]))
        pool = [item for item in pool if item['_edition'] == chosen_edition]

    raw_total = len(pool)
    items = dedup_items(pool, strategy='title')
    for item in items:
        item.pop('_title_key', None)
        item.pop('_ts', None)
        item.pop('_edition', None)
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
            '桶：%s%s；原始 %d 条，排重后 %d 条'
            '（Google News 会把同一条推文收录成多个不同的 article id，'
            '只能按标题排重）。无需 X 登录、无封号风险；'
            '延迟取决于 Google News 各桶索引速度。'
        ) % (
            username, when or 'all',
            ','.join(edition_stats),
            '，auto 选中 %s' % chosen_edition if chosen_edition else '',
            raw_total, len(items),
        ),
        'author': 'Google News',
        'items': items,
    }
