import re
from datetime import datetime, timezone
from rsshub.utils import fetch_with_deadline

domain = 'https://www.zhitongcaijing.com'

# 抓取预算(秒):JSON 接口通常 0.5~2s 返回,留足冷启动余量即可。
REQUEST_BUDGET = 5.0
# 列表 API 默认每页大小,与站点保持一致;limit 用于按需裁剪结果。
PAGE_SIZE = 10


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _abs_url(href):
    """把站内相对链接补全为 https 绝对链接。"""
    href = (href or '').strip()
    if not href:
        return ''
    if href.startswith('http'):
        return href
    if href.startswith('//'):
        return 'https:' + href
    return domain + href if href.startswith('/') else href


def _parse_pub_date(create_time):
    """API 返回的 create_time 是 Unix 秒级时间戳。"""
    try:
        dt = datetime.fromtimestamp(int(create_time), tz=timezone.utc)
        # 转北京时区(UTC+8)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ''


def _parse_item(d):
    """解析单条 JSON 记录,返回 item dict(或 None)。"""
    title = _clean(d.get('title', ''))
    link = _abs_url(d.get('url', ''))
    if not title or not link:
        return None

    digest = _clean(d.get('digest', ''))
    image = _abs_url(d.get('image', ''))

    desc_parts = []
    if image:
        desc_parts.append(f'<p><img src="{image}"/></p>')
    if digest and digest != title:
        desc_parts.append(f'<p>{digest}</p>')
    else:
        desc_parts.append(f'<p>{title}</p>')
    description = ''.join(desc_parts)

    item = {
        'title': title,
        'link': link,
        'description': description,
    }
    pub = _parse_pub_date(d.get('create_time'))
    if pub:
        item['pubDate'] = pub
    return item


def _fetch_page(author_id, page):
    """抓取单页 JSON 列表,返回解析后的 item 列表。"""
    api_url = (f'{domain}/column/detail.html?data_type=1'
               f'&id={author_id}&page={page}')
    res = fetch_with_deadline(api_url, deadline=REQUEST_BUDGET,
                              timeout=REQUEST_BUDGET + 1.0)
    payload = res.json()
    if not isinstance(payload, dict) or payload.get('status') != 'success':
        raise ValueError(f'智通财经专栏接口异常: {str(payload)[:120]}')

    items = []
    seen = set()
    for d in payload.get('data') or []:
        item = _parse_item(d)
        if not item or item['link'] in seen:
            continue
        seen.add(item['link'])
        items.append(item)
    return items


def _extract_column_name(html):
    """从作者页 <title> 中切出专栏名。

    服务端 HTML 里的 <title> 形如 "专栏-智通财经网-智通数据",最后一段就是
    专栏显示名;取不到时回落到 None。
    """
    if not html:
        return None
    m = re.search(r'<title>\s*([^<]+?)\s*</title>', html)
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split('－')] if '－' in m.group(1) \
        else [p.strip() for p in m.group(1).split('-')]
    if len(parts) >= 2 and parts[-1]:
        return parts[-1]
    return None


def ctx(author_id='85', limit=PAGE_SIZE, name=''):
    author_id = str(author_id).strip() or '85'
    page_url = f'{domain}/author/profile/{author_id}.html'

    # 只取第一页,避免 Vercel 函数预算被多页叠加耗尽
    items = _fetch_page(author_id, page=1)

    if limit and limit > 0:
        items = items[:limit]

    if not items:
        raise RuntimeError(f'智通财经专栏 {author_id} 解析为空(页面结构可能已变更)')

    # 展示名优先级:?name= > 作者页 <title> 切出来的专栏名 > '专栏 #<id>'
    display_name = (name or '').strip()
    if not display_name:
        try:
            res = fetch_with_deadline(page_url, deadline=REQUEST_BUDGET,
                                      timeout=REQUEST_BUDGET + 1.0)
            display_name = _extract_column_name(res.text) or ''
        except Exception:
            display_name = ''

    if display_name:
        feed_title = f'智通财经 - {display_name}'
        feed_desc = f'智通财经专栏「{display_name}」(#{author_id}) 的最新文章'
    else:
        feed_title = f'智通财经 - 专栏 #{author_id}'
        feed_desc = f'智通财经作者/专栏 #{author_id} 的最新文章'

    return {
        'title': feed_title,
        'link': page_url,
        'description': feed_desc,
        'author': 'hillerliao',
        'items': items,
    }
