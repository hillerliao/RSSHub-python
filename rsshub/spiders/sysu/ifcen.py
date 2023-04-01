from rsshub.utils import fetch_by_puppeteer
import asyncio

domain = 'https://ifcen.sysu.edu.cn/'


def parse(selector):

    items = list()

    # 公告通知
    xpath = '//div[@id="news-2"]/ul//a'
    announces = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    announces = ['公告通知 | ' + i for i in announces]
    for i in range(len(announces)):
        item = dict()
        item['title'] = announces[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 学院新闻
    xpath = '//*[@id="news-1"]/ul/li/a'
    news = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    for i in range(len(news)):
        item = dict()
        item['title'] = news[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 人才工作
    xpath = '//*[@id="notice-1"]/div//a'
    works = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    works = ['人才工作 | ' + i for i in works]
    for i in range(len(works)):
        item = dict()
        item['title'] = works[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 本科生教育
    xpath = '//*[@id="notice-2"]/div//a'
    ues = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    ues = ['本科生教育 | ' + i for i in ues]
    for i in range(len(ues)):
        item = dict()
        item['title'] = ues[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 研究生教育
    xpath = '//*[@id="notice-3"]/div//a'
    pgs = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    pgs = ['研究生教育 | ' + i for i in pgs]
    for i in range(len(pgs)):
        item = dict()
        item['title'] = pgs[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 科研信息
    xpath = '//*[@id="notice-4"]/div//a'
    research = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    research = ['科研信息 | ' + i for i in research]
    for i in range(len(research)):
        item = dict()
        item['title'] = research[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 学工信息
    xpath = '//*[@id="notice-5"]/div//a'
    students = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    students = ['学工信息 | ' + i for i in students]
    for i in range(len(students)):
        item = dict()
        item['title'] = students[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 党建通知
    xpath = '//*[@id="notice-6"]/div//a'
    party = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    party = ['党建通知 | ' + i for i in party]
    for i in range(len(party)):
        item = dict()
        item['title'] = party[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 工会工作
    xpath = '//*[@id="notice-7"]/div//a'
    union = selector.xpath(xpath + '/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    union = ['工会工作 | ' + i for i in union]
    for i in range(len(union)):
        item = dict()
        item['title'] = union[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    xpath = '//*[@id="event-1"]/li//a'
    report = selector.xpath(xpath + '/text()').getall()
    author = selector.xpath('//*[@id="event-1"]/li//span[@class="content"]/text()').getall()
    urls = selector.xpath(xpath + '/@href').getall()
    urls = [domain + i for i in urls]
    for i in range(len(report)) :
        report[i] = report[i] + author[i]
    report = ['学术报告 | ' + i for i in report]
    for i in range(len(report)):
        item = dict()
        item['title'] = report[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    return items

def ctx(category=''):
    tree = asyncio.run(fetch_by_puppeteer(domain))
    return {
        'title': '中山大学中法核官网信息',
        'link': domain,
        'description': '中山大学中法核官网通知公告',
        'author': 'echo',
        'items': parse(tree)
    }