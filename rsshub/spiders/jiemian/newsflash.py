import requests
import json
from parsel import Selector
from datetime import datetime, date

domain = 'https://jiemian.com'


def parse(post):
    item = {}
    item['title'] = post.css('a::text').extract_first()
    item['description'] = post.css('p::text').extract()[-1]\
                              .strip('】\n\t\t\t\t\t')
    item['link'] = post.css('a::attr(href)').extract_first()
    pubdate = post.xpath('//div[@class="item-news "]/\
                   preceding::div[@class="col-date"][last()-1]')\
                  .css('div::text').extract_first()
    cur_t = datetime.now().time().strftime("%H%M")
    pub_t = post.css('.item-date').css('div::text').extract_first()
    if pub_t.replace(':', '') < cur_t:
        pubdate = date.today().isoformat()
    item['pubDate'] = pubdate + ' ' + pub_t
    return item


def ctx(category=''):
    res = requests.get(f"https://a.jiemian.com/index.php?\
                       m=lists&a=ajaxNews&page=1&cid={category}")
    res = res.text[1:-1]
    res = json.loads(res)['rst']
    tree = Selector(text=res)
    posts = tree.css('.item-news')
    items = list(map(parse, posts))
    return {
        'title': f'{category} 快讯 - 界面新闻',
        'link': f'{domain}//lists/{category}.html',
        'description': f'{category} 快讯 - 界面新闻',
        'author': 'hillerliao',
        'items': items
    }
