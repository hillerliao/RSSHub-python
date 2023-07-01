from rsshub.utils import DEFAULT_HEADERS, fetch


def parse_html(post):
    item = {}
    item['title'] = post.xpath('text()').extract_first()
    item['link'] = post.xpath('@href').extract_first()
    print(item['link'])
    item['description'] = (
        fetch(item['link'], headers=DEFAULT_HEADERS)
        .xpath('//div[@id=\'detail\']')
        .get()
    )
    return item
