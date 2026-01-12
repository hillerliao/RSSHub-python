import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS
from flask import request as flask_request

def get_accesstoken():
    """从请求参数或环境变量中获取accesstoken"""
    # 优先从URL参数获取，如果缺失则尝试从环境变量获取
    # 使用环境变量可以避免在URL中暴露令牌，更加安全
    import os
    accesstoken = flask_request.args.get('accesstoken') or os.environ.get('DANJUAN_ACCESSTOKEN')
    return accesstoken

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

def get_portfolio_info(ic_plan_code, accesstoken=None):
    """获取组合信息：名称和简介"""
    url = f'https://danjuanfunds.com/djapi/fundx/portfolio/ic/plan/info?ic_plan_code={ic_plan_code}'
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json',
        'Referer': f'https://danjuanfunds.com/n/departure/{ic_plan_code}'
    })
    
    # 构造cookie
    cookies = None
    if accesstoken:
        cookies = {'accesstoken': accesstoken}
    
    portfolio_name = f'策略{ic_plan_code}'
    portfolio_intro = ''
    
    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('result_code') == 0:
                data_dict = data.get('data', {})
                # tp_plan_name 位于 data.plan_info 层级
                plan_info = data_dict.get('plan_info', {})
                portfolio_name = plan_info.get('tp_plan_name', f'策略{ic_plan_code}')
                # dynamic_text 位于 data.plan_desc 层级
                plan_desc = data_dict.get('plan_desc', {})
                portfolio_intro = plan_desc.get('dynamic_text', '')
    except Exception as e:
        print(f"Error fetching portfolio info: {e}")
    
    return portfolio_name, portfolio_intro

def ctx(strategy_code='TIA08030', page_no=1, page_size=20):
    """主函数：获取调仓数据并返回RSS上下文
    
    Args:
        strategy_code: 策略代码，默认TIA08030
        page_no: 页码，默认1
        page_size: 每页数量，默认20
    
    认证：通过URL参数accesstoken传递访问令牌
        例如：/danjuan/departure/TIA08030?accesstoken=xxx
    """
    
    # 获取accesstoken
    accesstoken = get_accesstoken()
    
    # 获取组合名称和简介
    portfolio_name, portfolio_intro = get_portfolio_info(strategy_code, accesstoken)
    
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
    
    # 构造cookie
    cookies = None
    if accesstoken:
        cookies = {'accesstoken': accesstoken}
    
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
    
    # 构建RSS描述，包含组合简介
    description_parts = []
    # Channel title：直接使用tp_plan_name
    channel_title = f'{portfolio_name} 调仓-蛋卷投顾组合' 
    # Channel description：组合名称 + 简介
    channel_description = f'{portfolio_name}'
    if portfolio_intro:
        channel_description = f'{portfolio_name} - {portfolio_intro}'
    
    description_parts.append(f'<p>{portfolio_name}</p>')
    if portfolio_intro:
        description_parts.append(f'<p>{portfolio_intro}</p>')
    description_parts.append('<p>来自蛋卷基金的调仓发车记录。</p>')
    rss_description = ''.join(description_parts)
    
    return {
        'title': channel_title,
        'link': f'https://danjuanfunds.com/n/departure/{strategy_code}',
        'description': rss_description,
        'author': 'hillerliao',
        'items': items
    }
