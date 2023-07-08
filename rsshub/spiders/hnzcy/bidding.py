import json
import datetime
import arrow
import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://hunan.zcygov.cn'

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'DNT': '1',
    'Origin': 'https://hunan.zcygov.cn',
    'Referer': 'https://hunan.zcygov.cn/bidding/newest?tradeModel=BIDDING&utm=luban.luban-PC-64.82-hunan-bidding-pc.1.7b6b17b01d7111ee97b97bde6f3bef69',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}


def parse(post):
    item = {}
    item['title'] = f'[{post["districtName"]}] {post["title"]} '
    budget = "{:.2f}".format(
        round ( post["budget"] / 100.0 , 2)
        ) 
    end_time = post['endTimestamp'] / 1000

    dt_object = datetime.datetime.fromtimestamp(end_time)
    end_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")

    item['description'] = f'{item["title"]}；采购单位：{post["orgName"]}； 金额：{budget}元；截止：{end_time}'
    item['link'] = f"{domain}/bidding/detail?requisitionId={post['requisitionId']}&type={post['type']}"
    item['author'] = post['orgName'] 
    item['pubDate'] = arrow.get(post['pubTimestamp']).isoformat()
    return item


def ctx(type=''):
    url = f'{domain}/front/api/sparta/announcement/list{type}'
    json_data = {
        'backCategoryName': '',
        'pageNo': 1,
        'pageSize': 16,
        'stateList': [],
        'otherSearch': '',
        'instanceCode': 'HNDZMC',
        'sortField': 'GMT_MODIFIED', 
        'sortMethod': 'DESC',
        'districtCodeList': [],
        'administrativeDistrictCodeList': [],
        'tradeModel': 'BIDDING',
    }

    response = requests.post(
        url,
        headers=headers,
        json=json_data,
    )

    posts = json.loads(response.text)['result']['list']
    items = list(map(parse, posts))    


    return {
        'title': f'{type} - 湖南竞价',
        'link': f'{domain}/bidding/',
        'description': f'政采云”是政府采购云计算服务平台的简称。以互联⽹为基础，充分运⽤云计算和⼤数据技术，以政府采购电⼦化交易和管理为重点，涉及政府采购全流程、各领域、多用户，集政府采购、网上交易、⽹上监管和⽹上服务为一体的综合性云服务平台。',
        'author': 'hillerliao',
        'items': items
    }
