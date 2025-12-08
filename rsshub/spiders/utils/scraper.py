import asyncio
from urllib.parse import unquote, urljoin
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
            return content, url
            
        except Exception as e:
            await browser.close()
            raise Exception(f"获取网页失败: {str(e)}")


def fix_relative_paths(html_content, base_url):
    """修复HTML中的相对路径，转换为绝对路径"""
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 修复各种标签中的相对路径
    tags_and_attrs = [
        ('a', 'href'),
        ('link', 'href'),
        ('script', 'src'),
        ('img', 'src'),
        ('iframe', 'src'),
        ('source', 'src'),
        ('video', 'src'),
        ('audio', 'src'),
        ('form', 'action'),
    ]
    
    for tag_name, attr_name in tags_and_attrs:
        for element in soup.find_all(tag_name):
            if element.has_attr(attr_name):
                attr_value = element[attr_name]
                # 修复相对路径
                if attr_value.startswith(('/', './')):
                    # 跳过锚点和JavaScript
                    if not attr_value.startswith('#') and not attr_value.startswith('javascript:'):
                        element[attr_name] = urljoin(base_url, attr_value)
                # 修复协议相对路径 (//example.com)
                elif attr_value.startswith('//'):
                    element[attr_name] = f'https:{attr_value}'
    
    # 修复内联样式中的URL
    for element in soup.find_all(style=True):
        style_content = element['style']
        # 使用正则表达式替换CSS url()中的相对路径
        def replace_css_url(match):
            url_path = match.group(1)
            if url_path.startswith(('/', './')) and not url_path.startswith('#'):
                return f'url({urljoin(base_url, url_path)})'
            return match.group(0)
        
        style_content = re.sub(r'url\([\'"]?([^\'")]+)[\'"]?\)', replace_css_url, style_content)
        element['style'] = style_content
    
    return str(soup)


def ctx(url):
    """主函数 - 获取网页HTML"""
    try:
        # 解码URL
        decoded_url = unquote(url)
        html_content, base_url = asyncio.run(get_html(decoded_url))
        
        # 修复相对路径
        fixed_html = fix_relative_paths(html_content, base_url)
        
        return fixed_html
    except Exception as e:
        raise Exception(f"抓取失败: {str(e)}")