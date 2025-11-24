import re
from flask import Response
import requests
from parsel import Selector

DEFAULT_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}


class XMLResponse(Response):
    def __init__(self, response, **kwargs):
        if 'mimetype' not in kwargs and 'contenttype' not in kwargs:
            if response.startswith('<?xml'):
                kwargs['mimetype'] = 'application/xml'
        return super().__init__(response, **kwargs)


def fetch(url: str, headers: dict=DEFAULT_HEADERS, proxies: dict=None):
    try:
        res = requests.get(url, headers=headers, proxies=proxies)
        res.raise_for_status()
    except Exception as e:
        print(f'[Err] {e}')
    else:
        html = res.text
        tree = Selector(text=html)
        return tree


async def fetch_by_puppeteer(url):
    try:
        from pyppeteer import launch
    except Exception as e:
        print(f'[Err] {e}')
    else:
        browser = await launch(  # 启动浏览器
            {'args': ['--no-sandbox']},
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        page = await browser.newPage()  # 创建新页面
        await page.goto(url)  # 访问网址
        html = await page.content()  # 获取页面内容
        await browser.close()  # 关闭浏览器
        return Selector(text=html)


import re
from flask import Response
import requests
from parsel import Selector

DEFAULT_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}


class XMLResponse(Response):
    def __init__(self, response, **kwargs):
        if 'mimetype' not in kwargs and 'contenttype' not in kwargs:
            if response.startswith('<?xml'):
                kwargs['mimetype'] = 'application/xml'
        return super().__init__(response, **kwargs)


def fetch(url: str, headers: dict=DEFAULT_HEADERS, proxies: dict=None):
    try:
        res = requests.get(url, headers=headers, proxies=proxies)
        res.raise_for_status()
    except Exception as e:
        print(f'[Err] {e}')
    else:
        html = res.text
        tree = Selector(text=html)
        return tree


async def fetch_by_puppeteer(url):
    try:
        from pyppeteer import launch
    except Exception as e:
        print(f'[Err] {e}')
    else:
        browser = await launch(  # 启动浏览器
            {'args': ['--no-sandbox']},
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        page = await browser.newPage()  # 创建新页面
        await page.goto(url)  # 访问网址
        html = await page.content()  # 获取页面内容
        await browser.close()  # 关闭浏览器
        return Selector(text=html)


def filter_content(items):
    content = []
    p1 = re.compile(r'(.*)(to|will|date|schedule) (.*)results', re.IGNORECASE)
    p2 = re.compile(r'(.*)(schedule|schedules|announce|to) (.*)call', re.IGNORECASE)
    p3 = re.compile(r'(.*)release (.*)date', re.IGNORECASE)

    for item in items:
        title = item['title']
        if p1.match(title) or p2.match(title) or p3.match(title):
            content.append(item)
    return content


import functools
import threading
import hashlib
import pickle
from flask import request
from rsshub.extensions import cache
import arrow

def swr_cache(timeout=3600):
    """
    Stale-While-Revalidate Cache Decorator
    
    If cache exists:
        - Return cached data immediately
        - If cache is stale (older than timeout), trigger background refresh
    If cache missing:
        - Fetch data synchronously and cache it
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate a unique cache key based on function name and arguments
            # We use pickle to serialize args/kwargs to ensure uniqueness
            key_data = (f.__name__, args, kwargs, request.path, request.args)
            key_hash = hashlib.md5(pickle.dumps(key_data)).hexdigest()
            cache_key = f"swr_cache:{key_hash}"
            
            # Try to get data from cache
            cached_data = cache.get(cache_key)
            
            if cached_data:
                data, timestamp = cached_data
                age = arrow.now().timestamp() - timestamp
                
                if age > timeout:
                    # Cache is stale, trigger background refresh
                    print(f"[SWR] Cache stale for {request.path}, triggering background refresh")
                    threading.Thread(target=refresh_cache, args=(cache_key, f, args, kwargs)).start()
                else:
                    print(f"[SWR] Cache hit for {request.path}")
                
                return data
            
            # Cache missing, fetch synchronously
            print(f"[SWR] Cache miss for {request.path}, fetching synchronously")
            result = f(*args, **kwargs)
            # Save to cache with current timestamp. 
            # We set a very long timeout for the underlying cache because we manage staleness manually.
            cache.set(cache_key, (result, arrow.now().timestamp()), timeout=timeout * 24 * 7) 
            return result
            
        return decorated_function
    return decorator

def refresh_cache(cache_key, func, args, kwargs):
    """Background task to refresh cache"""
    try:
        print(f"[SWR] Background refreshing {cache_key}")
        # with app.app_context(): # Need app context for Flask extensions if used inside func
             # Note: This might be tricky if func relies on request context. 
             # Spiders usually don't rely on request context, but we need to be careful.
             # For now, let's assume spiders are independent.
             # Actually, we can't easily pass request context to thread.
             # Fortunately, the spiders (ctx functions) seem to take arguments explicitly 
             # and don't seem to rely on global `request` object for their core logic.
             # However, `rsshub.extensions.cache` might need app context.
             # pass
        
        # We need to import app to push context
        # from rsshub.blueprints.main import bp
        # This is circular import if we import app here.
        # Let's try to run without app context first, as cache might be bound to app globally?
        # No, Flask-Caching usually needs app context or configured cache instance.
        # But `rsshub.extensions.cache` is initialized.
        
        result = func(*args, **kwargs)
        cache.set(cache_key, (result, arrow.now().timestamp()), timeout=86400 * 7)
        print(f"[SWR] Background refresh successful for {cache_key}")
    except Exception as e:
        print(f"[SWR] Background refresh failed for {cache_key}: {e}")