## 目标
为 yikecaiwan.com（VitePress 静态站，无原生 RSS）新增 `/yikecaiwan/weekly` 端点（抓全文），并补全已存在但为空壳的 `/yikecaiwan/journal` 端点（当前访问会 500）。

## 网站调研结论
- VitePress SSG，侧边栏链接直接输出在 HTML 中，`requests + BeautifulSoup` 即可，无需 Playwright。
- `/weekly/` 侧边栏列出全部周报（当前 9 期）：`"2026年30周(7.27-7.31)" → /weekly/2026-W30`。
- `/journal/` 为按周分组的每日条目列表，链接形如 `/journal/YYYY-MM-DD`。
- 文章正文在 `.vp-doc` 容器内（VitePress 约定），页面较大。

## 改动文件（4 个）

### 1. 新建 `rsshub/spiders/yikecaiwan/weekly.py`
- `fetch('https://yikecaiwan.com/weekly/')`，遍历所有 `a[href]`，用正则 `/weekly/(\d{4})-W(\d{2})(\.html)?/?` 匹配周报链接，去重后按 (年, 周) 降序排列。
- 每项再请求文章页提取全文：`select_one('.vp-doc')`（fallback `main`/`article`），将其中 `img[src]`、`a[href]` 用 `urljoin` 转绝对地址，`str(node)` 作为 `description`；单篇抓取失败时降级为标题文本，不影响整体。
- `pubDate`：正则从标题提取日期区间 `(7.27-7.31)`，取结束日（处理 12月→1月跨年）；解析失败时用 ISO 周号推算周五日期兜底。
- 输出 HTML 前做 XML 净化（参考已修改的 `mp/gh.py` 的做法）：剔除 XML 非法控制字符、转义 `]]>`，保证 CDATA/Atom 输出合法。
- `ctx()` 返回标准结构：title=「一颗财丸 - 周报」、items 含 title/link/description/pubDate/author。

### 2. 填充 `rsshub/spiders/yikecaiwan/journal.py`（现为空文件）
- 解析 `/journal/` 列表页，正则 `/journal/(\d{4}-\d{2}-\d{2})` 匹配每日条目；title = 「丸子早上看美股 {日期}」，pubDate = 链接中的日期，description 同 title（条目量大，不做全文抓取），按日期降序。
- 兜底：若列表页解析为空，改用 `sitemap.xml` 中的 `/journal/` URL 作为条目来源。

### 3. `rsshub/blueprints/main.py`
- 在文件末尾现有 `/yikecaiwan/journal` 路由旁新增：
  ```python
  @bp.route('/yikecaiwan/weekly')
  @swr_cache(timeout=3600)   # 全文抓取较慢，SWR 先返回旧数据后台刷新
  def yikecaiwan_weekly():
      from rsshub.spiders.yikecaiwan.weekly import ctx
      return render_template('main/atom.xml', **filter_content(ctx()))
  ```
- 给现有 journal 路由补上 `@cache.cached(timeout=3600)`（路由体不变，修掉空 spider 导致的 500）。

### 4. `rsshub/templates/main/feeds.html`
- 新增「一颗财丸」文档卡片，说明 `/yikecaiwan/weekly` 与 `/yikecaiwan/journal` 两条路由。

## 验证
1. `uv run python -c "from rsshub.spiders.yikecaiwan.weekly import ctx; print(ctx()['items'][0])"` 等直接调用两个 `ctx()`，确认解析出条目、pubDate 正确、正文非空。
2. 本地起服务（`uv run python main.py`）后访问 `/yikecaiwan/weekly` 与 `/yikecaiwan/journal`，确认返回合法 Atom XML、无 500。
3. `uv run python -m unittest discover tests` 确认现有测试不受影响。
4. 不提交 commit（除非你要求）。