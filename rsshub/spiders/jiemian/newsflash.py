import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, date

domain = 'https://jiemian.com'


def parse(post):
    item = {}
    a_tag = post.select('a')
    item['title'] = a_tag[0].text.strip() if a_tag else ''
    p_tags = post.select('p')
    item['description'] = p_tags[-1].text.strip('】\n\t\t\t\t\t') if p_tags else ''
    item['link'] = a_tag[0].get('href') if a_tag else ''
    # pubdate 部分复杂，暂时简化
    pubdate = date.today().isoformat()
    pub_t = post.select('.item-date div')
    pub_t = pub_t[0].text if pub_t else '00:00'
    item['pubDate'] = pubdate + ' ' + pub_t
    return item


def ctx(category=''):
    res = requests.get(f"https://a.jiemian.com/index.php?\
                       m=lists&a=ajaxNews&page=1&cid={category}")
    res = res.text[1:-1]
    res = json.loads(res)['rst']
    soup = BeautifulSoup(res, 'html.parser')
    posts = soup.select('.item-news')
    items = list(map(parse, posts))
    return {
        'title': f'{category} 快讯 - 界面新闻',
        'link': f'{domain}//lists/{category}.html',
        'description': f'{category} 快讯 - 界面新闻',
        'author': 'hillerliao',
        'items': items
    }
