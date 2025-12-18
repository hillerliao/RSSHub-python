from rsshub.utils import fetch_by_puppeteer
import asyncio

domain = 'https://ifcen.sysu.edu.cn/'


def parse(selector):

    items = list()

    # 公告通知
    css = '#news-2 ul a'
    links = selector.select(css)
    announces = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    announces = ['公告通知 | ' + i for i in announces]
    for i in range(len(announces)):
        item = dict()
        item['title'] = announces[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 学院新闻
    css = '#news-1 ul li a'
    links = selector.select(css)
    news = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    for i in range(len(news)):
        item = dict()
        item['title'] = news[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 人才工作
    css = '#notice-1 div a'
    links = selector.select(css)
    works = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    works = ['人才工作 | ' + i for i in works]
    for i in range(len(works)):
        item = dict()
        item['title'] = works[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 本科生教育
    css = '#notice-2 div a'
    links = selector.select(css)
    ues = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    ues = ['本科生教育 | ' + i for i in ues]
    for i in range(len(ues)):
        item = dict()
        item['title'] = ues[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 研究生教育
    css = '#notice-3 div a'
    links = selector.select(css)
    pgs = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    pgs = ['研究生教育 | ' + i for i in pgs]
    for i in range(len(pgs)):
        item = dict()
        item['title'] = pgs[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 科研信息
    css = '#notice-4 div a'
    links = selector.select(css)
    research = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    research = ['科研信息 | ' + i for i in research]
    for i in range(len(research)):
        item = dict()
        item['title'] = research[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 学工信息
    css = '#notice-5 div a'
    links = selector.select(css)
    students = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    students = ['学工信息 | ' + i for i in students]
    for i in range(len(students)):
        item = dict()
        item['title'] = students[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 党建通知
    css = '#notice-6 div a'
    links = selector.select(css)
    party = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    party = ['党建通知 | ' + i for i in party]
    for i in range(len(party)):
        item = dict()
        item['title'] = party[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    # 工会工作
    css = '#notice-7 div a'
    links = selector.select(css)
    union = [a.get_text() for a in links]
    urls = [a['href'] for a in links]
    urls = [domain + i for i in urls]
    union = ['工会工作 | ' + i for i in union]
    for i in range(len(union)):
        item = dict()
        item['title'] = union[i]
        item['description'] = "网站严格反爬，请进入网站查看具体内容"
        item['link'] = urls[i]
        items.append(item)

    css = '#event-1 li a'
    links = selector.select(css)
    report = [a.get_text() for a in links]
    author_spans = selector.select('#event-1 li span.content')
    author = [span.get_text() for span in author_spans]
    urls = [a['href'] for a in links]
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