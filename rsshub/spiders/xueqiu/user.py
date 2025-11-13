import re
import time
import random
import arrow
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def setup_chrome_options():
    """WSL/Linux 下稳定的 ChromeOptions 配置"""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')  # 无头模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    )
    return options


def get_user_statuses(user_id):
    """获取用户动态，并从页面源码提取 screen_name 和 description"""
    try:
        options = setup_chrome_options()
        all_posts = []
        screen_name = f'用户{user_id}'
        description = '雪球用户'
        with uc.Chrome(options=options) as driver:
            driver.set_window_size(1920, 1080)
            url = f"https://xueqiu.com/u/{user_id}"
            driver.get(url)
            time.sleep(5)
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "timeline__item")))
            time.sleep(3)
            for i in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
            soup = BeautifulSoup(driver.page_source, 'lxml')
            # 提取昵称和简介
            info_div = soup.select_one('.profiles__hd__info')
            if info_div:
                h2_tag = info_div.find('h2')
                p_tag = info_div.find('p')
                if h2_tag:
                    screen_name = h2_tag.get_text(strip=True)
                if p_tag:
                    description = p_tag.get_text(strip=True)
            timeline_items = soup.find_all('article', class_='timeline__item')
            for item in timeline_items[:5]:
                content_element = item.select_one('.timeline__item__content .content--description > div')
                content = content_element.get_text(strip=True, separator='\n') if content_element else "N/A"
                time_element = item.find('a', class_='date-and-source')
                timestamp = time_element.get_text(strip=True) if time_element else "N/A"
                link = "https://xueqiu.com" + time_element['href'] if time_element and time_element.has_attr('href') else f"https://xueqiu.com/u/{user_id}"
                all_posts.append({
                    'content': content,
                    'timestamp': timestamp,
                    'link': link
                })
        return {
            'screen_name': screen_name,
            'description': description,
            'posts': all_posts
        }
    except Exception as e:
        return {
            'screen_name': f'用户{user_id}',
            'description': '雪球用户',
            'posts': []
        }

def parse_status(status, user_id, screen_name=None):
    """解析单条动态数据"""
    item = {}
    text = re.sub('<[^<]+?>', '', status.get('content', '雪球动态'))
    item['title'] = text[:100] + '...' if len(text) > 50 else text
    item['description'] = text
    item['link'] = status.get('link', f'https://xueqiu.com/u/{user_id}')
    item['pubDate'] = arrow.now().isoformat()
    item['author'] = screen_name if screen_name else f'用户{user_id}'
    return item

def ctx(user_id=None):
    """主函数"""
    if not user_id:
        return {
            'title': '雪球用户动态',
            'link': 'https://xueqiu.com/',
            'description': '雪球用户最新动态',
            'items': []
        }
    result = get_user_statuses(user_id)
    items = [parse_status(s, user_id, result['screen_name']) for s in result['posts']]
    return {
        'title': f"{result['screen_name']} - 雪球动态",
        'link': f"https://xueqiu.com/u/{user_id}",
        'description': f"{result['description']}",
        'author': 'hillerliao',
        'items': items 
    }
