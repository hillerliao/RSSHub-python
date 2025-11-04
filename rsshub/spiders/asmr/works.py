import requests
import pytz
from jinja2 import Template
from datetime import datetime
from urllib.parse import unquote

domain = 'https://api.asmr-200.com/api/search'

tpl = '''
<a href="{{ link }}" title="点击进入官网查看"><img src="{{ work['mainCoverUrl'] }}" alt="{{ work['title'] }}" /></a>
<h1>{{ work['title'] }} <span style="font-size: 0.6em; color: darkred;">{{ work['source_id'] }}</span></h1>
<p><b>发布者：</b>{{ work['name'] }}</p>
<p><b>评分：</b>{{ work['rate_average_2dp'] }} | <b>评论数：</b>{{ work.review_count }} | <b>总时长：</b>{{ work['duration'] }} | <b>音频来源：</b>{{ work['source_type'] }}</p>
<p><b>价格：</b><span style="color: #f44336">{{ work.price }} JPY</span> | <b>销量：</b>{{ work['dl_count'] }}</p>
<p><b>分类：</b>{{ work['category'] }}</p>
<p><b>声优：</b>{{ work['cv'] }}</p>
'''

template = Template(tpl)

def parse(post):
    url = f'https://asmr-200.com/work/{post["source_id"]}'
    post['category'] = ', '.join(map(lambda tag: tag['name'], post['tags']))
    post['cv'] = ', '.join(map(lambda cv: cv['name'], post['vas']))
    return {
        'title': post['title'],
        'image': post['mainCoverUrl'],
        'author': post['name'],
        'link': url,
        'pubDate': pytz.timezone('Asia/Shanghai').localize(datetime.strptime(post['release'], '%Y-%m-%d')),
        'category': post['category'],
        'description': template.render({'work': post, 'link': url})
    }

def ctx(search='', order='create_date', subtitle=0, sort='desc'):
    top_url = f'{domain}/{search}?order={order}&subtitle={subtitle}&sort={sort}'
    res = requests.get(top_url).json()
    
    return {
        'title': f'ASMR{"-" + unquote(search) if search != "" else ""}',
        'link': top_url,
        'description': 'ASMR Search Subscription',
        'author': 'Bamboo_King',
        'items': list(map(parse, res['works']))
    }
    
