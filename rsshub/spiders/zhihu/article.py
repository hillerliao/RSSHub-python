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
        self.title = tree.css('h1::text').get()
        self.content = zhihu_figure_transfer(tree.css('.RichText').get())
        self.description = self.content

        # author

        self.author = json.loads(tree.xpath('//div[@class="ContentItem AnswerItem"]/@data-zop').get())['authorName']

        meta: dict = get_value(json.loads(tree.css("#js-initialData::text").get())
                               ['initialState']['entities']['questions'])

        self.pubDate = datetime.fromtimestamp(meta['created'])
        self.updated_time = datetime.fromtimestamp(meta['updatedTime'])


class ZhihuZhuanlanArticle(AtomEntry):
    def get(self):
        tree = fetch(self.link)
        self.title = tree.css('h1::text').get()
        author = tree.xpath('//meta[@itemProp="name"]/@content').get()
        if author:
            self.author = author
        self.content = zhihu_figure_transfer(tree.css('article').css('.RichText').get())
        self.description = self.content

        #
        data = json.loads(tree.css("#js-initialData::text").get())
        metadata = list(data['initialState']['entities']['articles'].values())[0]
        self.pubDate = datetime.fromtimestamp(metadata['created'])
        self.updated_time = datetime.fromtimestamp(metadata['updated'])


class ZhihuQuestion(Feed):

    def get_description(self):
        tree = fetch(self.link)
        self.title = tree.css('title::text').get()
        self.description = tree.xpath('//meta[@name="description"]/text()').get()

        data = json.loads(tree.css("#js-initialData::text").get())
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