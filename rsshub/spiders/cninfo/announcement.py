import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'http://www.cninfo.com.cn'


def parse(post):
    item = {}
    item['title'] = post['secName']  + '('  + post['secCode']  + ')'  + ': '  + post['announcementTitle']
    item['description'] = item['title']
    item['link'] = 'http://static.cninfo.com.cn/' + post['adjunctUrl']
    item['pubDate'] = post['announcementTime']
    return item 


def ctx(stock_id='', category=''):
    stock_id = '' if stock_id == 'all' else stock_id
    stock_name = ''
    stock_list = requests.get('http://www.cninfo.com.cn/new/data/szse_stock.json', headers=DEFAULT_HEADERS).json()['stockList']
    for stock in stock_list:
        if stock['code'] == stock_id :
            stock_id = stock['orgId']
            stock_name = stock['zwjc']
            break
    
    import datetime
    nowtime = datetime.datetime.now()
    deltaday=datetime.timedelta(days=1)
    start_date = datetime.datetime.strftime(nowtime- 700 * deltaday, '%Y-%m-%d')
    end_date = datetime.datetime.strftime(nowtime + 2 * deltaday, '%Y-%m-%d')
    seDate = start_date + '~' + end_date

    searchkey = ''
    column = ''
    if '_' in category:
        searchkey = category.split('_')[-1]
        category = category.split('_')[0]
        category = '' if category == 'all' else f'category_{category}_szsh'
        # column = 'szse'

        
    DEFAULT_HEADERS.update({'Referer': domain}) 
    post_data = {'pageNum':'1', 'pageSize': '30','column': column, 'tabName':'fulltext', 'plate': '', \
                'category': category, 'secid': stock_id, 'seDate': seDate, 'searchkey': searchkey }
    print(post_data)
    posts = requests.post(f'{domain}/new/hisAnnouncement/query', \
            data=post_data, headers=DEFAULT_HEADERS).json()['announcements']
    return {
        'title': f'{stock_name}-{category}-公告-巨潮资讯',
        'link': f'{domain}/new/commonUrl/pageOfSearch?url=disclosure/list/search&checkedCategory=category_{category}_szsh&searchkey={searchkey}',
        'description': f'{stock_name}关于{category}的公告-巨潮资讯',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }