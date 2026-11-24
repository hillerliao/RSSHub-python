import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

import requests

from tests.base import BaseTestCase
from rsshub.extensions import cache


SKILLS_JS = """
const skillsData = [
  { id: 1, name: 'Older Skill', desc: 'old & useful', tags: ['工具'], downloads: 12, rating: 4.1, icon: 'fa-tool' },
  { id: 3, name: 'Newest Skill', desc: 'new <skill>', tags: ['开发', 'AI'], downloads: 34, rating: 4.9, icon: 'fa-code', featured: true },
];
// 教程数据
const tutorialsData = [];
"""


class SkillHubTestCase(BaseTestCase):
    def make_response(self):
        response = Mock()
        response.text = SKILLS_JS
        response.headers = {'Last-Modified': 'Fri, 13 Mar 2026 13:19:24 GMT'}
        return response

    def test_parser_returns_newest_skills_first(self):
        from rsshub.spiders.skillhub.skills import ctx

        with patch('requests.get', return_value=self.make_response()):
            feed = ctx()

        self.assertEqual([item['title'] for item in feed['items']],
                         ['Newest Skill', 'Older Skill'])
        newest = feed['items'][0]
        self.assertEqual(newest['link'],
                         'https://skillhub.swaggin.cn/skills.html#skill-3')
        self.assertEqual(newest['pubDate'], '2026-03-13T13:19:24+00:00')
        self.assertIn('开发', newest['description'])
        self.assertIn('34', newest['description'])
        self.assertIn('&lt;skill&gt;', newest['description'])

    def test_route_returns_valid_atom_and_supports_limit(self):
        cache.clear()
        with patch('requests.get', return_value=self.make_response()):
            result = self.client.get('/skillhub/skills?limit=1')

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_type, 'application/xml; charset=utf-8')
        root = ET.fromstring(result.data)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].findtext('{http://www.w3.org/2005/Atom}title'),
                         'Newest Skill')

    def test_upstream_failure_returns_502(self):
        cache.clear()
        with patch('requests.get', side_effect=requests.Timeout('upstream timeout')):
            result = self.client.get('/skillhub/skills')
        self.assertEqual(result.status_code, 502)


if __name__ == '__main__':
    unittest.main()
