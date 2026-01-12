import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS
from flask import request as flask_request

def get_auth_cookies():
    """从请求参数中获取认证cookie"""
    # 支持通过URL参数传递cookie字符串
    cookie_str = flask_request.args.get('cookie') or flask_request.args.get('cookies')
    if cookie_str:
        return cookie_str
    return None

def parse(post, index=0, strategy_code='TIA08030'):
    """解析单条调仓记录"""
    item = {}
    
    departure_date = post.get('departure_date', '')
    departure_amount = post.get('departure_amount', '')
    trade_desc = post.get('trade_desc', '')
    departure_message = post.get('departure_message', '')
    departure_plan_outline = post.get('departure_plan_outline', '')
    departure_no = post.get('departure_no', '')
    
    # 标题：调仓消息 + 日期
    item['title'] = f"{departure_message} - {departure_date}" if departure_message else departure_date
    
    # 描述：包含详细信息的HTML
    desc_parts = []
    
    if departure_plan_outline:
        desc_parts.append(f"<h4>{departure_plan_outline}</h4>")
    
    if trade_desc:
        desc_parts.append(f"<p><strong>市场分析：</strong>{trade_desc}</p>")
    
    # 添加发车金额信息
    if departure_amount:
        desc_parts.append(f"<p><strong>发车金额：</strong>{departure_amount}元</p>")
    
    # 添加市场情绪信息
    market_sentiment = post.get('market_sentiment', {})
    if market_sentiment:
        sentiment_value = market_sentiment.get('sentiment_value')
        sentiment_desc = ''
        for enum_item in market_sentiment.get('sentiment_enums', []):
            if enum_item.get('value') == sentiment_value:
                sentiment_desc = enum_item.get('desc', '')
                break
        if sentiment_value is not None:
            desc_parts.append(f"<p><strong>市场情绪：</strong>{sentiment_desc} ({sentiment_value}/10)</p>")
    
    # 添加投资建议
    invest_advice = post.get('departure_invest_advice', {})
    if invest_advice:
        advice_desc = invest_advice.get('desc', '')
        if advice_desc:
            desc_parts.append(f"<p><strong>投资建议：</strong>{advice_desc}</p>")
    
    item['description'] = ''.join(desc_parts) or trade_desc or '无内容'
    
    # 日期处理
    if departure_date:
        try:
            item['pubDate'] = arrow.get(departure_date).isoformat()
        except Exception:
            item['pubDate'] = arrow.now().isoformat()
    else:
        item['pubDate'] = arrow.now().isoformat()
    
    # 链接
    item['link'] = f'https://danjuanfunds.com/n/departure/{strategy_code}?departure_no={departure_no}'
    
    return item

def get_strategy_name(strategy_code, cookies=None):
    """获取策略名称"""
    url = f'https://danjuanfunds.com/djapi/fundx/ic/activity/server/departure/scheme/info?strategy_code={strategy_code}'
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json',
        'Referer': f'https://danjuanfunds.com/n/departure/{strategy_code}'
    })
    
    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('result_code') == 0:
                scheme_info = data.get('data', {}).get('scheme_info', {})
                return scheme_info.get('scheme_name', f'策略{strategy_code}')
    except Exception as e:
        print(f"Error fetching strategy info: {e}")
    return f'策略{strategy_code}'

def ctx(strategy_code='TIA08030', page_no=1, page_size=20):
    """主函数：获取调仓数据并返回RSS上下文"""
    
    # 获取认证cookie
    cookies_str = get_auth_cookies()
    cookies = None
    if cookies_str:
        # 解析cookie字符串为字典
        cookies = {}
        for item in cookies_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
    
    # 获取策略名称
    strategy_name = get_strategy_name(strategy_code, cookies)
    
    # 构建API请求URL
    url = 'https://danjuanfunds.com/djapi/fundx/ic/activity/server/departure/scheme/list'
    params = {
        'page_no': page_no,
        'page_size': page_size,
        'strategy_code': strategy_code,
        'request_page': 'product'
    }
    
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'https://danjuanfunds.com/n/departure/{strategy_code}',
        'DNT': '1'
    })
    
    items = []
    try:
        res = requests.get(url, headers=headers, params=params, cookies=cookies, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('result_code') == 0:
                items_data = data.get('data', {}).get('items', [])
                items = [parse(item, i, strategy_code) for i, item in enumerate(items_data)]
            else:
                print(f"API Error: {data.get('result_code')} - {data.get('result_msg')}")
        else:
            print(f"Failed to fetch departure data: {res.status_code}")
    except Exception as e:
        print(f"Error fetching departure data: {e}")
    
    return {
        'title': f'{strategy_name} - 调仓动态',
        'link': f'https://danjuanfunds.com/n/departure/{strategy_code}',
        'description': f'{strategy_name} 的调仓发车记录，来自蛋卷基金',
        'author': 'hillerliao',
        'items': items
    }
