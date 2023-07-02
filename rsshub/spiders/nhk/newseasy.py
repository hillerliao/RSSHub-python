import json
import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www3.nhk.or.jp'


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['title_with_ruby'] + '<br/><br/>' + post['outline_with_ruby']
    item['link'] = f"{domain}/news/easy/{post['news_id']}/{post['news_id']}.html"
    return item


def ctx(category=''):
    url = f'{domain}/news/easy/top-list.json'
    posts = requests.get(
        url,
        headers=DEFAULT_HEADERS,
    ).text
    posts = json.loads(posts)
    return {
        'title': 'News Web Easy - NHK',
        'link': f'{domain}/news/easy/',
        'description': 'NEWS WEB EASYは、小学生・中学生の皆さんや、日本に住んでいる外国人のみなさんに、わかりやすいことば　でニュースを伝えるウェブサイトです。',
        'author': 'hillerliao',
        'items': list(map(parse, posts)),
    }
