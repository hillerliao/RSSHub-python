import requests
from bs4 import BeautifulSoup
import datetime
from rsshub.utils import DEFAULT_HEADERS

def get_random_content(url, content_type):
    """从randomword.com获取随机内容"""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        
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
            return content
        else:
            # 备用方案：查找其他可能的元素
            content_elements = soup.find_all('div', string=True)
            for element in content_elements:
                text = element.get_text(strip=True)
                if len(text) > 20:  # 假设内容长度大于20个字符
                    return text
            
            return f"Failed to extract {content_type} from the page"
            
    except Exception as e:
        return f"Error fetching {content_type}: {str(e)}"

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
        'author': 'Hiller Liao
        'items': [item]
    }