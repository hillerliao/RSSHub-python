import requests
import json
import arrow
from rsshub.utils import DEFAULT_HEADERS


def parse(post):
    item = {}
    item['title'] = post['ArticleTitle']
    item['description'] = post['ArticleBrief']
    articleid = post['ArticleId']
    item['link'] = f'https://api3.cls.cn/share/article/{articleid}?os=android&sv=734&app='
    item['author'] = post['ArticleAuthor']
    item['pubDate'] = arrow.get(int(post['ArticleTime'])).isoformat()
    return item


def ctx(category=''):
    url = f'https://i.cls.cn/articles/subject/v1/{category}?sign=ab07b305da92f72ea5e509ba6d1216ff&app=cailianpress&LastTime=&PageNum=20&os=android&sv=734'
    res = requests.get(url, headers=DEFAULT_HEADERS)
    res = json.loads(res.text)
    posts = res
    items = list(map(parse, posts))
    return {
        'title': f'{category} - 主题 - 财联社',
        'link': f'https://api3.cls.cn/share/subject/{category}?os=android&sv=734',
        'description': f'{category} - 主题 - 财联社',
        'author': 'hillerliao',
        'items': items
    }
