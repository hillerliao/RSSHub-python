import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import time
import random
from rsshub.utils import DEFAULT_HEADERS

def get_random_content(url, content_type):
    """从randomword.com获取随机内容，具有更强的反检测能力"""
    
    # 多个真实的浏览器头部配置
    header_configs = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        },
        DEFAULT_HEADERS  # 保留原始配置作为最后的备用选项
    ]
    
    # 随机打乱headers顺序，增加不可预测性
    random.shuffle(header_configs)
    
    for attempt, headers in enumerate(header_configs):
        try:
            # 添加随机延迟，避免被识别为机器人
            if attempt > 0:
                delay = random.uniform(1, 4)
                time.sleep(delay)
                print(f"[DEBUG] 尝试 {attempt + 1}, 延迟 {delay:.2f}s")
            
            # 使用session来保持连接
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, timeout=20)
            print(f"[DEBUG] 尝试 {attempt + 1}/{len(header_configs)}: 状态码 {response.status_code}")
            
            # 如果状态码不是200，尝试下一个headers
            if response.status_code != 200:
                print(f"[DEBUG] 状态码 {response.status_code}，尝试下一个headers")
                session.close()
                continue
                
            response.raise_for_status()
            
            # 检查响应内容是否为空或异常
            if len(response.text.strip()) == 0:
                print("[DEBUG] 响应内容为空，尝试下一个headers")
                session.close()
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据content_type查找不同的元素
            if content_type == 'paragraph':
                # 查找包含段落的div
                content_div = soup.find('div', {'id': 'random_word_definition'})
                if not content_div:
                    # 备用方案：查找其他可能的段落元素
                    content_div = soup.find('div', {'id': 'random_word'})
            else:
                # 其他类型使用默认的div查找
                content_div = soup.find('div', {'id': 'random_word'})
            
            if content_div:
                content = content_div.get_text(strip=True)
                if content and len(content) > 5:  # 确保内容有意义
                    session.close()
                    return content
            
            # 备用方案：查找其他可能的元素
            content_elements = soup.find_all('div', string=True)
            for element in content_elements:
                text = element.get_text(strip=True)
                if len(text) > 20:  # 假设内容长度大于20个字符
                    session.close()
                    return text
            
            session.close()
            print(f"[DEBUG] 未找到有效内容，尝试下一个headers")
            continue
                
        except requests.exceptions.HTTPError as e:
            if 'session' in locals():
                session.close()
            
            # 如果是最后一次尝试，返回错误
            if attempt == len(header_configs) - 1:
                status = getattr(e.response, 'status_code', None)
                if status == 403:
                    return f"Error fetching {content_type}: 403 Forbidden (site blocks automated requests from this environment after {len(header_configs)} attempts)."
                return f"Error fetching {content_type}: {str(e)}"
            print(f"[DEBUG] HTTP错误: {e}, 尝试下一个headers")
            continue
        except Exception as e:
            if 'session' in locals():
                session.close()
            
            if attempt == len(header_configs) - 1:
                return f"Error fetching {content_type}: {str(e)}"
            print(f"[DEBUG] 异常: {e}, 尝试下一个headers")
            continue
    
    return f"Failed to fetch {content_type} after {len(header_configs)} attempts with different headers"

def ctx(category=''):
    """通用RSS内容生成函数"""
    # 根据类型确定URL和标题
    type_map = {
        'sentence': {
            'url': 'https://randomword.com/sentence',
            'title_prefix': 'Random Sentence',
            'feed_title': 'Random Sentence'
        },
        'question': {
            'url': 'https://randomword.com/question', 
            'title_prefix': 'Random Question',
            'feed_title': 'Random Question'
        },
        'paragraph': {
            'url': 'https://randomword.com/paragraph',
            'title_prefix': 'Random Paragraph',
            'feed_title': 'Random Paragraph'
        }
    }
    
    if category not in type_map:
        # 默认使用sentence类型
        category = 'sentence'
    
    config = type_map[category]
    content = get_random_content(config['url'], category)
    
    # 创建RSS项目
    item = {
        'title': content,
        'description': content,
        'link': config['url'],
        'pubDate': datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'author': 'RandomWord.com'
    }
    
    return {
        'title': config['feed_title'],
        'link': config['url'],
        'description': f'Random {category}s from RandomWord.com',
        'author': 'Hiller Liao',
        'items': [item]
    }