import re
import json
import asyncio
from bs4 import BeautifulSoup
from rsshub.spiders.utils.browser import browser_pool, HAS_PLAYWRIGHT

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

async def get_content_with_playwright(page, url):
    await page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    # Block unnecessary resources
    await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())

    try:
        # Increase timeout to 60s and wait for domcontentloaded which is faster
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        # Wait for content to load
        await page.wait_for_selector("main", timeout=60000)
        # Scroll to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await asyncio.sleep(5)
        content = await page.content()
        return content
    except Exception as e:
        print(f"Error fetching content: {e}")
        return None

def ctx(category=''):
    """
    解析 JSON 数据，提取所有brief news的内容。
    """
    url = f"{domain}/the-world-in-brief"

    if not HAS_PLAYWRIGHT:
        return {
            'title': 'World Brief - Economist (Not supported on Vercel)',
            'link': url,
            'description': 'Playwright is not available in this environment. Please use the self-hosted version for this feed.',
            'author': 'hillerliao',
            'items': [{
                'title': 'Playwright not supported on Vercel',
                'description': 'This feed requires Playwright, which is not supported on Vercel. Please use the self-hosted scraper image.',
                'link': url
            }]
        }

    html = browser_pool.run(lambda page: get_content_with_playwright(page, url))
    
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
