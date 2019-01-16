import requests

data = requests.get(
    'https://www.guokr.com/apis/minisite/article.json?retrieve_type=by_subject'
).json()['result']


def parse(d):
    item = {}
    item['title'] = d['title']
    item['description'] = f"{d['summary']}<br><img referrerpolicy='no-referrer' src={d['image_info']['url']}"
    item['pubDate'] = d['date_published']
    item['link'] = d['url']
    return item


ctx = {
    'title': '果壳网 科学人',
    'link': 'https://www.guokr.com/scientific',
    'description': '果壳网 科学人',
    'author': 'alphardex',
    'items': list(map(parse, data))
}