---
name: yikecaiwan-journal-rss
overview: 为"一颗财丸"网站的"美股晨报"栏目（https://yikecaiwan.com/journal/）新增 RSS Feed 抓取节点，采用简单 HTML 解析模式。
todos:
  - id: create-spider
    content: 创建 yikecaiwan 目录和 journal.py，实现 ctx() 解析 journal 页面条目
    status: completed
  - id: add-route
    content: 在 main.py 末尾追加 /yikecaiwan/journal 路由
    status: completed
    dependencies:
      - create-spider
  - id: update-status
    content: 在 status.html 的 feeds 数组中追加 Yikecaiwan Journal 条目
    status: completed
    dependencies:
      - add-route
  - id: cleanup-tmp
    content: 清理临时文件 tmp_yikecaiwan.html
    status: completed
---

## 用户需求

为「一颗财丸」(yikecaiwan.com) 的「丸子早上看美股」栏目 (https://yikecaiwan.com/journal/) 新增 RSS 订阅节点。该站点无内置 RSS Feed，需通过 HTML 解析生成 Atom Feed。

## 核心功能

- 抓取 /journal/ 页面，提取所有每日美股晨报条目
- 解析 4 种格式变体（标准、P包裹、纯文本无链接、仅链接无描述）
- 以日期为标题、摘要为描述生成 Atom Feed，按日期倒序排列
- 支持项目已有的 `?include_title` / `?exclude_title` / `?limit` 过滤参数

## 技术栈

- Python 3.x + Flask（复用现有框架）
- BeautifulSoup + `rsshub.utils.fetch()`（项目已有工具）
- Jinja2 渲染 `main/atom.xml` 模板

## 实现方案

### 抓取策略

简单 HTML 解析模式（参考 `zaobao/realtime.py`）。目标站是 VitePress SSR 静态页面，所有数据已在 HTML 中，无需 JavaScript 执行。

### HTML 解析策略

页面结构：`div.vp-doc._journal_ > h2(周分组) + ul > li`，选择器 `.vp-doc._journal_ ul li` 提取所有条目。

**4 种格式统一处理**：

1. **标准格式** `<li><a href="/journal/DATE">DATE</a><br>DESC</li>` — 最常见
2. **P 包裹** `<li><p><a>DATE</a><br>DESC</p></li>` — 在 li 内递归查找 a
3. **纯文本无链接** `<li>DATE DESC</li>` — 正则 `\d{4}-\d{2}-\d{2}` 匹配日期
4. **仅链接无描述** `<li><a>DATE</a></li>` — 早期旧文章

统一方法：在 li 内查找 `<a href="/journal/...">`（含 p 内），提取 href 和日期文本；描述通过 `li.get_text()` 整体获取再剔除日期部分。

### 关键决策

- **不抓取详情页**：列表页摘要已足够 RSS 阅读器使用，避免对目标站造成过多请求
- **pubDate 用日期**：从链接中提取 `YYYY-MM-DD`，通过 `datetime.strptime` 转为 RFC 2822
- **默认返回全部条目**：约200+条，由 `?limit=N` 参数按需控制

## 文件清单

```
d:/prj/RSSHub-python/
├── rsshub/
│   ├── spiders/
│   │   └── yikecaiwan/
│   │       ├── __init__.py          # [NEW] 空文件
│   │       └── journal.py           # [NEW] Spider 实现，导出 ctx()
│   ├── blueprints/
│   │   └── main.py                  # [MODIFY] 末尾追加路由
│   └── templates/
│       └── main/
│           └── status.html          # [MODIFY] feeds 数组追加条目
└── tmp_yikecaiwan.html              # [DELETE] 临时分析文件
```

## 实现细节

### journal.py 核心结构

`parse_item(li)` — 解析单个 `<li>` 为条目字典：

1. 在 li 内递归查找 `<a href="/journal/...">`（包括 `<p>` 内）
2. 找到 `<a>`：提取 href 拼完整 URL → link，取文本 → 日期/标题
3. 描述提取：`li.get_text(separator=' ', strip=True)` 整体获取，移除日期部分后 trim
4. 未找到 `<a>`：正则匹配日期 `\d{4}-\d{2}-\d{2}`，剩余为描述，link 指向 `/journal/`
5. 处理 `\xa0` 空白字符

`ctx()` — 主入口：

- `fetch('https://yikecaiwan.com/journal/', headers=DEFAULT_HEADERS)` 获取页面
- `tree.select('.vp-doc._journal_ ul li')` 选择条目列表
- 过滤空 li 和仅空白 li
- `map(parse_item, lis)` 转条目列表
- 按日期倒序排列
- 返回 `{title, link, description, author, items}`

### main.py 路由

在文件末尾（第 484 行后）追加：

```python
@bp.route('/yikecaiwan/journal')
def yikecaiwan_journal():
    from rsshub.spiders.yikecaiwan.journal import ctx
    return render_template('main/atom.xml', **filter_content(ctx()))
```

### status.html feeds 数组

在 `YFChuhai Express` 条目后（第 64 行后），按字母序插入：

```javascript
{ name: 'Yikecaiwan Journal', route: '/yikecaiwan/journal' },
```