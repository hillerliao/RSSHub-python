# RSSHub Python

> 🍰 Everything can be RSS

RSSHub Python is a lightweight, extensible RSS generator. It is a Python-based implementation of the [original RSSHub](https://github.com/DIYgod/RSSHub) philosophy: bringing RSS feeds to everything.

**Demo**: [https://pyrsshub.vercel.app](https://pyrsshub.vercel.app)

---

## ✨ Key Features

- **Versatile Source Support**: Generate RSS from CSV, TSV, TXT, PDF, EPUB, MOBI, and even raw HTML.
- **Intelligent Extraction**: Built-in readability engine to extract clean content from web pages and formatted documents.
- **Playwright Powered**: Seamlessly handles dynamic, JavaScript-heavy websites using modern browser automation.
- **Smart Caching**: Implements Stale-While-Revalidate (SWR) strategies to balance performance and freshness.
- **Hugging Face Integration**: Turn datasets on Hugging Face into fresh RSS feeds.
- **Anki Integration**: Sync your due cards as an RSS feed for mobile review.

---

## 🚀 Quick Start

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

```bash
git clone https://github.com/alphardex/RSSHub-python
cd RSSHub-python
uv sync
uv run flask run
```

> **Note**: For full features (Playwright, PDF processing, etc.), use `pip install -r requirements-full.txt` instead of the default `requirements.txt`.

---

## 🛠 Advanced Features

### Dynamic Source Discovery (`/randomline`)
Extract random content blocks from various file formats.
- Supports: `CSV`, `TSV`, `TXT`, `PDF`, `EPUB`, `MOBI`, and Web URLs.
- Features: Automatic paragraph joining for PDFs and readability extraction for web pages.
- Parameters:
  - `url`: Custom file URL (supports CSV/TXT/PDF/EPUB/MOBI or web pages)
  - `title_col`: Column index for title (0-based, default: 0)
  - `delimiter`: Separator type (`tab`, `newline`, `double_newline`, `triple_newline`, etc.)
  - `min_length`: Minimum title length requirement
  - `include_context`: Include previous and next lines in description when set to `true`

### Proxy Readability (`/proxy/readability`)
A dedicated endpoint to extract clean text from any URL, stripping away ads and navigation.

### Universal Filtering
Filter any feed using URL parameters:
- `include_title` / `include_description`: Case-insensitive keyword matching (supports `|` for OR).
- `exclude_title` / `exclude_description`: Remove unwanted content.
- `limit`: Control the number of items returned.

---

## ☁️ Deployment

### Docker (Recommended)
```bash
docker run -d \
  --name pyrsshub \
  -p 5000:5000 \
  --restart unless-stopped \
  --shm-size=512mb \
  hillerliao/pyrsshub:latest
```

### Cloud Platforms
- **Vercel**: [![Deploy with Vercel](https://vercel.app/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fhillerliao%2Frsshub-python)
  > **Note**: The project is pre-configured for Vercel Lite Mode via `vercel.json`. It uses `requirements-lite.txt` to avoid the 250MB size limit.
  > Advanced features like Playwright and PDF parsing are disabled in Lite Mode.

- **Zeabur**: Supports both Git integration and pre-built Docker images.

---

## 🤝 Contributing

We welcome new spiders!
1. **Spider**: Create a script in `/rsshub/spiders/your_spider/`.
2. **Route**: Add the endpoint definition in `/rsshub/blueprints/main.py`.
3. **Docs**: Document your new feed in `/rsshub/templates/main/feeds.html`.

---

## 💬 Community

- **Discord**: [Join our server](https://discord.gg/4BZBZuyx7p)
- **Contribution Guide**: Check our [crawler tutorial](https://juejin.cn/post/6953881777756700709) (Chinese).

---
*Actually writing crawlers in Python is more convenient than JS :p*
