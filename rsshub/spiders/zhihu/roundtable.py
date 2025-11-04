import json
import requests

from .article import ZhihuQuestion

def ctx(name):
    url = f'https://www.zhihu.com/api/v4/roundtables/{name}/hot-questions?include=data[*].question.relationship'
    response = requests.get(url)
    response.raise_for_status()

    data = json.loads(response.text)
    items = []

    for d in data['data']:
        item = ZhihuQuestion(f'https://www.zhihu.com/question/{d["question"]["id"]}')
        item.get_description()

        items.append(item)

    return {
        'title': 'roundtable',
        'items': items
    }
