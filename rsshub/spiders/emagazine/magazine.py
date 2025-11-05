import json
import requests
import arrow
from rsshub.utils import DEFAULT_HEADERS
from bs4 import BeautifulSoup

domain = 'https://emagazine.link'

def parse(entry):
    """解析单本电子书数据"""
    item = {}
    item['title'] = entry.find('title').text if entry.find('title') else 'No Title'
    
    # 获取下载链接 - 优先寻找 EPUB 格式的链接
    epub_link = None
    
    # 查找所有下载链接
    acquisition_links = entry.find_all('link', rel='http://opds-spec.org/acquisition')
    for link in acquisition_links:
        href = link.get('href', '')
        # 如果链接以 /epub/ 结尾，则使用这个链接
        if href.endswith('/epub/'):
            epub_link = domain + href
            break
        # 或者如果链接包含 epub 关键字
        elif 'epub' in href.lower():
            epub_link = domain + href
    
    # 如果没找到 EPUB 链接，使用第一个下载链接并修改为 /epub/ 结尾
    if not epub_link and acquisition_links:
        first_link = acquisition_links[0]
        href = first_link.get('href', '')
        # 移除路径中的文件名，只保留目录部分，然后添加 /epub/
        if '/' in href:
            path_parts = href.split('/')
            # 保留路径的主干部分
            base_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else href
            epub_link = domain + base_path + '/epub/'
        else:
            epub_link = domain + '/epub/'
    
    item['link'] = epub_link if epub_link else ''
    
    # 获取描述
    summary = entry.find('summary')
    item['description'] = summary.text if summary else ''
    
    # 处理发布时间
    updated = entry.find('updated')
    if updated:
        item['pubDate'] = arrow.get(updated.text).isoformat()
    else:
        item['pubDate'] = arrow.now().isoformat()
    
    # 获取作者
    author = entry.find('author')
    if author and author.find('name'):
        item['author'] = author.find('name').text
    else:
        item['author'] = 'EMagazine'
    
    # 获取封面图片
    image_link = entry.find('link', rel='http://opds-spec.org/image')
    if image_link:
        item['image'] = domain + image_link.get('href', '')
    
    return item

def ctx(category=''):
    """主函数 - 获取电子书列表并生成RSS内容"""
    try:
        # 构建请求URL
        url = f'{domain}/opds/new'
        
        # 设置请求头
        headers = DEFAULT_HEADERS.copy()
        headers.update({
            'User-Agent': 'EReader/273 CFNetwork/3826.600.41 Darwin/24.6.0',
            'Accept': 'application/atom+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cookie': 'session=eyJ2aWV3Ijp7fX0.aQlNcA.7CzaBeAuen_fNVXAzT-otqJCnI8'
        })
        
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        
        # 解析XML响应
        soup = BeautifulSoup(response.content, 'xml')
        
        # 提取所有entry条目
        entries = soup.find_all('entry')
        
        # 处理每本电子书
        items = []
        for entry in entries:
            try:
                parsed_item = parse(entry)
                items.append(parsed_item)
            except Exception as e:
                continue
        
        # 按发布时间排序（最新的在前）
        items.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
        
        # 返回RSS结构
        return {
            'title': 'EMagazine - 最新电子书',
            'link': f'{domain}/opds/new',
            'description': 'EMagazine 最新电子书资源，包含各类杂志和期刊',
            'author': 'emagazine.link',
            'items': items
        }
        
    except requests.RequestException as e:
        return {
            'title': 'EMagazine - 最新电子书',
            'link': f'{domain}/opds/new',
            'description': 'EMagazine 最新电子书资源 - 请求失败',
            'author': 'emagazine.link',
            'items': []
        }
    except Exception as e:
        return {
            'title': 'EMagazine - 最新电子书',
            'link': f'{domain}/opds/new',
            'description': 'EMagazine 最新电子书资源 - 解析失败',
            'author': 'emagazine.link',
            'items': []
        }
