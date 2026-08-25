import requests
import json
from datetime import datetime, date
from rsshub.utils import DEFAULT_HEADERS


# 东方财富研报类型: qType 0个股 1行业 2策略 3宏观 4券商晨会
# 个股/行业走 report/list 接口; 策略/宏观/晨会走 report/jg 接口; 新股走 report/newStockList 接口
# 个股/新股详情页为 info/{infoCode}.html, 其余为 {link}.jshtml?encodeUrl=...
REPORT_TYPES = {
    'stock': {'qType': '0', 'api': 'list', 'link': 'info'},
    'industry': {'qType': '1', 'api': 'list', 'link': 'zw_industry'},
    'strategyreport': {'qType': '2', 'api': 'jg', 'link': 'zw_strategy'},
    'macresearch': {'qType': '3', 'api': 'jg', 'link': 'zw_macresearch'},
    'brokerreport': {'qType': '4', 'api': 'jg', 'link': 'zw_brokerreport'},
    'newstock': {'qType': '4', 'api': 'newStockList', 'link': 'info'},
}

REPORT_NAMES = {
    'stock': '个股研报',
    'industry': '行业研报',
    'strategyreport': '策略报告',
    'macresearch': '宏观研究',
    'brokerreport': '券商晨会',
    'newstock': '新股研报',
}


def parse(post, link_type='zw_industry'):
    item = {}
    stock_name = post.get('stockName') or ''
    if stock_name != '':
        stock_name = '[' + stock_name + '] '
    title = (stock_name + post.get('title', '')).strip()
    item['title'] = title
    item['description'] = title
    if link_type == 'info':
        item['link'] = f"http://data.eastmoney.com/report/info/{post['infoCode']}.html"
    else:
        item['link'] = f"http://data.eastmoney.com/report/{link_type}.jshtml?encodeUrl={post['encodeUrl']}"
    item['author'] = (post.get('orgSName', '') + ' ' + post.get('researcher', '')).strip()
    item['pubDate'] = post['publishDate']
    return item


def ctx(type='macresearch', category=''):
    if type not in REPORT_TYPES:
        raise ValueError(f'unsupported report type: {type}')
    cfg = REPORT_TYPES[type]
    if cfg['api'] == 'list':
        url = (f'http://reportapi.eastmoney.com/report/list?cb='
               f'&industryCode={category}'
               f'&pageSize=50&industry=*&rating=*&ratingChange=*'
               f'&beginTime=&endTime=&pageNo=1&fields=&qType={cfg["qType"]}'
               f'&orgCode=&rcode=&_=1583647953800')
    else:
        url = (f'http://reportapi.eastmoney.com/report/{cfg["api"]}?cb='
               f'&pageSize=50&beginTime=&endTime=&pageNo=1'
               f'&fields=&qType={cfg["qType"]}')
    res = requests.get(url)
    posts = json.loads(res.text)['data']
    items = list(map(lambda post: parse(post, cfg['link']), posts))
    name = REPORT_NAMES.get(type, type)
    # 带行业代码的个股/行业研报, 用接口返回的行业名称替代数字 id
    # 行业研报(qType=1)行业名在 industryName; 个股研报(qType=0)在 indvInduName
    display = name
    if category:
        for post in posts:
            industry_name = (post.get('industryName') or post.get('indvInduName') or '').strip()
            if industry_name:
                display = f'{industry_name} {name}'
                break
    suffix = f'?hyid={category}' if category else ''
    return {
        'title': f'{display} - 东方财富网',
        'link': f'http://data.eastmoney.com/report/{type}.jshtml{suffix}',
        'description': f'{display} - 东方财富网',
        'author': 'hillerliao',
        'items': items
    }
