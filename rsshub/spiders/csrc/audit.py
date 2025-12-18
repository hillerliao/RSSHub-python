import requests
from bs4 import BeautifulSoup

domain = 'https://neris.csrc.gov.cn'


def parse(post):
    item = {}
    title_li = post.select('li.templateTip li')
    item['title'] = title_li[0].text.strip() if title_li else ''
    audit_status_tds = post.select('td[style="font-weight:100 ;color: black ;position: relative;left:20px"]')
    audit_status = [td.text.strip() for td in audit_status_tds]
    audit_date_tds = post.select('td[style="font-weight:100 ;color:black;position: relative; "]')
    audit_date = [td.text.strip() for td in audit_date_tds]
    
    description = item['title'] + '；'
    for i in range(len(audit_status)):
        description += '<' + audit_date[i] + ' ' + audit_status[i] + '>\n'

    item['title'] += '，' + audit_status[-1] if audit_status else ''
    item['description'] = description
    item['pubDate'] = audit_date[-1] if audit_date else ''
    return item


def ctx(category=''):
    q_url = f"{domain}/alappl/home1/onlinealog.do"
    items = []
    for i in range(1,4):
        q_data = {"appMatrCde": category, "pageNo": str(i), "pageSize": "10"}
        res = requests.post(q_url,data=q_data, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = soup.select('tr[height="50"]')
        items.extend(list(map(parse, posts)))
    return {
        'title': f'申请事项进度查询 - {category}  - 中国证监会',
        'link': f'{domain}/alappl/home1/onlinealog?appMatrCde={category}',
        'description': f'{category} 申请事项进度查询 - 中国证监会',
        'author': 'hillerliao',
        'items': items
    }
