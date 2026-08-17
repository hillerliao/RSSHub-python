import asyncio
import threading

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class BrowserPool:
    """在后台线程的常驻事件循环里维护一个可复用的 Chromium 实例。

    Playwright 的 browser 对象绑定在创建它的事件循环上，而 Flask 请求里
    每次 asyncio.run() 都会新建循环，导致浏览器无法复用。因此这里用一个
    永久运行的后台事件循环承载 browser，每次请求只新建 Page。
    浏览器空闲超过 idle_timeout 秒会自动关闭以释放内存，下次请求再重新拉起。
    """

    def __init__(self, idle_timeout=30 * 60):
        self.idle_timeout = idle_timeout
        self._lock = threading.Lock()
        self._loop = None
        self._thread = None
        self._playwright = None
        self._browser = None
        self._last_used = 0.0

    def _ensure_loop(self):
        with self._lock:
            if self._loop is not None and not self._loop.is_closed():
                return
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._loop.run_forever,
                name='playwright-browser-loop',
                daemon=True,
            )
            self._thread.start()
            self._loop.call_soon_threadsafe(self._schedule_idle_check)

    def _schedule_idle_check(self):
        # 运行在后台事件循环内：每 60 秒检查一次是否空闲超时
        if self._browser is not None and self._browser.is_connected():
            idle = self._loop.time() - self._last_used
            if idle >= self.idle_timeout:
                asyncio.ensure_future(self._close_idle_browser())
                return
        self._loop.call_later(60, self._schedule_idle_check)

    async def _close_idle_browser(self):
        if self._browser is not None:
            browser, self._browser = self._browser, None
            await browser.close()

    async def _get_browser(self):
        # 浏览器崩溃或未启动时自动（重新）拉起
        if self._browser is None or not self._browser.is_connected():
            await self._restart_playwright()
            self._schedule_idle_check()
        return self._browser

    async def _restart_playwright(self):
        # 彻底丢弃旧 browser + playwright 句柄，避免"内核已换但 client 仍持有
        # 旧上下文 id"导致的 Protocol error。下次 _get_browser 会重新启动。
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self._playwright = await async_playwright().start()
        # 优先使用系统 Chrome/Edge：自带 Chromium 容易被 Cloudflare 等反爬拦截
        # （例如 economist.com 直接返回 403 挑战页），系统浏览器指纹更真实。
        launch_kwargs = dict(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage'],
        )
        self._browser = None
        for channel in ('chrome', 'msedge', None):
            try:
                if channel:
                    self._browser = await self._playwright.chromium.launch(channel=channel, **launch_kwargs)
                else:
                    self._browser = await self._playwright.chromium.launch(**launch_kwargs)
                break
            except Exception as e:
                print(f'[browser] launch channel={channel} failed: {e}')
        if self._browser is None:
            raise RuntimeError('Failed to launch any Chromium browser')
        # 等待浏览器 CDP 连接就绪，避免 launch 后立即 new_page 触发上下文错乱
        for _ in range(20):
            if self._browser.is_connected():
                try:
                    await self._browser.contexts  # 触发一次状态探测
                    return
                except Exception:
                    pass
            await asyncio.sleep(0.1)

    def run(self, page_task, timeout=None):
        """在常驻浏览器上新开一个页面执行 page_task(page)，同步返回结果。

        page_task: async 可调用对象，签名为 (page) -> result，页面用完后自动关闭。
        若浏览器状态异常（崩溃/上下文句柄错乱），自动彻底重启 Playwright 后重试一次。
        """
        self._ensure_loop()

        # 每次请求使用独立 context 并携带真实 UA/视口。注意：
        # page.set_extra_http_headers 设置的 User-Agent 在 Playwright 中不生效，
        # 只能通过 context 的 user_agent 参数指定，否则会带 HeadlessChrome 标识
        # 被 Cloudflare 等反爬拦截（例如 economist.com 返回 403 挑战页）。
        context_kwargs = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
        }

        async def wrapper():
            browser = await self._get_browser()
            self._last_used = self._loop.time()
            try:
                context = await browser.new_context(**context_kwargs)
                page = await context.new_page()
            except Exception as e:
                # 上下文句柄错乱时彻底重建 Playwright，再开新 context/page
                if 'TargetClosedError' in type(e).__name__ or 'Protocol error' in str(e):
                    await self._restart_playwright()
                    browser = self._browser
                    context = await browser.new_context(**context_kwargs)
                    page = await context.new_page()
                else:
                    raise
            try:
                return await page_task(page)
            finally:
                try:
                    await context.close()
                except Exception:
                    pass
                self._last_used = self._loop.time()

        future = asyncio.run_coroutine_threadsafe(wrapper(), self._loop)
        return future.result(timeout=timeout)


browser_pool = BrowserPool() if HAS_PLAYWRIGHT else None
