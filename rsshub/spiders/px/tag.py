import requests
from rsshub.utils import DEFAULT_HEADERS
from jinja2 import Template
from zoneinfo import ZoneInfo
import datetime

domain = "https://500px.com.cn" 
tag = {"rating":"热门","rankingRise":"排名上升","created_date":"新作","recommendTime":'编辑推荐'}


tpl = '''<img src="{{imageUrl}}" alt="文章配图" />'''
template = Template(tpl)

def getDate(id):
    url = f'{domain}/community/photo-details/{id}?type=json'
    data = requests.get(url=url,headers=DEFAULT_HEADERS).json()
    timestamp = int(data["uploadedDate"])
    timestamp = timestamp / 1000.0
    utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    sh_dt = utc_dt.astimezone(ZoneInfo('Asia/Shanghai'))
    return sh_dt

def parse(post):
    item = {}
    item["title"] = post["title"]
    item["author"] = post["uploaderInfo"]["nickName"]
    item["link"] = f"https://500px.com.cn/photo/{post['id']}"
    imageUrl = post["url"]["baseUrl"]+"!p5"
    item["description"] = template.render({'imageUrl': imageUrl, })
    item['pubDate'] = getDate(post["id"])
    return item



def ctx(category=''):
    url = f'{domain}/community/discover/{category}'
    if category not in tag.keys():
       return {
            'title': f'500px{category}分区',
            'link': url,
            'description': f'{category}应在{tag}里面',
            'author': '1200522928',
            'items': []
        }
    data = requests.get(url=url,headers=DEFAULT_HEADERS).json()
    return {
            'title': f'500px{tag[category]}分区',
            'link': url,
            'description':f'500px{tag[category]}分区' ,
            'author': '1200522928',
            'items': list(map(parse,data))
        }