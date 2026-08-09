---
name: yikecaiwan-sitemap-rss
overview: 基于 sitemap.xml 为 yikecaiwan.com 生成全站 RSS Feed，包含 journal 日报、weekly 周报和所有 wiki 静态文章。
todos:
  - id: create-sitemap-spider
    content: 创建 sitemap.py，实现 sitemap.xml 解析和 URL 分类生成
    status: completed
  - id: recreate-journal
    content: 重建 journal.py（当前内容为空），恢复日报 RSS 功能
    status: completed
  - id: add-sitemap-route
    content: 在 main.py 追加 /yikecaiwan/sitemap 路由
    status: completed
    dependencies:
      - create-sitemap-spider
  - id: update-status-sitemap
    content: 在 status.html 的 feeds 数组追加 Yikecaiwan Sitemap 条目
    status: completed
    dependencies:
      - add-sitemap-route
---

## 用户需求

基于 yikecaiwan.com 的 sitemap.xml 生成全站 RSS Feed，包含 sitemap 中所有 ~460 个 URL。

## 核心功能

- 解析 sitemap.xml，提取所有 `<loc>` 中的 URL
- 按内容类型分类：journal 日报（~200条）、weekly 周报（~9条）、wiki 静态文章（~250条）
- journal 和 weekly 从 URL 提取日期作为 pubDate，按日期降序排列在前
- wiki 文章无日期信息，按 URL 字母序排列在后
- 每条 item 的 title 由 URL 路径推导（如 `/bankcard/bochk` → "bankcard / bochk"），link 为原始 URL
- 支持 `?limit=N` 截断（默认返回全部 ~460 条）

## 技术栈

- Python 3.x + Flask（复用现有框架）
- BeautifulSoup（`html.parser` 解析 sitemap XML，与项目 `fetch()` 一致）
- `rsshub.utils.fetch()` + `DEFAULT_HEADERS`

## 实现方案

### 抓取策略

一次性请求 `https://yikecaiwan.com/sitemap.xml`，解析 `<loc>` 内容。**不抓取各详情页**（~460 次请求不可行），title 完全由 URL 推导。

### URL 分类与标题生成

| 类型 | URL 模式 | 标题格式 | pubDate |
| --- | --- | --- | --- |
| journal | `/journal/YYYY-MM-DD` | `日报 YYYY-MM-DD` | 从URL提取 |
| weekly | `/weekly/2026-Wxx` | `周报 2026-Wxx` | 从URL提取（用周起始日） |
| wiki | 其他所有 | `section / slug` | 无 |


**wiki 标题生成规则**：

- 去掉首页 `/`、索引页 `/section/`
- 路径按 `/` 分段，用 ` / ` 连接
- 如 `/bankcard/bochk` → `bankcard / bochk`
- 如 `/insurance/premium-financing-compare` → `insurance / premium financing compare`（连字符替换为空格）

### 排序策略

1. journal + weekly：按日期降序（最新在前）
2. wiki：按 URL 字母序升序
3. 拼接：有日期的在前，无日期的在后

### 性能考量

- 单次 HTTP 请求，O(n) 解析 ~460 条，瞬时完成
- 可加 SWR 缓存减少对目标站请求频率

## 实现细节

### 文件清单

```
d:/prj/RSSHub-python/
├── rsshub/
│   ├── spiders/
│   │   └── yikecaiwan/
│   │       └── sitemap.py          # [NEW] Sitemap spider
│   ├── blueprints/
│   │   └── main.py                 # [MODIFY] 追加 /yikecaiwan/sitemap 路由
│   └── templates/
│       └── main/
│           └── status.html         # [MODIFY] feeds 数组追加条目
```

### sitemap.py 核心结构

**`parse_sitemap(tree)`** — 解析 BeautifulSoup 对象：

1. `tree.select('url loc')` 提取所有 `<loc>` 元素
2. 遍历，对每个 URL 调用 `classify_url(url)` 分类
3. 分别收集到 `dated_items` 和 `wiki_items` 列表

**`classify_url(url)`** — 返回 `(type, title, pubDate)`：

- `type` 为 `'journal'` / `'weekly'` / `'wiki'`
- journal/ weekly 提取日期和标题
- wiki 生成路径标题

**`ctx()`** — 主入口：

- fetch sitemap，解析出 dated + wiki 两类 items
- 合并后返回标准字典

### 路由

```python
@bp.route('/yikecaiwan/sitemap')
def yikecaiwan_sitemap():
    from rsshub.spiders.yikecaiwan.sitemap import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))
```

### status.html

在 `Yikecaiwan Journal` 后追加：

```javascript
{ name: 'Yikecaiwan Sitemap', route: '/yikecaiwan/sitemap' },
```