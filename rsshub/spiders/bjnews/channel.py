import time
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from rsshub.utils import fetch_with_deadline

domain = 'https://www.bjnews.com.cn'
m_domain = 'https://m.bjnews.com.cn'

# 总抓取预算(秒):尽量贴近 Vercel 10s 上限但留出冷启动/渲染余量。
#
# 线上实测结论(2026-09-07, Vercel 函数区域 hkg1):
#   - www.bjnews.com.cn 直连几乎恒定黑洞(8s TCP 无响应)。
#   - m.bjnews.com.cn JSON 接口是"间歇黑洞":Vercel 出口 IP 池中部分被封锁,
#     部分可通;单请求成功概率约 1/3~1/2,失败是 2.2s 秒超时。
# 因此策略:desktop 快速试探一次(1.5s),随后把剩余预算全部押在 m 站 API 上
# 多轮重试(每轮独立出口连接,撞中可用 IP 即成功)。
# 另加模块级 last-good:同实例进程内若此前成功过,连续黑洞时返回最近一次
# 成功结果,避免 SWR 冷缓存窗口内直接 500。
REQUEST_BUDGET = 8.0
DESKTOP_SLICE = 1.5  # www 已基本全黑洞,给短预算止损
MAPI_SLICE = 2.2     # m 站 API 单轮预算;黑洞 2.2s 秒超时,成功多在 1~3s
MAPI_ATTEMPTS = 3    # 并发竞速,避免串行重试耗尽 Vercel 函数预算
LAST_GOOD_TTL = 6 * 3600  # last-good 兜底最大时长(秒)
FETCH_RETRIES = 1       # 整轮抓取失败后立即再试一次
LAST_GOOD_TTL = 6 * 3600  # last-good 兜底最大时长(秒)
TOTAL_BUDGET = 10.0       # 两次抓取总共允许的墙钟秒数

# 频道元信息:category -> (m站 channel_id, 中文名)
# m站接口 /bwnew/index-tj 需要 channel_id;名称用于 API 兜底时的 feed 标题。
CHANNELS = {
    'video': (90, '视频'),
    'depth': (97, '深读'),
    'gongyi': (10022, '公益'),
    'diyikandian': (10010, '第一看点'),
    'news': (101, '时事'),
    'beijing': (4, '北京'),
    'guoji': (10008, '国际'),
    'zhengshi': (10016, '政事儿'),
    'point': (5, '观点'),
    'industrial': (92, '消费'),
    'entertainment': (8, '娱乐'),
    'culture': (7, '文化'),
    'sports': (9, '体育'),
    'education': (12, '京彩教育'),
    'financial': (6, '浪花资本'),
    'technology': (16, '藻知科技'),
    'kunlunzhiku': (10053, '鲲纶智库'),
    'car': (10, '潮流智造局'),
    'estate': (11, '城市好望角'),
    'shenghuoshe': (10052, '海星生活社'),
    'photo': (14, '图说'),
    'thinktank': (94, '智库'),
    'shuju': (10011, '数据'),
    'country': (93, '乡村'),
    'beikecaijingapp': (10047, '贝壳财经客户端'),
}


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _m_channel(category):
    """(channel_id, 中文名);未知频道 id 返回 None。"""
    meta = CHANNELS.get(category)
    return (meta if meta else (None, category))


def parse_desktop(res):
    """解析桌面站瀑布流列表,返回 item 列表。"""
    tree = BeautifulSoup(res.text, 'html.parser')
    posts = tree.select('#waterfall-container .pin_demo > a')
    if not posts:
        raise ValueError('解析为空(页面结构可能已变更)')

    def parse(post):
        item = {}
        text = _clean(post.get_text())
        item['description'] = item['title'] = text
        item['link'] = post['href']
        return item

    return list(map(parse, posts))


def parse_mapi(res):
    """解析 m站 JSON 列表接口,返回 item 列表。"""
    payload = res.json()
    if not (isinstance(payload, dict) and str(payload.get('status')) == '1'
            and payload.get('info') == 'ok'):
        raise ValueError(f'm站接口返回异常: {str(payload)[:100]}')
    items = []
    for d in payload.get('data') or []:
        title = _clean(d.get('title', ''))
        if not title:
            continue
        du = d.get('detail_url') or {}
        link = du.get('pc_url') or du.get('m_url')
        if not link:
            uuid = d.get('uuid')
            if not uuid:
                continue
            link = f'{domain}/detail/{uuid}.html'
        item = {'title': title, 'description': title, 'link': link}
        try:
            pt = d.get('publish_time')
            dt = datetime.strptime(pt, '%Y-%m-%d %H:%M:%S')
            dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            item['pubDate'] = dt.isoformat()
        except Exception:
            pass
        items.append(item)
    if not items:
        raise ValueError('m站接口未返回有效条目')
    return items


# 模块级 last-good:key=category -> (items, ts)。进程存活期内跨请求兜底黑洞。
_LAST_GOOD = {}


