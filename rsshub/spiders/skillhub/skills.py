import ast
import html
import re
from email.utils import parsedate_to_datetime

import requests

from rsshub.utils import DEFAULT_HEADERS

SKILLS_URL = 'https://skillhub.swaggin.cn/skills.html'
DATA_URL = 'https://skillhub.swaggin.cn/data-simulator.js'

_ARRAY_RE = re.compile(
    r'const\s+skillsData\s*=\s*\[(.*?)\]\s*;.*?const\s+tutorialsData',
    re.DOTALL,
)
_OBJECT_RE = re.compile(r'\{(.*?)\}', re.DOTALL)


def _field(obj, name):
    pattern = rf"\b{re.escape(name)}\s*:\s*(['\"])((?:\\.|(?!\1).)*)\1"
    match = re.search(pattern, obj, re.DOTALL)
    if not match:
        return ''
    return ast.literal_eval(f'{match.group(1)}{match.group(2)}{match.group(1)}')


def _number(obj, name, default=0):
    match = re.search(rf'\b{re.escape(name)}\s*:\s*(-?\d+(?:\.\d+)?)', obj)
    return float(match.group(1)) if match else default


def _tags(obj):
    match = re.search(r'\btags\s*:\s*\[(.*?)\]', obj, re.DOTALL)
    if not match:
        return []
    return [value for _, value in re.findall(r"(['\"])((?:\\.|(?!\1).)*)\1", match.group(1))]


def parse_skills(script, modified_at=None):
    array_match = _ARRAY_RE.search(script)
    if not array_match:
        raise ValueError('skillsData not found')

    items = []
    for obj in _OBJECT_RE.findall(array_match.group(1)):
        skill_id = int(_number(obj, 'id'))
        name = _field(obj, 'name')
        if not skill_id or not name:
            continue
        description = _field(obj, 'desc')
        tags = _tags(obj)
        downloads = int(_number(obj, 'downloads'))
        rating = _number(obj, 'rating')
        details = [f'<p>{html.escape(description)}</p>']
        if tags:
            details.append(f'<p>标签：{html.escape(", ".join(tags))}</p>')
        details.append(f'<p>下载量：{downloads:,} · 评分：{rating:g}</p>')
        item = {
            'title': name,
            'link': f'{SKILLS_URL}#skill-{skill_id}',
            'description': ''.join(details),
            'author': 'SkillHub',
            '_id': skill_id,
        }
        if modified_at:
            item['pubDate'] = modified_at
        items.append(item)

    items.sort(key=lambda item: item['_id'], reverse=True)
    for item in items:
        item.pop('_id')
    return items


def ctx():
    response = requests.get(DATA_URL, headers=DEFAULT_HEADERS, timeout=10)
    response.raise_for_status()
    modified_at = None
    if response.headers.get('Last-Modified'):
        modified_at = parsedate_to_datetime(response.headers['Last-Modified']).isoformat()

    return {
        'title': 'SkillHub 最新技能',
        'link': SKILLS_URL,
        'description': 'SkillHub 技能库最新发布，按技能 ID 倒序排列',
        'author': 'skillhub.swaggin.cn',
        'items': parse_skills(response.text, modified_at),
    }
