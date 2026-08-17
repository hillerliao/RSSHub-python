import re
import arrow
import requests
from rsshub.utils import DEFAULT_HEADERS

# 金十数据(www.jin10.com) 市场快讯
# 全部快讯: https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=1
# 分类快讯: https://4a735ea38f8146198dc205d2e2d1bd28.z3c.jin10.com/flash?channel=-8200&vip=1&classify=[id]

REQUEST_TIMEOUT = 8
PAGE_LIMIT = 50  # 接口默认返回 50 条

INDEX_URL = 'https://flash-api.jin10.com/get_flash_list'
CATEGORY_URL = 'https://4a735ea38f8146198dc205d2e2d1bd28.z3c.jin10.com/flash'
SOURCE_URL = 'https://www.jin10.com/'

# 金十数据分类: id -> 名称 (参考 RSSHub jin10/category 路由)
CATEGORIES = {
    '1': '贵金属', '2': '黄金', '3': '白银', '4': '钯金', '5': '铂金',
    '6': '石油', '7': 'WTI 原油', '8': '布伦特原油', '9': '欧佩克', '10': '页岩气',
    '11': '原油市场报告', '12': '外汇', '13': '欧元', '14': '英镑', '15': '日元',
    '16': '美元', '17': '瑞郎', '18': '人民币', '36': '期货', '145': '油脂油料',
    '146': '钢矿', '147': '煤炭', '148': '化工', '149': '有色', '150': '谷物',
    '151': '糖棉果蛋', '152': '生猪', '154': '碳排放', '19': '数字货币', '107': '数字人民币',
    '22': '科技', '23': '手机', '39': '电动汽车', '40': '芯片', '41': '中国突破',
    '42': '5G', '43': '量子计算', '158': '航空航天', '165': '元宇宙', '168': '人工智能',
    '24': '地缘局势', '44': '缅甸局势', '45': '印巴纷争', '46': '中东风云', '155': '阿富汗局势',
    '167': '俄乌冲突', '25': '人物', '47': '鲍威尔', '48': '马斯克', '49': '拉加德',
    '50': '特朗普', '51': '拜登', '157': '巴菲特', '26': '央行', '53': '美联储',
    '54': '中国央行', '55': '欧洲央行', '56': '日本央行', '137': '货币政策调整', '141': '英国央行',
    '159': '澳洲联储', '160': '新西兰联储', '161': '加拿大央行', '27': '美股', '59': '财报',
    '60': 'Reddit 散户动态', '108': '个股动态', '28': '港股', '61': '美股回港', '62': '交易所动态',
    '63': '指数动态', '109': '个股动态', '29': 'A 股', '64': '美股回 A', '65': '券商分析',
    '66': '板块异动', '67': '大盘动态', '68': '南北资金', '69': '亚盘动态', '70': 'IPO 信息',
    '110': '个股动态', '166': '北交所', '30': '基金', '31': '投行机构', '71': '标普、惠誉、穆迪',
    '72': '美银', '112': '高盛', '32': '疫情', '73': '疫苗动态', '74': '确诊数据',
    '113': '新冠药物', '33': '债券', '34': '政策', '75': '中国', '76': '美国',
    '77': '欧盟', '78': '日本', '79': '贸易、关税', '80': '碳中和', '81': '中国香港',
    '120': '英国', '156': '房地产动态', '35': '经济数据', '82': '中国', '83': '美国',
    '84': '欧盟', '85': '日本', '37': '公司', '86': '特斯拉', '90': '苹果',
    '91': '独角兽', '92': '谷歌', '93': '华为', '94': '阿里巴巴', '95': '小米',
    '116': '字节跳动', '117': '腾讯', '118': '微软', '119': '百度', '162': '美团',
    '163': '滴滴', '164': '中国恒大', '38': '灾害事故', '96': '地震', '97': '爆炸',
    '98': '海啸', '99': '寒潮', '100': '洪涝', '101': '火灾', '102': '矿难',
    '103': '枪击案',
}

# 名称 -> id 反向映射 (重复名称保留第一个)
_NAME_TO_ID = {}
for _id, _name in CATEGORIES.items():
    _NAME_TO_ID.setdefault(_name, _id)


def fetch_flash(category_id=''):
    """获取快讯列表, category_id 为空时返回全部快讯"""
    if category_id:
        url = CATEGORY_URL
        params = {'channel': '-8200', 'vip': '1', 'classify': f'[{category_id}]'}
        version = '1.0'
    else:
        url = INDEX_URL
        params = {'channel': '-8200', 'vip': '1'}
        version = '1.0.0'

    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Referer': SOURCE_URL,
        'Origin': 'https://www.jin10.com',
        'x-app-id': 'bVBF4FyRTn5NJF5n',
        'x-version': version,
    })
    res = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    data = res.json().get('data') or []
    # 过滤掉付费/置顶类(type=1)条目
    return [x for x in data if x.get('type') != 1]


def parse(post):
    item = {}
    data = post.get('data') or {}
    content = data.get('content') or ''

    # 标题: 优先取内容开头的 【...】
    m = re.match(r'^【(.*?)】', content)
    if m:
        title = m.group(1)
        content = content[m.end():]
    else:
        title = data.get('vip_title') or content

    item['title'] = title
    description = content
    pic = data.get('pic') or ''
    if pic:
        description = f'{description}<br><img src="{pic}">'
    item['description'] = description
    item['link'] = data.get('link') or ''
    item['author'] = '金十数据'
    time_str = post.get('time') or ''
    try:
        # 接口 time 为北京时间字符串
        item['pubDate'] = arrow.get(time_str, 'YYYY-MM-DD HH:mm:ss').replace(tzinfo='+08:00').isoformat()
    except (ValueError, TypeError):
        item['pubDate'] = arrow.now().isoformat()
    return item


def ctx(category='', important=''):
    category = (category or '').strip()
    important = bool(important)

    # 支持分类 id 与中文名称
    category_id = ''
    if category:
        if category in CATEGORIES:
            category_id = category
        elif category in _NAME_TO_ID:
            category_id = _NAME_TO_ID[category]
        else:
            # 未知分类回退为全部
            category_id = ''
            print(f'[jin10/kuaixun] Unknown category: {category}')

    try:
        posts = fetch_flash(category_id)
    except Exception as e:
        print(f'[jin10/kuaixun] Fetch failed: {e}')
        posts = []

    if important:
        posts = [x for x in posts if x.get('important')]

    items = []
    for post in posts[:PAGE_LIMIT]:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f'[jin10/kuaixun] Skipping bad item: {e}')

    if category_id:
        name = CATEGORIES.get(category_id, category)
        title = f'{name} - 金十数据'
        link = SOURCE_URL
        description = f'金十数据 - {name} 分类快讯'
    else:
        title = '金十数据 市场快讯'
        link = SOURCE_URL
        description = '金十数据 7x24 小时全球快讯'
    if important:
        title = f'重要 - {title}'
        description = f'{description}(仅重要快讯)'

    if not items:
        description += ' (数据获取失败或暂无内容)'

    return {
        'title': title,
        'link': link,
        'description': description,
        'author': 'hillerliao',
        'items': items,
    }
