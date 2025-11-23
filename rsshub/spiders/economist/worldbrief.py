import re
import json
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

domain = 'https://www.economist.com'

 

def parse_news(gobbet):
    """
    生成单条 news 的新闻内容，提取标题和正文。
    """   
    title = re.sub(r'<[^>]+>', '', gobbet.strip())
    item = {
        'title': title,  
        'description': gobbet,   # 简单设置正文为描述
        'link': f"{domain}/the-world-in-brief?from={title[:100]}"  # 生成链接
    }
    return item

def get_content_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url)
            # Wait for content to load
            page.wait_for_selector("main", timeout=60000)
            # Scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(5)
            content = page.content()
            return content
        except Exception as e:
            print(f"Error fetching content: {e}")
            return None
        finally:
            browser.close()

def ctx(category=''):
    """
    解析 JSON 数据，提取所有brief news的内容。
    """
    url = f"{domain}/the-world-in-brief"
    html = get_content_with_playwright(url)
    
    if not html:
        raise ValueError("Failed to retrieve content from The Economist")

    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', id="__NEXT_DATA__", type="application/json")

    if not script_tag:
        # Fallback if __NEXT_DATA__ is not found (e.g. if page structure changed significantly)
        # For now, we'll stick to the original logic but raise a clearer error
        raise ValueError("Could not find __NEXT_DATA__ script tag in the rendered page.")

    # Load JSON content
    data = json.loads(script_tag.string)

    news_list = data.get('props', {}).get('pageProps', {}).get('content', {}).get('gobbets', [])

    # 使用 parse_gobbet 解析每一条新闻
    items = [parse_news(news) for news in news_list]

    return {
        'title': 'World Brief - Economist',
        'link': url,
        'description': 'The world in brief: Catch up quickly on the global stories that matter',
        'author': 'hillerliao',
        'items': items
    }
