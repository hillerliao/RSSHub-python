from itertools import chain

from .article import *


def ctx():
    r_url = 'https://www.zhihu.com/explore'
    tree = fetch(r_url)
    items = {}
    channel = {}

    hot_question = tree.select('.ExploreSpecialCard-contentTitle')
    newest_topic = tree.select('.ExploreSpecialCard-contentTitle')
    discussion = tree.select('.ExploreRoundtableCard-questionTitle')
    collection_card = tree.select('.ExploreCollectionCard-contentTitle')

    for post in chain(hot_question, collection_card, discussion): #, newest_topic):
        link_elem = post.select('a')
        link = None  # Initialize link variable
        title = None  # Initialize title variable
        if link_elem:
            title = link_elem[0].get_text()
            link: str = link_elem[0]['href']
        else:
            # Check parent element for link
            parent = post.parent
            if parent:
                parent_links = parent.select('a')
                if parent_links:
                    title = post.get_text()
                    link = parent_links[0]['href']

        if link:
            if not (link.startswith('https://www.zhihu.com')
                    or link.startswith('https://zhuanlan.zhihu.com')):
                link = f'https://www.zhihu.com{link}'

            if link.startswith('https://www.zhihu.com/question/'):
                item = ZhihuQuestion(link, title=title)
                channel[link] = item
            elif link.startswith('https://zhuanlan.zhihu.com/p'):
                item = ZhihuZhuanlanArticle(link)
                item.get()
                items[link] = item
            elif link.startswith('https://www.zhihu.com/answer/'):
                item = ZhihuAnswer(link)
                item.get()
                items[link] = item
            else:
                items[link] = {
                    'title': title,
                    'link': link,
                    'description': title
                }

    for c in channel.values():
        c.get_description()
        for i in c.items:
            items[i.link] = i

    return {
        'title': f'发现 - 知乎',
        'link': r_url,
        'items': list(items.values())
    }
