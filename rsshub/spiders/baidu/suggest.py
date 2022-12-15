import json
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://baidu.com'


def parse(post):
    item = {}
    item['title'] = post['q'] 
    item['description'] = post['q']
    item['link'] = f'{domain}/s?ie=UTF-8&wd=' + post['q']
    item['pubDate'] =  arrow.now().isoformat()
    item['author'] = '百度'
    return item 


def ctx(category=''):
    url = f'{domain}/sugrec?wd={category}&pre=1&p=3&ie=utf-8&json=1&prod=pc&from=pc_web&sugsid=37858,36557,37691,37908,37919,37758,37903,26350,37957,37881&req=2&csor=3&pwd=ruhe%20&cb=jQuery110209380107568499061_1671113820948&_=1671113820958'
    posts = requests.get(url).text.split('(')[-1].split(')')[0]
    posts = json.loads(posts)['g']           
    return {
        'title': f'{category} - 搜索提示 - 百度',
        'link': f'https://www.baidu.com/s?ie=UTF-8&wd={category}',
        'description': f'百度搜索提示',
        'author': 'hillerliao',
        'items': list(map(parse, posts))
    }