import asyncio
import arrow
from bs4 import BeautifulSoup
from rsshub.spiders.utils.browser import browser_pool, HAS_PLAYWRIGHT


async def scrape_stock(page, symbol):
    """抓取雪球个股讨论页 https://xueqiu.com/S/<symbol> 的帖子流。"""
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    await page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    # 屏蔽图片/字体/CSS
    await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())

    url = f"https://xueqiu.com/S/{symbol.upper()}"
    await page.goto(url, wait_until='domcontentloaded', timeout=30000)

    # 等帖子列表容器出现（雪球页面主要用 .timeline__item）
    try:
        await page.wait_for_selector('.timeline__item', timeout=15000)
    except Exception:
        # 没有帖子也不报错，照常返回空列表
        pass

    # 滚动加载
    for _ in range(3):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

    content = await page.content()
    return content, url


def parse_posts(html, symbol):
    soup = BeautifulSoup(html, 'html.parser')
    items = []

    # 名称/描述
    title = f"{symbol.upper()} - 雪球个股讨论"
    description = f"雪球上 {symbol.upper()} 的最新讨论"

    info_div = soup.select_one('.profiles__hd__info')
    if info_div:
        h2_tag = info_div.find('h2')
        p_tag = info_div.find('p')
        if h2_tag:
            name = h2_tag.get_text(strip=True)
            title = f"{name} ({symbol.upper()}) - 雪球个股讨论"
        if p_tag:
            description = p_tag.get_text(strip=True)

    timeline_items = soup.find_all('article', class_='timeline__item')
    for item in timeline_items[:5]:
        content_element = item.select_one('.timeline__item__content .content--description > div')
        text = content_element.get_text(strip=True, separator='\n') if content_element else "N/A"
        time_element = item.find('a', class_='date-and-source')
        link = (
            "https://xueqiu.com" + time_element['href']
            if time_element and time_element.has_attr('href')
            else f"https://xueqiu.com/S/{symbol.upper()}"
        )

        item_title = text[:100] + '...' if len(text) > 50 else text
        items.append({
            'title': item_title,
            'description': text,
            'link': link,
            'pubDate': arrow.now().isoformat(),
            'author': 'xueqiu',
        })

    return {
        'title': title,
        'description': description,
        'link': f"https://xueqiu.com/S/{symbol.upper()}",
        'items': items,
    }


def ctx(symbol='TSLA'):
    """主函数：抓取雪球个股页讨论帖"""
    if not HAS_PLAYWRIGHT:
        return {
            'title': f'{symbol} - 雪球个股讨论 (Not supported on Vercel)',
            'link': f'https://xueqiu.com/S/{symbol}',
            'description': 'Playwright is not available in this environment. Please use the self-hosted version for this feed.',
            'author': 'hillerliao',
            'items': [{
                'title': 'Playwright not supported on Vercel',
                'description': 'This feed requires Playwright, which is not supported on Vercel. Please use the self-hosted scraper image.',
                'link': f'https://xueqiu.com/S/{symbol}'
            }]
        }

    symbol = (symbol or 'TSLA').upper().strip()
    try:
        html, url = browser_pool.run(lambda page: scrape_stock(page, symbol))
        result = parse_posts(html, symbol)
        result['link'] = url
    except Exception as e:
        print(f"Error fetching Xueqiu stock {symbol}: {e}")
        result = {
            'title': f'{symbol} - 雪球个股讨论',
            'link': f'https://xueqiu.com/S/{symbol}',
            'description': '雪球个股讨论',
            'items': [],
        }

    return result