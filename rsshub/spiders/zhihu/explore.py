from itertools import chain

from .article import *


def ctx():
    r_url = 'https://www.zhihu.com/explore'
    tree = fetch(r_url)
    items = {}
    channel = {}

    hot_question = tree.css('.css-1nd7dqm')
    newest_topic = tree.css('.ExploreSpecialCard-contentTitle')
    discussion = tree.css('.ExploreRoundtableCard-questionTitle')
    collection_card = tree.css('.ExploreCollectionCard-contentTitle')

    for post in chain(hot_question, collection_card, discussion): #, newest_topic):
        title = post.css('a::text').extract_first()
        link: str = post.css('a::attr(href)').extract_first()

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
