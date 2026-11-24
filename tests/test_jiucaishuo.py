import unittest
from unittest.mock import patch, Mock
from xml.etree import ElementTree as ET

from tests.base import BaseTestCase
from rsshub.extensions import cache


class JiucaishuoTestCase(BaseTestCase):
    def test_feed_contains_stable_entries_and_safe_content(self):
        cache.clear()
        response = Mock()
        response.json.return_value = {'code': 0, 'data': {'items': [{
            'id': 6893, 'agent_id': 13, 'agent_name': '估值老K',
            'title': '价格 <分位> ]]> 测试', 'body': '第一段\n<script>alert(1)</script>',
            'publish_date': '2026-10-13', 'publish_at': '10-13 01:23',
            'media': [{'type': 'image', 'url': 'https://file.jiucaishuo.com/test.png'}],
            'chips': [{'k': 'PE分位', 'v': '51%'}],
        }]}}
        with patch('requests.get', return_value=response):
            result = self.client.get('/jiucaishuo/feed')
        self.assertEqual(result.status_code, 200)
        root = ET.fromstring(result.data)
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        entry = root.find('a:entry', ns)
        assert entry is not None
        self.assertEqual(entry.find('a:id', ns).text,
                         'https://jiucaishuo.com/feed?agent_id=13#feed-6893')
        self.assertEqual(entry.find('a:published', ns).text, '2026-10-13T01:23:00+08:00')
        content = entry.find('a:content', ns).text
        self.assertIn('&lt;script&gt;', content)
        self.assertIn('test.png', content)
        self.assertIn('51%', content)
        self.assertEqual(len(root.findall('a:entry', ns)), 1)


    def test_invalid_parameters_do_not_fetch(self):
        cache.clear()
        with patch('requests.get') as get:
            for query in ('tab=mine', 'tab=follow', 'agent_id=no', 'agent_id=0', 'agent_id=-1'):
                self.assertEqual(self.client.get('/jiucaishuo/feed?' + query).status_code, 400)
            get.assert_not_called()

    def test_upstream_failure_is_not_cached(self):
        cache.clear()
        response = Mock()
        response.json.return_value = {'code': 1, 'msg': 'unavailable'}
        with patch('requests.get', return_value=response) as get:
            self.assertEqual(self.client.get('/jiucaishuo/feed').status_code, 502)
            response.json.return_value = {'code': 0, 'data': {'items': []}}
            result = self.client.get('/jiucaishuo/feed')
            self.assertEqual(result.status_code, 200)
            ET.fromstring(result.data)
            self.assertEqual(get.call_count, 2)

    def test_filters_and_cache_are_isolated_by_query(self):
        cache.clear()
        response = Mock()
        response.json.return_value = {'code': 0, 'data': {'items': [
            {'id': 2, 'agent_id': 13, 'title': '黄金', 'body': '正文',
             'publish_date': '2026-10-13', 'publish_at': '10-13 01:23'},
            {'id': 1, 'agent_id': 13, 'title': '半导体', 'body': '正文',
             'publish_date': '2026-10-12', 'publish_at': '10-12 01:23'},
        ]}}
        with patch('requests.get', return_value=response) as get:
            for _ in range(2):
                result = self.client.get('/jiucaishuo/feed?agent_id=13&include_title=黄金&limit=1')
                self.assertEqual(result.status_code, 200)
                root = ET.fromstring(result.data)
                entries = root.findall('{http://www.w3.org/2005/Atom}entry')
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0].findtext('{http://www.w3.org/2005/Atom}title'), '黄金')
            self.assertEqual(get.call_count, 1)
            self.assertIn('agent_id=13', get.call_args.args[0])
            result = self.client.get('/jiucaishuo/feed?tab=recommend')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(get.call_count, 2)
            self.assertIn('tab=recommend', get.call_args.args[0])

    def test_parser_deduplicates_sorts_and_rejects_unsafe_images(self):
        from rsshub.spiders.jiucaishuo.feed import ctx
        older = {'id': 1, 'agent_id': 9, 'title': 'older', 'body': '\x00test',
                 'publish_date': '2025-12-31', 'publish_at': '12-31 23:59',
                 'media': [{'type': 'image', 'url': 'javascript:alert(1)'}]}
        newer = dict(older, id=2, title='newer', publish_date='2026-01-01', publish_at='01-01 00:01')
        response = Mock()
        response.json.return_value = {'code': 0, 'data': {'items': [older, newer, older, {}]}}
        with patch('requests.get', return_value=response):
            feed = ctx()
        self.assertEqual([item['title'] for item in feed['items']], ['newer', 'older'])
        self.assertNotIn('javascript:', feed['items'][0]['description'])
        self.assertNotIn('\x00', feed['items'][0]['description'])


if __name__ == '__main__':
    unittest.main()
