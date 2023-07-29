from unicodedata import category
import requests
import json
import arrow
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856'

type = ''

def parse(post):
    item = {}
    item['title'] = '【原文】' + post['thread']['title'] + ' → 【跟贴】' + post['comments'][0]['1']['content'] 
    item['description'] = '【回帖】' + post['comments'][1]['1']['content'] if len(post['comments']) > 1 \
                        else '【回帖】' + post['comments'][0]['2']['content']  if '2' in post['comments'][0]  \
                        else ''
    thread_link = post['thread']['url']
    item['description'] = item['description'] + f' <a href="{thread_link}">原文链接</a>'
    item['link'] = f"https://comment.tie.163.com/{post['thread']['docId']}.html"
    item['author'] = ''
    item['pubDate'] =  arrow.now().isoformat()
    return item


def ctx(category=''):
    type = category
    paths = {"heated":"/heatedList/allSite?ibc=newspc&page=1",
            "splendid":"/recommendList/single?ibc=newspc&offset=0&limit=30",
            "build":"/recommendList/build?ibc=newspc&offset=0&limit=15&showLevelThreshold=72"}
    url = domain + paths[category]
    res = requests.get(url, headers=DEFAULT_HEADERS)
    res = json.loads(res.text)
    posts = res
    items = list(map(parse, posts))
    return {
        'title': f'{category} - 网易跟贴',
        'link': "https://comment.163.com/#/" + category,
        'description': f'{category} - 网易跟贴',
        'author': 'hillerliao',
        'items': items
    }
