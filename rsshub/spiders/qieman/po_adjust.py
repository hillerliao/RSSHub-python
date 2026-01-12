import requests
import time
import math
import arrow
import hashlib
from rsshub.utils import DEFAULT_HEADERS

def get_x_sign():
    t = int(time.time() * 1000)
    # The subagent found: e + r(Math.floor(1.01 * e).toString()).toUpperCase().substring(0, 32)
    # where r is SHA-256
    s = str(math.floor(1.01 * t))
    h = hashlib.sha256(s.encode()).hexdigest().upper()[:32]
    return str(t) + h

def get_portfolio_info(portfolio_id):
    url = f'https://qieman.com/pmdj/v1/pomodels/{portfolio_id}'
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json',
        'x-sign': get_x_sign(),
        'Referer': f'https://qieman.com/sig/portfolios/{portfolio_id}/adjustments?tab=history'
    })
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get('poName'), data.get('poDesc')
    except Exception as e:
        print(f"Error fetching portfolio info: {e}")
    return None, None

def parse(post, index=0):
    item = {}
    
    sig_summary = post.get('sigSummary', '')
    adjust_summary = post.get('adjustSummary', '')
    date_str = post.get('adjustedDate', '')
    
    # Title: Prioritize adjustSummary if available
    item['title'] = adjust_summary or sig_summary or '调仓分析'
    item['title'] += f"({date_str})" if date_str else ''
    
    # Description: Construct rich HTML
    desc_parts = []
    
    # Description (Explanation)
    explanation = post.get('description')
    
    if explanation:
        header = f"本次发车说明({date_str})" if date_str else "本次发车说明"
        desc_parts.append(f"<h4>{header}</h4><p>{explanation}</p>")
    
    # Signal Summary
    buy_total = post.get('buyTotalAmount')
    if sig_summary or buy_total:
        desc_parts.append(f"<h4>本期发车信号</h4><p>{sig_summary} {f'{buy_total}元' if buy_total else ''}</p>")
    
    # Buy Orders
    buy_orders = post.get('buyOrders', [])
    if buy_orders:
        desc_parts.append("<h4>发车买入基金</h4>")
        table = "<table border='1' style='width:100%; border-collapse: collapse; text-align: left;'>"
        table += "<tr><th>基金名称</th><th>基金代码</th><th>比例</th><th>金额</th></tr>"
        for order in buy_orders:
            p = order.get('percent', 0)
            percent = f"{p * 100:.2f}%" if isinstance(p, (int, float)) else str(p)
            table += f"<tr><td>{order.get('fundName', '-')}</td><td>{order.get('fundCode', '-')}</td><td>{percent}</td><td>{order.get('amount', '-')}元</td></tr>"
        table += "</table>"
        desc_parts.append(table)
        
    # Convert Orders
    convert_orders = post.get('convertOrders', [])
    if convert_orders:
        desc_parts.append("<h4>调仓基金</h4>")
        table = "<table border='1' style='width:100%; border-collapse: collapse; text-align: left;'>"
        table += "<tr><th>转出基金</th><th>转出比例</th><th>转入至</th></tr>"
        for order in convert_orders:
            p = order.get('percent', 0)
            percent = f"{p * 100:.2f}%" if isinstance(p, (int, float)) else str(p)
            table += f"<tr><td>{order.get('fundName', '-')} ({order.get('fundCode', '-')})</td><td>{percent}</td><td>{order.get('targetFundName', '-')} ({order.get('targetFundCode', '-')})</td></tr>"
        table += "</table>"
        desc_parts.append(table)
        
    item['description'] = "".join(desc_parts) or '无内容'
    
    # Handle date
    date_str = post.get('adjustedDate')
    if date_str:
        try:
            # adjustedDate is "YYYY-MM-DD"
            item['pubDate'] = arrow.get(date_str).isoformat()
        except Exception:
            item['pubDate'] = arrow.now().isoformat()
    else:
        # Fallback to createdTime if adjustedDate is missing
        created_time = post.get('createdTime')
        if created_time:
            try:
                item['pubDate'] = arrow.get(created_time).isoformat()
            except Exception:
                item['pubDate'] = arrow.now().isoformat()
        else:
            item['pubDate'] = arrow.now().isoformat()
    
    # Link
    po_code = post.get('poCode') or 'SI000108'
    adj_id = post.get('id')
    if index == 0:
        item['link'] = f'https://qieman.com/sig/portfolios/{po_code}/adjustments?tab=latest'
    else:
        item['link'] = f'https://qieman.com/sig/portfolios/{po_code}/adjustments?tab=history&adj_id={adj_id}'
        
    return item

def ctx(portfolio_id='SI000108'):
    # Fetch dynamic metadata
    po_name, po_desc = get_portfolio_info(portfolio_id)
    
    # Verified API endpoint via browser subagent
    url = f'https://qieman.com/pmdj/v1/pomodels/{portfolio_id}/sig-adjustments?page=0&size=10'
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Accept': 'application/json, text/plain, */*',
        'x-sign': get_x_sign(),
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://qieman.com/sig/portfolios/{portfolio_id}/adjustments?tab=history',
        'Authorization': 'Bearer null'
    })
    
    posts = []
    try:
        # Set timeout to handle potential delays
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and 'content' in data:
                posts = data['content']
            elif isinstance(data, list):
                posts = data
        else:
            print(f"Failed to fetch Qieman API: {res.status_code}")
    except Exception as e:
        print(f"Error fetching Qieman API: {e}")

    return {
        'title': f'{po_name}({portfolio_id})-且慢发车记录',
        'link': f'https://qieman.com/sig/portfolios/{portfolio_id}/adjustments?tab=history',
        'description': po_desc or f'且慢组合 {portfolio_id} 的调仓记录',
        'author': 'hillerliao',
        'items': [parse(p, i) for i, p in enumerate(posts)]
    }
