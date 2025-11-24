# RSSHub

> 🍰 Everything can be RSS

RSSHub is a lightweight, easily extensible RSS generator that can create RSS feeds for any type of content.

This project is a Python implementation of the [original RSSHub](https://github.com/DIYgod/RSSHub).

**Actually writing crawlers in Python is more convenient than JS :p**

DEMO address: https://pyrsshub.vercel.app

## Special Features

### Anki Integration

This RSSHub instance includes integration with Anki through the AnkiConnect addon. This allows you to get an RSS feed of a random card due for review today.

To use this feature:

1. Install and run [Anki](https://apps.ankiweb.net/)
2. Install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon (addon code: 2055492159)
3. Configure AnkiConnect to listen on the correct address (0.0.0.0:8765 by default)
4. Create a `.env` file in the project root directory with the following content (adjust as needed):
   ```
   ANKI_CONNECT_HOST=192.168.6.181
   ANKI_CONNECT_PORT=8765
   ```
5. Access the feed at `/anki/due-cards`

Each time you refresh the feed, you'll get a random card from those due for review today. The feed includes additional information such as:
- Deck name
- Card type and queue status
- Model name
- Total number of reviews for the card
- Number of lapses (times you've forgotten the card)
- Current interval (how long the card will wait before appearing again)
- Ease factor (how well you're learning the card)
- Tags associated with the card

## Community


Discord Server: [https://discord.gg/4BZBZuyx7p](https://discord.gg/4BZBZuyx7p)

## RSS Filtering

You can filter RSS content using the following query strings:

- include_title: Search titles (supports multiple keywords)
- include_description: Search descriptions
- exclude_title: Exclude titles
- exclude_description: Exclude descriptions
- limit: Limit number of items

## How to Contribute RSS

1. Fork this repository
2. Create a new spider directory and script in the spiders folder, write your crawler (refer to my [crawler tutorial](https://juejin.cn/post/6953881777756700709))
3. Add corresponding routes in main.py under blueprints (following existing route formats)
4. Write documentation in feeds.html under templates/main directory (follow existing formats)
5. Submit a PR

## Deployment

### Local Testing

First ensure [uv](https://github.com/astral-sh/uv) is installed

```bash
git clone https://github.com/alphardex/RSSHub-python
cd RSSHub-python
uv sync
uv run flask run
```

### Production Environment

```bash
uv run gunicorn main:app -b 0.0.0.0:5000
```

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fhillerliao%2Frsshub-python)

### Docker Deployment

Create docker container: `docker run -dt --name pyrsshub -p 5000:5000 hillerliao/pyrsshub:latest`

## Requirements

- Python 3.12.3
