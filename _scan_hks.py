# -*- coding: utf-8 -*-
"""临时脚本：扫描同花顺港股频道所有子栏目列表页 URL"""
import requests, re, io, sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = 'gbk'
    return r.text


def dump(url, out):
    html = fetch(url)
    io.open(out, 'w', encoding='utf-8').write(html)
    print('saved', out, len(html))
    return html


def main():
    html = fetch('https://stock.10jqka.com.cn/hks/')
    io.open('_hks_home.html', 'w', encoding='utf-8').write(html)
    print('home len', len(html))
    # 提取所有链接
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{2,40})</a>', html)
    seen = set()
    for u, t in links:
        if 'hks' in u and not u.endswith(('.css', '.js', '.jpg', '.png', '.gif')):
            key = (u.strip(), t.strip())
            if key not in seen:
                seen.add(key)
                print(u.strip(), '|', t.strip())
    # 也抓取两个已知列表页
    dump('https://stock.10jqka.com.cn/hks/ggyj_list/', '_hks_ggyj.html')
    dump('https://stock.10jqka.com.cn/hks/ggydg_list/', '_hks_ggydg.html')


if __name__ == '__main__':
    main()
