import requests
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.infoq.cn'


def parse(post):
    item = {}
    item['title'] = post['article_title']
    item['description'] = f"{post['article_summary']}<br><img referrerpolicy='no-referrer' src={post.get('article_cover')}>"
    item['link'] = f"{domain}/article/{post['uuid']}"
    return item


def ctx():
    headers = DEFAULT_HEADERS.copy()
    headers.update({'Referer': 'https://www.infoq.cn'})  # 必须设置Referer，不然会451错误
    import json
    try:
        response = requests.post(f'{domain}/public/v1/my/recommond', json={'size': 20}, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = json.loads(response.text)
        posts = data.get('data', [])
    except requests.RequestException as e:
        print(f'Request error: {e}')
        posts = []
    except json.JSONDecodeError as e:
        print(f'JSON decode error: {e}')
        posts = []
    except KeyError as e:
        print(f'Key error in response: {e}')
        posts = []
    
    return {
        'title': 'infoq',
        'link': domain,
        'description': 'InfoQ - 促进软件开发领域知识与创新的传播',
        'author': 'alphardex',
        'items': list(map(parse, posts))
    }