import json
import requests

domain = 'https://itunes.apple.com'

countries = {"CN": "143465-19",
"US": "143441-1",
"JP": "143462-9",
"KR": "143466-13",
"HK": "143463-18",
"AU": "143460",
"TW": "143470-18",
"CA": "143455-6",
"DK": "143458-2",
"RU": "143469-16",
"ID": "143476-2",
"TR": "143480-2",
"GR": "143448-2",
"DE": "143443-4",
"IT": "143450-7",
"NO": "143457-2",
"FR": "143442-3",
"TH": "143475-2",
"SE": "143456-17",
"FI": "143447-2",
"GB": "143444",
"NL": "143452-10",
"BR": "143503-15",
"PT": "143453-24",
"MX": "143468-28",
"ES": "143454-8",
"VN": "143471-2"}

def gen_headers(cc=''):
    headers = {
        "Accept-Language": f"{cc}",
        "User-Agent": "AppStore/2.0 iOS/10.2 model/iPhone6,1 hwp/s5l8960x build/14C92 (6; dt:89)",
        'Accept': '*/*' ,
        'X-Apple-Store-Front': f'{countries[cc.upper()]},29' ,
    }
    return headers

def parse(post):
    print(post)
    item = {}
    subtitle = post['name'] + '</br></br>' + post['subtitle'] if post.__contains__('subtitle') else post['name']
    item['title'] = post['name']
    item['description'] = subtitle + '</br></br>开发者: ' + '<a href="' + post['artistUrl']  + '">' + post['artistName'] + '</a> ' \
                          + '</br></br>Rating: ' + str( post['userRating']['value'] ) \
                          + '，数量：' + str( post['userRating']['ratingCount'] )
    url_paths = post['shortUrl'].split('/')
    item['author'] = post['artistName']
    del url_paths[-2]
    item['link'] = '/'.join(url_paths)
    return item

def ctx(cc='', genreid=''):
    top_url = f"{domain}/WebObjects/MZStore.woa/wa/viewTop?cc={cc}&genreId={genreid}&l=en"
    res = requests.get(top_url, headers=gen_headers(cc)).json()
    posts = res['storePlatformData']['lockup']['results'].values()
    
    return {
        'title': f'Top Apps in {cc} - App Store',
        'link': top_url,
        'description': f'Top Apps in {cc} - App Store',
        'author': 'hillerliao',
        'items': list(map(parse, posts)) 
    }