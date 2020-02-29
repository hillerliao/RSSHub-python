import requests
from parsel import Selector

domain = 'https://neris.csrc.gov.cn'


def parse(post):
    item = {}
    item['title'] = post.css('li.templateTip').css('li::text').extract_first()
    audit_status = post.css('td[style="font-weight:100 ;color: black ;position: relative;left:20px"]').css('td::text').extract()
    audit_date = post.css('td[style="font-weight:100 ;color:black;position: relative; "]').css('td::text').extract()
    
    description = item['title'] + '；'
    for i in range(len(audit_status)):
        description += '<' + audit_date[i] + ' ' + audit_status[i] + '>\n'

    item['title'] += '，' + audit_status[-1]
    item['description'] = description
    item['pubDate'] = audit_date[-1]
    return item


def ctx(category=''):
    q_url = f"{domain}/alappl/home1/onlinealog.do"
    items = []
    for i in range(1,4):
        q_data = {"appMatrCde": category, "pageNo": str(i), "pageSize": "10"}
        res = requests.post(q_url,data=q_data, verify=False)
        tree = Selector(res.text)
        posts = tree.css('tr[height="50"]')
        items.extend(list(map(parse, posts)))
    return {
        'title': f'申请事项进度查询 - {category}  - 中国证监会',
        'link': f'{domain}/alappl/home1/onlinealog?appMatrCde={category}',
        'description': f'{category} 申请事项进度查询 - 中国证监会',
        'author': 'hillerliao',
        'items': items
    }
