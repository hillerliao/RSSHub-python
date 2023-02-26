import requests
from bs4 import BeautifulSoup
import pyjsparser
import arrow

domain = 'https://mp.weixin.qq.com'


def parse(post):
    item = {}
    item['title'] = post['properties'][4]['value']['value']  
    item['description'] = post['properties'][5]['value']['value']      
    item['link'] = post['properties'][6]['value']['value']      
    item['pubDate'] = post['properties'][16]['value']['left']['value']
    item['pubDate'] = arrow.get(int(item['pubDate'])).isoformat()
    test = item['author'] = post['properties'][1]['value']['properties'][0]['value']['value']     
    return item

def ctx(c1='', tag=''):
    url = f"{domain}/mp/recommendtag?c1={c1}&tag={tag}&msg_type=1&sn=2fGf6B-xDlazPj5_t_KgEH0Gpkw"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    scripts = soup.findAll("script")[12].text        
    scripts = scripts.split('mp_msgs: ')[-1].split('isSubscribed')[0][:-6]
    posts = pyjsparser.parse(scripts)['body'][0]['expression']['elements']
    
    return {
        'title': f'{tag} - 微信公众号推荐话题',
        'link': url,
        'description': f'{tag} - 微信公众号推荐话题',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }