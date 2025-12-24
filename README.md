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
4. Create a `.env` file in the project root directory with the following content (adjust as needed), or pass at runtime via `?api=` query param.
   ```
   ANKI_CONNECT_HOST=192.168.6.181
   ANKI_CONNECT_PORT=8765
   ```
5. Access the feed at `/anki/due-cards`
   - Runtime override: `/anki/due-cards?api=http://your_host:8765`

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
uv run gunicorn -c gunicorn.conf main:app
```

### Background Execution (nohup)

To run the server in the background and keep it running after you disconnect:

```bash
mkdir -p logs
nohup uv run gunicorn -c gunicorn.conf main:app > logs/server.log 2>&1 &
```

-   Output will be saved to `logs/server.log`.
-   Use `tail -f logs/server.log` to view logs.
-   Use `ps aux | grep gunicorn` to find the process ID.
-   Use `kill <pid>` to stop the server.

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fhillerliao%2Frsshub-python)

### Docker Deployment
#### Option 1: Docker Compose (Recommended)
This method ensures all configurations (like `shm_size` for Playwright) are correct.

1.  Create `docker-compose.yml`:
    ```yaml
    services:
      rsshub:
        image: hillerliao/pyrsshub:latest
        container_name: pyrsshub
        ports:
          - "5000:5000"
        restart: unless-stopped
        # Playwright requires increased shared memory
        shm_size: 512mb
        environment:
          - PORT=5000
    ```
2.  Run:
    ```bash
    docker-compose up -d
    ```

#### Option 2: Docker Run
If you prefer a single command:
```bash
docker run -d \
  --name pyrsshub \
  -p 5000:5000 \
  --restart unless-stopped \
  --shm-size=512mb \
  hillerliao/pyrsshub:latest
```

### Zeabur Deployment

Zeabur can automatically deploy directly from this GitHub repository or using a Docker image.

**Method 1: Git Integration**
1. Push this project to your GitHub.
2. In Zeabur, go to **Create Service** -> **Git**.
3. Select this repository.
4. Zeabur will automatically build and run it.

**Method 2: Pre-built Image**
1. In Zeabur, go to **Create Service** -> **Docker Image**.
2. Image Name: `hillerliao/pyrsshub:latest`
3. Zeabur will pull and run the optimized image.

> Note: The image includes Playwright dependencies optimized for Docker environments.

**Use cases:**
- `/scrape/https://example.com` - Get HTML source of any webpage
- `/xueqiu/user/USER_ID` - Scrape xueqiu user feeds
- Any route requiring browser automation

## Requirements

- Python 3.12.3
