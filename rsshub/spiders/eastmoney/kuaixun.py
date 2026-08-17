import requests
import json
import arrow
from rsshub.utils import DEFAULT_HEADERS

# 东方财富 7x24 快讯分类
# key: 路由分类参数 | (column 列表, 分类中文名, 分类页面)
CATEGORIES = {
    'all': ('102', '7x24全球直播', 'https://kuaixun.eastmoney.com/'),
    'focus': ('101', '焦点', 'https://kuaixun.eastmoney.com/yw.html'),
    'zhibo': ('zhiboall', '股市直播', 'https://kuaixun.eastmoney.com/zhibo.html'),
    'company': ('103', '上市公司', 'https://kuaixun.eastmoney.com/ssgs.html'),
    'region': ('110,111,112,113,114,115,116,117', '地区', 'https://kuaixun.eastmoney.com/dq.html'),
    'us': ('111', '美国', 'https://kuaixun.eastmoney.com/dq_mg.html'),
    'eurozone': ('112', '欧元区', 'https://kuaixun.eastmoney.com/dq_oyq.html'),
    'uk': ('113', '英国', 'https://kuaixun.eastmoney.com/dq_yg.html'),
    'japan': ('114', '日本', 'https://kuaixun.eastmoney.com/dq_rb.html'),
    'canada': ('115', '加拿大', 'https://kuaixun.eastmoney.com/dq_jnd.html'),
    'australia': ('116', '澳洲', 'https://kuaixun.eastmoney.com/dq_oz.html'),
    'emerging': ('117', '新兴市场', 'https://kuaixun.eastmoney.com/dq_xxsc.html'),
    'centralbank': ('118,119,120,121,122,123,124', '全球央行', 'https://kuaixun.eastmoney.com/qqyh.html'),
    'fed': ('119', '美联储', 'https://kuaixun.eastmoney.com/qqyh_mlc.html'),
    'ecb': ('120', '欧洲央行', 'https://kuaixun.eastmoney.com/qqyh_ozyh.html'),
    'boe': ('121', '英国央行', 'https://kuaixun.eastmoney.com/qqyh_ygyh.html'),
    'boj': ('122', '日本央行', 'https://kuaixun.eastmoney.com/qqyh_rbyh.html'),
    'boc': ('123', '加拿大央行', 'https://kuaixun.eastmoney.com/qqyh_jndyh.html'),
    'rba': ('124', '澳洲联储', 'https://kuaixun.eastmoney.com/qqyh_ozlc.html'),
    'economydata': ('125,126,127,128,129,130,131', '经济数据', 'https://kuaixun.eastmoney.com/jjsj.html'),
    'usdata': ('126', '美国数据', 'https://kuaixun.eastmoney.com/jjsj_mgsj.html'),
    'eurozonedata': ('127', '欧元区数据', 'https://kuaixun.eastmoney.com/jjsj_oyqsj.html'),
    'ukdata': ('128', '英国数据', 'https://kuaixun.eastmoney.com/jjsj_ygsj.html'),
    'japandata': ('129', '日本数据', 'https://kuaixun.eastmoney.com/jjsj_rbsj.html'),
    'canadadata': ('130', '加拿大数据', 'https://kuaixun.eastmoney.com/jjsj_jndsj.html'),
    'ausdata': ('131', '澳洲数据', 'https://kuaixun.eastmoney.com/jjsj_ozsj.html'),
    'stock': ('105', '全球股市', 'https://kuaixun.eastmoney.com/qqgs.html'),
    'commodity': ('106', '商品', 'https://kuaixun.eastmoney.com/sp.html'),
    'fx': ('107', '外汇', 'https://kuaixun.eastmoney.com/wh.html'),
    'bond': ('108', '债券', 'https://kuaixun.eastmoney.com/zq.html'),
    'fund': ('109', '基金', 'https://kuaixun.eastmoney.com/jj.html'),
}

# 接口超时(避免上游慢导致网关 504)
REQUEST_TIMEOUT = 8
PAGE_SIZE = 50

API_BASE = 'https://newsapi.eastmoney.com/kuaixun/v1/getlist_{column}_ajaxResult_{page_size}_{page_no}_.html'


def fetch_column(column, page_size=PAGE_SIZE, page_no=1):
    """获取指定 column 的快讯列表,返回 LivesList"""
    url = API_BASE.format(column=column, page_size=page_size, page_no=page_no)
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Referer': 'https://kuaixun.eastmoney.com/',
        'Accept': 'application/json, text/plain, */*',
    })
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    # 接口返回 JSONP: var ajaxResult={...}; 提取 JSON 部分
    text = res.text
    start = text.find('{')
    end = text.rfind('}') + 1
    if start == -1 or end == 0:
        return []
    data = json.loads(text[start:end])
    return data.get('LivesList') or []


def parse(post):
    item = {}
    title = post.get('title') or post.get('simtitle') or ''
    digest = post.get('digest') or post.get('simdigest') or title
    item['title'] = title
    item['description'] = digest
    item['link'] = post.get('url_w') or ''
    item['author'] = '东方财富网'
    showtime = post.get('showtime') or post.get('ordertime')
    try:
        item['pubDate'] = arrow.get(showtime, 'YYYY-MM-DD HH:mm:ss').isoformat()
    except (ValueError, TypeError):
        item['pubDate'] = arrow.now().isoformat()
    return item


def ctx(category='all'):
    if category in CATEGORIES:
        columns, name, page = CATEGORIES[category]
    elif category:
        # 支持直接传 column 编号(如 102)或逗号分隔的多个 column
        columns, name, page = category, category, 'https://kuaixun.eastmoney.com/'
    else:
        columns, name, page = CATEGORIES['all']

    posts = []
    seen = set()
    errors = []
    for col in [c for c in columns.split(',') if c]:
        try:
            lives = fetch_column(col)
        except Exception as e:
            errors.append(f'{col}: {e}')
            continue
        for post in lives:
            nid = post.get('id')
            if nid and nid not in seen:
                seen.add(nid)
                posts.append(post)

    # 按发布时间倒序排列(组合分类时多 column 合并)
    posts.sort(key=lambda p: p.get('showtime') or '', reverse=True)
    items = []
    for post in posts[:PAGE_SIZE]:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f"[eastmoney/kuaixun] Skipping bad item: {e}")

    description = f'东方财富 7x24 快讯 - {name}'
    if errors:
        description += f' (部分分类获取失败: {"; ".join(errors)})'

    return {
        'title': f'{name} - 东方财富网快讯',
        'link': page,
        'description': description,
        'author': 'hillerliao',
        'items': items
    }
