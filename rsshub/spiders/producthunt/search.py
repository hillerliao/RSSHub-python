import re
import asyncio
from playwright.async_api import async_playwright
from rsshub.utils import DEFAULT_HEADERS

domain = 'https://www.producthunt.com'

async def get_search_html(keyword, period):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent=DEFAULT_HEADERS.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        )
        
        # Add init script to hide webdriver property (stealth)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        # Block images and fonts to speed up loading
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
        
        url = f'{domain}/search?q={keyword}&postedAfter={period}:days'
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5) 
            content = await page.content()
            print(f"DEBUG: Fetched HTML length: {len(content)}")
            if len(content) < 1000:
                print(f"DEBUG: Content preview: {content}")
            return content
        except Exception as e:
            print(f"Error fetching page: {e}")
            return ""
        finally:
            await browser.close()

def parse_products(html):
    print("DEBUG: Parsing products with robust heuristic...")
    items = []
    seen_slugs = set()
    
    # Heuristic: Find all "slug":"..." and look around for "name" and "tagline"
    # This handles JSON field order variations.
    slug_pattern = re.compile(r'"slug"\s*:\s*"(?P<slug>[^"]+)"')
    
    for match in slug_pattern.finditer(html):
        slug = match.group('slug')
        if slug in seen_slugs:
            continue
            
        # Define a window around the slug to search for other fields
        start = match.start()
        end = match.end()
        # Look 500 chars before and after
        search_window = html[max(0, start-500):min(len(html), end+500)]
        
        name_match = re.search(r'"name"\s*:\s*"(?P<name>[^"]+)"', search_window)
        tagline_match = re.search(r'"tagline"\s*:\s*"(?P<tagline>(?:\\.|[^"\\])*)"', search_window)
        
        if name_match:
            name = name_match.group('name')
            tagline = tagline_match.group('tagline') if tagline_match else ""
            
            # Clean up tagline escape sequences if any
            try:
                tagline = tagline.encode('utf-8').decode('unicode_escape')
            except:
                pass

            items.append({
                'title': name,
                'description': tagline,
                'link': f'{domain}/products/{slug}',
                'author': 'Product Hunt'
            })
            seen_slugs.add(slug)
    
    print(f"DEBUG: Found {len(items)} items.")
    return items

def ctx(keyword='', period=''):
    html = asyncio.run(get_search_html(keyword, period))
    items = parse_products(html)
    
    return {
        'title': f'{keyword} - Producthunt',
        'link': f'{domain}/search?q={keyword}&postedAfter={period}:days',
        'description': f'{keyword} - Producthunt',
        'author': 'hillerliao',
        'items': items
    }