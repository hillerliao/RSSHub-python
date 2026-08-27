import json
from rsshub.utils import DEFAULT_HEADERS, fetch_with_deadline

domain = 'https://readhub.cn'
api_domain = 'https://api.readhub.cn'

# 总耗时预算(秒):给 Vercel 10s 限制留出冷启动余量,
# 避免上游跨境访问过慢/慢速爬行导致网关 504
REQUEST_DEADLINE = 6.0
REQUEST_TIMEOUT = 5.0


def parse(post):
    item = {}
    item['title'] = post['title']
    item['description'] = post['summary']
    item['link'] = f"{domain}/topic/{post['uid']}"
    item['author'] = post['siteNameDisplay']
    item['pubDate'] = post['publishDate']
    return item


def ctx(type='', uid=''):
    referer = f'{domain}/entity_topics?type=22&uid={uid}&tb=0'
    DEFAULT_HEADERS.update({'Referer': referer})
    type_name = 'entity' if type == '10' else 'tag'
    url = f'{api_domain}/topic/list_pro?{type_name}_id={uid}&size=10'

    try:
        res = fetch_with_deadline(url, headers=DEFAULT_HEADERS, deadline=REQUEST_DEADLINE, timeout=REQUEST_TIMEOUT)
        data = json.loads(res.text)['data']
        topic_name = data['self'][f'{type_name}List'][0]['name']
        posts = data['items']
    except Exception as e:
        print(f'[readhub/topic] 数据获取失败: {e}')
        topic_name = uid
        posts = []

    items = []
    for post in posts:
        try:
            items.append(parse(post))
        except Exception as e:
            print(f'[readhub/topic] 跳过异常条目: {e}')

    return {
        'title': f'{topic_name} - 主题 - Readhub',
        'link': referer,
        'description': f'"{topic_name}"动态' + (' (数据获取失败或暂无内容)' if not items else ''),
        'author': 'hillerliao',
        'items': items,
    }
