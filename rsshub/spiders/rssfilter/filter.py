import requests 
import feedparser
import arrow

from rsshub.utils import DEFAULT_HEADERS

def parse(post):
    item = {}
    item['title'] = post.title
    item['description'] = post.summary if hasattr(post,'summary') else post.title
    item['pubDate'] = post.published if post.has_key('published') else arrow.now().isoformat()
    item['link'] = post.link if hasattr(post,'link') else ''
    item['author'] = post.author if post.has_key('author') else ''
    return item

def ctx(feed_url=''):
    res = requests.get(feed_url,headers=DEFAULT_HEADERS,verify=False)
    feed = feedparser.parse(res.text)
    title = feed.feed.title
    description = feed.feed.subtitle
    author = feed.feed.author if feed.feed.has_key('author') \
        else feed.feed.generator if feed.feed.has_key('generator') \
        else title
    posts = feed.entries

    return {
        'title': title,
        'link': feed_url,
        'description': description,
        'author': author,
        'items': list(map(parse, posts)) 
    }  