def _last_good(category):
    rec = _LAST_GOOD.get(category)
    if not rec:
        return None
    items, ts = rec
    if time.time() - ts > LAST_GOOD_TTL:
        return None
    return items


def _save_good(category, items):
    _LAST_GOOD[category] = (items, time.time())


def _fetch_once(category, budget=REQUEST_BUDGET):
    """预算内抓取:www 桌面站快速试探 → m站 JSON 接口多轮重试。

    全部失败:若同进程此前成功过且未过期,返回 last-good 避免 500;否则抛异常
    (不吞错,防止坏数据进 SWR 缓存)。
    """
    start = time.time()
    errors = []
    r_url = f'{domain}/{category}'
    channel_id, channel_name = _m_channel(category)
    api_url = None

    def _ok(source, items):
        _save_good(category, items)
        print(f'[bjnews] {category}: 源 {source} 成功 '
              f'({time.time() - start:.1f}s, {len(items)} 条)')
        return items, channel_name, r_url

    # 未知频道:先以短请求探测 m 页里隐藏的 channel_id(供 m 站接口使用)
    if channel_id is None:
        try:
            page = fetch_with_deadline(f'{m_domain}/{category}',
                                       deadline=1.8, timeout=3.0)
            m = re.search(r"id=['\"]cur_channel_id['\"][^>]*value=['\"](\d+)", page.text)
            if m:
                channel_id = int(m.group(1))
                api_url = (f'{m_domain}/bwnew/index-tj?page=1&size=20'
                           f'&channel_id={channel_id}&wz_id=1')
        except Exception as e:
            errors.append(f'探测channel_id: {e}')
    if channel_id and api_url is None:
        api_url = (f'{m_domain}/bwnew/index-tj?page=1&size=20'
                   f'&channel_id={channel_id}&wz_id=1')

    # ① www 桌面站:仅在放行窗口内可通,短预算止损
    try:
        res = fetch_with_deadline(r_url, deadline=DESKTOP_SLICE,
                                  timeout=DESKTOP_SLICE + 1.0)
        items = parse_desktop(res)
        if not items:
            raise ValueError('桌面站解析为空')
        return _ok('desktop', items)
    except Exception as e:
        errors.append(f'desktop: {e}')
        print(f'[bjnews] {category}: desktop 失败 ({time.time() - start:.1f}s): {e}')

    # ② m站 JSON 接口:间歇黑洞,并发竞速多个独立连接
    if api_url:
        remaining = budget - (time.time() - start)
        if remaining >= 1.4:
            executor = ThreadPoolExecutor(max_workers=MAPI_ATTEMPTS)
            futures = [executor.submit(fetch_with_deadline, api_url,
                                       deadline=min(MAPI_SLICE, remaining),
                                       timeout=min(MAPI_SLICE, remaining) + 1.0)
                       for _ in range(MAPI_ATTEMPTS)]
            try:
                while futures:
                    left = budget - (time.time() - start)
                    if left <= 0:
                        break
                    done, pending = wait(futures, timeout=left,
                                         return_when=FIRST_COMPLETED)
                    if not done:
                        break
                    futures = list(pending)
                    for future in done:
                        rnd = MAPI_ATTEMPTS - len(futures)
                        try:
                            items = parse_mapi(future.result())
                            if not items:
                                raise ValueError('m站接口解析为空')
                            return _ok(f'mapi竞速({rnd}号)', items)
                        except Exception as e:
                            errors.append(f'mapi竞速: {e}')
                            print(f'[bjnews] {category}: mapi竞速失败 '
                                  f'({time.time() - start:.1f}s): {e}')
            finally:
                # 请求线程由 fetch_with_deadline 设为 daemon,不让清理阻塞响应。
                executor.shutdown(wait=False, cancel_futures=True)

    raise RuntimeError(f'新京报「{category}」抓取失败: ' + ' | '.join(errors))


def _fetch(category):
    """整轮抓取失败后立即重试一次;失败结果不进入缓存。"""
    errors = []
    attempt_budget = TOTAL_BUDGET / (FETCH_RETRIES + 1)
    for attempt in range(1, FETCH_RETRIES + 2):
        try:
            return _fetch_once(category, budget=attempt_budget)
        except Exception as e:
            errors.append(f'第{attempt}轮: {e}')
            if attempt <= FETCH_RETRIES:
                print(f'[bjnews] {category}: 第{attempt}轮失败, 立即重试: {e}')
    stale = _last_good(category)
    if stale:
        channel_name = _m_channel(category)[1]
        print(f'[bjnews] {category}: 重试仍失败,返回 last-good ({len(stale)} 条)')
        return stale, channel_name, f'{domain}/{category}'
    raise RuntimeError(f'新京报「{category}」抓取失败: ' + ' | '.join(errors))


def ctx(category=''):
    items, channel_name, r_url = _fetch(category)
    return {
        'title': f'{channel_name} - 新京报',
        'link': r_url,
        'description': f'新京报「{channel_name}」频道新闻',
        'author': 'hillerliao',
        'items': items,
    }
