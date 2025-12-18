from rsshub.utils import DEFAULT_HEADERS, fetch


def parse_html(post):
    item = {}
    item['title'] = post.get_text()
    item['link'] = post['href']
    print(item['link'])
    detail_tree = fetch(item['link'], headers=DEFAULT_HEADERS)
    detail_elem = detail_tree.select('#detail') if detail_tree else []
    item['description'] = detail_elem[0].decode_contents() if detail_elem else ''
    return item
