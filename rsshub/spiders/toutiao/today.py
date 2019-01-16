from rsshub.utils import fetch

base_url = 'https://toutiao.io'
tree = fetch(base_url)
items = []
posts = tree.css('.posts .post')

for post in posts:
    item = {}
    item['title'] = post.css('.title a::attr(title)').extract_first()
    item['description'] = ''
    item['pubDate'] = ''
    item['link'] = base_url + post.css('.title a::attr(href)').extract_first()
    items.append(item)

ctx = {
    'title': '开发者头条:今日头条',
    'link': 'https://toutiao.io',
    'description': '开发者头条:今日头条',
    'author': 'alphardex',
    'items': items
}