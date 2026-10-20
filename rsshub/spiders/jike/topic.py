import html
import json
import re

import arrow
import requests

from rsshub.utils import DEFAULT_HEADERS

BASE_URL = 'https://m.okjike.com'
VIDEO_API = 'https://api.ruguoapp.com/1.0/mediaMeta/play?type=ORIGINAL_POST'


def _original_pic_url(pic):
    """即刻图片默认带缩略图参数，这里还原成原图地址。"""
    url = pic.get('picUrl') or ''
    if not url:
        return ''
    if re.search(r'\.[0-9a-z]+\?imageMogr2', url):
        return url.split('?imageMogr2')[0]
    return re.sub(r'thumbnail/.+', '', url)


def _fetch_video_url(post_id):
    """即刻帖子里的 video 对象没有直链，需要再查一次媒体接口。"""
    try:
        resp = requests.get(f'{VIDEO_API}&id={post_id}', headers=DEFAULT_HEADERS, timeout=10)
        return resp.json().get('url') or ''
    except Exception:
        return ''


def _parse_post(post, show_uid=False):
    content = post.get('content') or ''
    link = f"{BASE_URL}/originalPosts/{post.get('id')}"

    author = ''
    description = ''
    if post.get('user'):
        author = post['user'].get('screenName') or ''
        if show_uid:
            description += (
                f"<span>用户昵称：{html.escape(author)} <br> "
                f"Username：{html.escape(post['user'].get('username') or '')}</span><br>"
            )

    audio_name = video_name = link_name = ''
    link_info = post.get('linkInfo') or {}
    if link_info:
        link_url = link_info.get('originalLinkUrl') or link_info.get('linkUrl') or ''
        # 微信公众号文章直接把条目链接指向原文
        if link_url and 'mp.weixin.qq.com' in link_url:
            link = link_url

        audio = link_info.get('audio') or post.get('audio')
        video = link_info.get('video') or post.get('video')
        if audio:
            audio_name = f"{audio.get('title') or ''} - {audio.get('author') or ''}"
            image = (audio.get('image') or {}).get('picUrl') or (audio.get('image') or {}).get('thumbnailUrl') or ''
            description += f'<img src="{html.escape(image, quote=True)}">'
            description += f'<a href="{html.escape(link_url, quote=True)}">{html.escape(audio_name)}</a>'

        if video:
            image = (video.get('image') or {}).get('picUrl') or (video.get('image') or {}).get('thumbnailUrl') or ''
            duration = int((video.get('duration') or 0) / 60000)
            video_name = link_info.get('title') or ''
            description += f'<img src="{html.escape(image, quote=True)}">'
            description += (
                f'<a href="{html.escape(link_url, quote=True)}">'
                f'{html.escape(video_name or "观看视频")} - 约{duration}分钟</a>'
            )

        if not audio and not video and link_url:
            link_name = link_info.get('title') or ''
            image = link_info.get('pictureUrl') or ''
            if image:
                description += f'<img src="{html.escape(image, quote=True)}">'
            description += f'<a href="{html.escape(link_url, quote=True)}">{html.escape(link_name or "访问原文")}</a>'

    if content:
        description += ('<br>' if description else '') + html.escape(content)

    for pic in post.get('pictures') or []:
        pic_url = _original_pic_url(pic)
        if pic_url:
            description += f'<br><img src="{html.escape(pic_url, quote=True)}">'

    if post.get('video'):
        video_url = _fetch_video_url(post.get('id'))
        if video_url:
            description += f'<br><video src="{html.escape(video_url, quote=True)}" controls="controls"></video>'

    title = audio_name or video_name or content or link_name or '无题'
    if len(title) > 100:
        title = title[:100] + '...'

    pub_date = ''
    if post.get('createdAt'):
        try:
            pub_date = arrow.get(post['createdAt']).isoformat()
        except Exception:
            pub_date = post['createdAt']

    return {
        'title': title,
        'link': link,
        'author': author,
        'description': description.strip().replace('\n', '<br>'),
        'pubDate': pub_date,
    }


def _not_found(topic_url):
    return {'title': '主题 ID 不存在，或该主题暂无内容', 'link': topic_url, 'items': []}


def ctx(topic_id, show_uid=0):
    topic_url = f'{BASE_URL}/topics/{topic_id}'
    try:
        resp = requests.get(topic_url, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return _not_found(topic_url)

    match = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', resp.text, re.S)
    if not match:
        return _not_found(topic_url)

    try:
        page_props = json.loads(match.group(1)).get('props', {}).get('pageProps', {})
    except (json.JSONDecodeError, AttributeError):
        return _not_found(topic_url)

    topic = page_props.get('topic') or {}
    posts = page_props.get('posts') or []
    if not topic:
        return _not_found(topic_url)

    return {
        'title': f"{topic.get('content') or ''} - 即刻圈子",
        'link': topic_url,
        'description': topic.get('briefIntro') or '',
        'author': '即刻',
        'items': [_parse_post(post, show_uid=bool(show_uid)) for post in posts],
    }
