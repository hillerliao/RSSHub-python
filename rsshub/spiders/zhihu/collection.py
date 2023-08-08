import json
import requests

from .article import ZhihuAnswer, ZhihuZhuanlanArticle



def get_metadata(collection_id):
    response = requests.get(f'https://api.zhihu.com/collections/{collection_id}')
    response.raise_for_status()
    data = json.loads(response.text)['collection']

    metadata = dict()
    metadata['link'] = data['url']
    metadata['title'] = data['title']
    # metadata['created_time'] = data['created_time']
    # metadata['updated_time'] = data['updated_time']
    return metadata

def ctx(collection_id):

    # meta
    metadata = get_metadata(collection_id)

    # content

    response = requests.get(f'https://www.zhihu.com/api/v4/collections/{collection_id}/items?limit=20&offset=0')
    response.raise_for_status()
    data = json.loads(response.text)
    items = []

    for d in data['data']:
        if d['content']['type'] == 'answer':
            item = ZhihuAnswer(d['content']['url'])
        elif d['content']['type'] == 'article':
            item = ZhihuZhuanlanArticle(d['content']['url'])
        else:
            assert False
        item.get()
        items.append(item)

    metadata['items'] = items

    return metadata
