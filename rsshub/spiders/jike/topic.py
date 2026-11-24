import html
import json
import re
import textwrap
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import arrow

from rsshub.utils import fetch_with_deadline

BASE_URL = 'https://m.okjike.com'
VIDEO_API = 'https://api.ruguoapp.com/1.0/mediaMeta/play?type=ORIGINAL_POST'
UNKNOWN_TYPE_NOTE = '未知帖子类型，请前往即刻 APP 查看'


def _not_found(topic_url):
    return {'title': '主题 ID 不存在，或该主题暂无内容', 'link': topic_url, 'items': []}


def _sanitize_cdata(text):
    """模板用 <![CDATA[...]]> 包裹且带 |safe，防 "]]>" 闭合逃逸。"""
    return (text or '').replace(']]>', ']] >')


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
        resp = fetch_with_deadline(f'{VIDEO_API}&id={post_id}', deadline=8.0)
        return resp.json().get('url') or ''
    except Exception:
        return ''


def _resolve_video_urls(post_ids):
    """串行查视频直链太慢（每个 10s 超时），并行处理。"""
    if not post_ids:
        return {}
    with ThreadPoolExecutor(max_workers=min(len(post_ids), 5)) as executor:
        urls = list(executor.map(_fetch_video_url, post_ids))
    return dict(zip(post_ids, urls))


def _video_duration_minutes(video):
    try:
        return int(float(video.get('duration') or 0) // 60000)
    except (TypeError, ValueError):
        return 0


def _is_wechat_link(link_url):
    """只有真正的微信公众号文章才把条目链接直接指向原文。"""
    try:
        return urlparse(link_url).hostname == 'mp.weixin.qq.com'
    except Exception:
        return False


def _parse_post(post, topic_url, video_url='', show_uid=False):
    """把一条即刻帖子转成 feed item 字典。"""
    post_type = post.get('type')
    content = post.get('content') or ''
    post_id = post.get('id')
    is_original = post_type == 'ORIGINAL_POST'

    if not is_original and not content:
        content = UNKNOWN_TYPE_NOTE
    link = f'{BASE_URL}/originalPosts/{post_id}' if is_original else topic_url

    author = ''
    description = ''
    user = post.get('user') or {}
    if user:
        author = user.get('screenName') or ''
        if show_uid:
            description += (
                f"<span>用户昵称：{html.escape(author)} <br> "
                f"Username：{html.escape(user.get('username') or '')}</span><br>"
            )

    audio_name = video_name = link_name = ''
    link_info = post.get('linkInfo') or {}
    video = link_info.get('video') or post.get('video')
    audio = link_info.get('audio') or post.get('audio')
    if link_info:
        link_url = link_info.get('originalLinkUrl') or link_info.get('linkUrl') or ''
        if link_url and _is_wechat_link(link_url):
            link = link_url

        if audio:
            audio_image = (audio.get('image') or {}).get('picUrl') or ''
            audio_name = f"{audio.get('title') or ''} - {audio.get('author') or ''}"
            description += f'<img src="{html.escape(audio_image, quote=True)}">'
            description += f'<a href="{html.escape(link_url, quote=True)}">{html.escape(audio_name)}</a>'

        if video:
            video_image = (video.get('image') or {}).get('picUrl') or ''
            video_name = link_info.get('title') or ''
            duration = _video_duration_minutes(video)
            description += f'<img src="{html.escape(video_image, quote=True)}">'
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
        if not isinstance(pic, dict):
            continue
        pic_url = _original_pic_url(pic)
        if pic_url:
            description += f'<br><img src="{html.escape(pic_url, quote=True)}">'

    if video and video_url:
        description += f'<br><video src="{html.escape(video_url, quote=True)}" controls="controls"></video>'

    if audio_name:
        raw_title = audio_name
    elif video_name:
        raw_title = video_name
    elif content:
        raw_title = textwrap.shorten(content, width=100, placeholder='...')
    elif link_name:
        raw_title = link_name
    else:
        raw_title = '无题'

    pub_date = ''
    if post.get('createdAt'):
        try:
            pub_date = arrow.get(post['createdAt']).isoformat()
        except Exception:
            pub_date = post['createdAt']

    return {
        'title': _sanitize_cdata(raw_title),
        'link': html.escape(link, quote=True),
        'author': _sanitize_cdata(author),
        'description': description.strip().replace('\n', '<br>'),
        'pubDate': pub_date,
    }


def ctx(topic_id, show_uid=0):
    """即刻圈子帖子列表：抓圈子页内嵌的 JSON，不需要登录，只取第一页。"""
    topic_url = f'{BASE_URL}/topics/{topic_id}'
    try:
        resp = fetch_with_deadline(topic_url, deadline=10.0)
        resp.raise_for_status()
    except Exception:
        return _not_found(topic_url)

    match = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', resp.text, re.S)
    if not match:
        return _not_found(topic_url)

    try:
        page_props = json.loads(match.group(1)).get('props', {}).get('pageProps', {})
    except (json.JSONDecodeError, AttributeError):
        return _not_found(topic_url)

    topic = page_props.get('topic')
    posts = page_props.get('posts')
    if not isinstance(topic, dict) or not topic or not isinstance(posts, list):
        return _not_found(topic_url)

    video_ids = [
        p['id'] for p in posts
        if isinstance(p, dict) and p.get('id')
        and (p.get('video') or (p.get('linkInfo') or {}).get('video'))
    ]
    video_urls = _resolve_video_urls(video_ids)

    items = [
        _parse_post(p, topic_url, video_urls.get(p.get('id'), ''), show_uid=bool(show_uid))
        for p in posts if isinstance(p, dict)
    ]

    square = topic.get('squarePicture') or {}
    image = square.get('picUrl') or square.get('middlePicUrl') or square.get('thumbnailUrl') or ''

    return {
        'title': _sanitize_cdata(f"{topic.get('content') or ''} - 即刻圈子"),
        'link': html.escape(topic_url, quote=True),
        'description': html.escape(topic.get('briefIntro') or ''),
        'author': '即刻',
        'image': image,
        'items': items,
    }
