import asyncio
from urllib.parse import unquote
from playwright.async_api import async_playwright


async def get_html(url):
    """使用 Playwright 获取网页 HTML 源代码"""
    # 验证URL格式
    if not url.startswith(('http://', 'https://')):
        raise ValueError("只支持 HTTP 和 HTTPS 协议")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        
        try:
            # 设置反检测
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
            
            # 设置超时时间
            page.set_default_timeout(30000)  # 30 seconds
            
            await page.goto(url, wait_until='domcontentloaded')
            
            # 等待页面加载完成
            await asyncio.sleep(2)
            
            # 获取最终HTML
            content = await page.content()
            
            await browser.close()
            return content
            
        except Exception as e:
            await browser.close()
            raise Exception(f"获取网页失败: {str(e)}")


def ctx(url):
    """主函数 - 获取网页HTML"""
    try:
        # 解码URL
        decoded_url = unquote(url)
        html_content = asyncio.run(get_html(decoded_url))
        return html_content
    except Exception as e:
        raise Exception(f"抓取失败: {str(e)}")