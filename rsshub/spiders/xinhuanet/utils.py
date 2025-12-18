from rsshub.utils import DEFAULT_HEADERS, fetch


def parse_html(post):
    item = {}
    item['title'] = post.get_text()
    href = post['href']
    # Handle relative URLs
    if href.startswith('http'):
        item['link'] = href
    else:
        # Convert relative URL to absolute URL
        item['link'] = f'http://www.news.cn/{href}'
    print(item['link'])
    detail_tree = fetch(item['link'], headers=DEFAULT_HEADERS)
    detail_elem = detail_tree.select('#detail') if detail_tree else []
    item['description'] = detail_elem[0].decode_contents() if detail_elem else ''
    return item
