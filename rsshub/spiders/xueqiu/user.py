import re
import asyncio
import arrow
try:
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth_async
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
from bs4 import BeautifulSoup


async def get_user_statuses(user_id):
    """使用 Playwright 获取用户动态"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        
        # 设置反检测
        await stealth_async(page)
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Block unnecessary resources
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
        
        try:
            await page.goto(f"https://xueqiu.com/u/{user_id}", wait_until='domcontentloaded')
            await page.wait_for_selector('.timeline__item', timeout=15000)
            
            # 模拟滚动加载
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            all_posts = []
            screen_name = f'用户{user_id}'
            description = '雪球用户'
            
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
            
            await browser.close()
            return {
                'screen_name': screen_name,
                'description': description,
                'posts': all_posts
            }
            
        except Exception as e:
            await browser.close()
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
    
    if not HAS_PLAYWRIGHT:
        return {
            'title': f'用户{user_id} - 雪球动态 (Not supported on Vercel)',
            'link': f"https://xueqiu.com/u/{user_id}",
            'description': 'Playwright is not available in this environment. Please use the self-hosted version for this feed.',
            'author': 'hillerliao',
            'items': [{
                'title': 'Playwright not supported on Vercel',
                'description': 'This feed requires Playwright, which is not supported on Vercel. Please use the self-hosted scraper image.',
                'link': f"https://xueqiu.com/u/{user_id}"
            }]
        }

    result = asyncio.run(get_user_statuses(user_id))
    items = [parse_status(s, user_id, result['screen_name']) for s in result['posts']]
    return {
        'title': f"{result['screen_name']} - 雪球动态",
        'link': f"https://xueqiu.com/u/{user_id}",
        'description': f"{result['description']}",
        'author': 'hillerliao',
        'items': items 
    }
