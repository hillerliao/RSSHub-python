import requests 
import feedparser

from rsshub.utils import DEFAULT_HEADERS
from rsshub.utils import fetch

def parse(post):
    item = {}
    item['title'] = post.title
    item['description'] = post.summary
    item['pubDate'] = post.published
    item['link'] = post.link
    return item

def ctx(feed_url=''):
    # tree = fetch(feed_url,headers=DEFAULT_HEADERS)
    # title = tree.css('channel').css('title::text').get()
    # description = tree.css('channel').css('description').get()
    # posts = tree.css('item')

    feed = feedparser.parse(feed_url)

    title = feed.feed.title
    description = feed.feed.subtitle

    posts = feed.entries
    
    return {
        'title': title,
        'link': feed_url,
        'description': description,
        'author': feed.feed.author,
        'items': list(map(parse, posts)) 
    }  