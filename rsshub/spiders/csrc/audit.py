import datetime
import requests

domain = 'https://neris.csrc.gov.cn'


def parse(post):
    item = {}
    flows = post.get('aprvSchdPubFlowPOs') or []
    title = f"关于{post.get('apptPubName')}的《{post.get('appMatrName')}》"
    audit_status = [flow.get('taskName') for flow in flows if flow.get('taskName')]
    audit_date = [
        datetime.datetime.fromtimestamp(flow['fnshDate'] / 1000).strftime('%Y-%m-%d')
        for flow in flows
        if flow.get('fnshDate')
    ]

    description = title + '；'
    for d, s in zip(audit_date, audit_status):
        description += f'<{d} {s}>\n'

    item['title'] = title + ('，' + audit_status[-1] if audit_status else '')
    item['description'] = description
    item['link'] = f"{domain}/alappl/home1/onlinealog?appMatrCde={post.get('supvAppMatruuid', '')}"
    item['pubDate'] = audit_date[-1] if audit_date else ''
    return item


def ctx(category=''):
    items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'{domain}/alappl/home1/onlinealog.do?appMatrCde={category}',
    }
    for i in range(1, 4):
        q_params = {
            'appMatrCde': category,
            'appMatrName': '',
            'apptName': '',
            'pageNo': i,
            'pageSize': 10,
        }
        try:
            res = requests.get(f'{domain}/alappl/home1/newOnlinealog', params=q_params, headers=headers, verify=False, timeout=20)
            data = res.json()
        except (requests.RequestException, ValueError):
            break
        posts = data.get('appltList') or []
        if not posts:
            break
        items.extend(map(parse, posts))
    return {
        'title': f'申请事项进度查询 - {category}  - 中国证监会',
        'link': f'{domain}/alappl/home1/onlinealog?appMatrCde={category}',
        'description': f'{category} 申请事项进度查询 - 中国证监会',
        'author': 'hillerliao',
        'items': items
    }
