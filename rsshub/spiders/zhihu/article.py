import re
import json

from dataclasses import dataclass, field, asdict
from datetime import datetime

import requests
from rsshub.utils import fetch


def get_value(d):
    return list(d.values())[0]


@dataclass
class Feed:
    link: str
    title: str = ''
    author: str = '未知作者'
    description: str = ''
    items: list = field(default_factory=list)


@dataclass
class AtomEntry:
    link: str
    title: str = ''
    author: str = '未知作者'
    pubDate: datetime = datetime.now()
    updated_time: datetime = datetime.now()

    description: str = ''
    content: str = ''


class ZhihuAnswer(AtomEntry):
    def get(self):
        tree = fetch(self.link)
        if tree is None:
            return
            
        h1_elem = tree.select('h1')
        self.title = h1_elem[0].get_text() if h1_elem else ''
        rich_text_elem = tree.select('.RichText')
        self.content = zhihu_figure_transfer(rich_text_elem[0].decode_contents() if rich_text_elem else '')
        self.description = self.content

        # author

        answer_item = tree.select('div.ContentItem.AnswerItem')
        self.author = json.loads(answer_item[0]['data-zop'])['authorName'] if answer_item else ''

        js_data_elem = tree.select("#js-initialData")
        meta: dict = get_value(json.loads(js_data_elem[0].get_text())
                               ['initialState']['entities']['questions']) if js_data_elem else {}

        self.pubDate = datetime.fromtimestamp(meta['created'])
        self.updated_time = datetime.fromtimestamp(meta['updatedTime'])


class ZhihuZhuanlanArticle(AtomEntry):
    def get(self):
        tree = fetch(self.link)
        if tree is None:
            return
            
        h1_elem = tree.select('h1')
        self.title = h1_elem[0].get_text() if h1_elem else ''
        author_meta = tree.select('meta[itemprop="name"]')
        if author_meta:
            self.author = author_meta[0]['content']
        article_rich = tree.select('article .RichText')
        self.content = zhihu_figure_transfer(article_rich[0].decode_contents() if article_rich else '')
        self.description = self.content

        #
        js_data_elem = tree.select("#js-initialData")
        data = json.loads(js_data_elem[0].get_text()) if js_data_elem else {}
        metadata = list(data['initialState']['entities']['articles'].values())[0]
        self.pubDate = datetime.fromtimestamp(metadata['created'])
        self.updated_time = datetime.fromtimestamp(metadata['updated'])


class ZhihuQuestion(Feed):

    def get_description(self):
        tree = fetch(self.link)
        if tree is None:
            return
            
        desc_meta = tree.select('meta[name="description"]')
        self.description = desc_meta[0].get_text() if desc_meta else ''

        js_data_elem = tree.select("#js-initialData")
        data = json.loads(js_data_elem[0].get_text()) if js_data_elem else {}
        for answer_id in list(data['initialState']['question']['answers'].values())[0]['ids']:
            assert answer_id['targetType'] == 'answer'
            item = ZhihuAnswer(f'{self.link}/answer/{answer_id["target"]}')
            item.get()
            self.items.append(item)

        self.next = list(data['initialState']['question']['answers'].values())[0]['next']

    def get_all(self):
        if 'next' not in self.__dict__:
            self.get_description()

        while True:
            data = json.loads(requests.get(self.next).text)

            for d in data['data']:
                target = d['target']
                author = target['author']['name']
                content = zhihu_figure_transfer(target['content'])

                self.items.append(ZhihuAnswer(
                    title=f'{author}的回答',
                    author=author,
                    link=f'{self.link}/answer/{target["id"]}',
                    pubDate=datetime.fromtimestamp(target['created_time']),
                    updated_time=datetime.fromtimestamp(target['updated_time']),
                    description=zhihu_figure_transfer(content)
                ))

            if data['paging']['is_end']:
                del self.next
                break

            self.next = data['paging']['next']


def zhihu_figure_transfer(content):
    pattern = r'<figure(.*?)<noscript>(.*?)</noscript>(.*?)</figure>'
    return re.sub(pattern, lambda match: match.group(2), content)


def ctx_question(qid):
    url = f'https://www.zhihu.com/question/{qid}'
    question = ZhihuQuestion(url)
    question.get_all()
    return asdict(question)