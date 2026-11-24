# -*- coding: utf-8 -*-
"""``/x/<username>``（Google News 版 Twitter 时间线）的排重与时间窗。"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import arrow
from tests.base import BaseTestCase

from rsshub.spiders.twitter import user as twitter


def make_entry(title, guid, days_ago=1, source='x.com'):
    dt = arrow.utcnow().shift(days=-days_ago)
    return SimpleNamespace(
        title=title,
        link='https://news.google.com/rss/articles/%s?oc=5' % guid,
        id=guid,
        published=dt.strftime('%a, %d %b %Y %H:%M:%S GMT'),
        published_parsed=dt.timetuple(),
        source={'title': source, 'href': 'https://x.com'},
    )


class DedupTestCase(unittest.TestCase):
    """Google News 对同一条推文会给出多个不同的 article id，只能按标题排重。"""

    TXT = '沃仕加息25个基点，所有委员均表示同意。 - x.com'

    def test_same_tweet_with_different_ids_is_merged(self):
        entries = [
            make_entry(self.TXT, 'CBMiZkFVX3lxTE1sX0VGNGxOTTBIUGlndA'),
            make_entry(self.TXT, 'CBMicEFVX3lxTFAzUHZaRWVlNWpvUWRzcGhB'),
            make_entry(self.TXT, 'CBMid0FVX3lxTFAzUHZaRWVlNWpvUWRzcGhB'),
        ]
        with patch.object(twitter, 'fetch_feed', side_effect=[entries, []]):
            ctx = twitter.ctx('wangwatchworld')
        self.assertEqual(len(ctx['items']), 1, '同一条推文的 3 个 article id 应并成一条')

    def test_distinct_permalink_tweets_are_not_merged(self):
        """标题里只有 URL 的 permalink 推文清洗后标题相同，但真实 URL 不同，不能误并。"""
        entries = [
            make_entry('https://x.com/i/status/1857439359026507877 - x.com', 'a'),
            make_entry('https://x.com/i/status/2063998840878018924 - x.com', 'b'),
        ]
        with patch.object(twitter, 'fetch_feed', side_effect=[entries, []]):
            ctx = twitter.ctx('wangwatchworld')
        self.assertEqual(len(ctx['items']), 2)
        links = {item['link'] for item in ctx['items']}
        self.assertEqual(links, {'https://x.com/i/status/1857439359026507877',
                                 'https://x.com/i/status/2063998840878018924'})

    def test_duplicates_across_editions_are_merged(self):
        entries = [make_entry(self.TXT, 'id-1'), make_entry('早晨开油管 - x.com', 'id-2')]
        with patch.object(twitter, 'fetch_feed', side_effect=[entries, list(reversed(entries))]):
            ctx = twitter.ctx('wangwatchworld')
        self.assertEqual(len(ctx['items']), 2, '两个桶返回同一批推文时不应翻倍')

    def test_private_fields_are_stripped(self):
        with patch.object(twitter, 'fetch_feed', side_effect=[[make_entry(self.TXT, 'id-1')], []]):
            ctx = twitter.ctx('wangwatchworld')
        for item in ctx['items']:
            self.assertFalse([key for key in item if key.startswith('_')])


class EditionQueryTestCase(unittest.TestCase):
    def test_when_goes_into_query_not_tbs(self):
        """tbs=qdr:7d 在 News RSS 上是空操作，时间窗得写成 when:7d。"""
        with patch.object(twitter, 'fetch_feed', return_value=[make_entry('推文 - x.com', 'id')]) as mocked:
            twitter.ctx('wangwatchworld', when='7d')
        params = mocked.call_args_list[0][0][0]
        self.assertEqual(params['q'], 'site:x.com/wangwatchworld when:7d')
        self.assertNotIn('tbs', params)

    def test_empty_when_result_retries_without_when_and_filters_locally(self):
        recent = make_entry('新鲜的推文 - x.com', 'guid-recent', days_ago=2)
        stale = make_entry('十天前的推文 - x.com', 'guid-stale', days_ago=10)
        with patch.object(twitter, 'fetch_feed',
                          side_effect=[ValueError('Google 新闻没有返回任何条目'),
                                       [recent, stale], []]) as mocked:
            ctx = twitter.ctx('wangwatchworld', when='7d', editions='cn')
        self.assertEqual([item['title'] for item in ctx['items']], ['新鲜的推文'])
        self.assertEqual(mocked.call_count, 2, '带 when: 查空后应只重试一次')
        self.assertIn('when:7d', mocked.call_args_list[0][0][0]['q'])
        self.assertNotIn('when:', mocked.call_args_list[1][0][0]['q'])


class AutoEditionTestCase(unittest.TestCase):
    def test_auto_picks_newest_edition_without_extra_request(self):
        cn_entries = [make_entry('中文桶的旧推文 - x.com', 'cn-1', days_ago=6)]
        us_entries = [make_entry('US bucket fresh tweet - x.com', 'us-1', days_ago=1)]
        with patch.object(twitter, 'fetch_feed', side_effect=[cn_entries, us_entries]) as mocked:
            ctx = twitter.ctx('wangwatchworld', auto=True)
        self.assertEqual(mocked.call_count, 2, '选桶用的是第一轮结果，不应再打一次 Google')
        self.assertEqual([item['title'] for item in ctx['items']], ['US bucket fresh tweet'])
        self.assertIn('auto 选中 us', ctx['description'])

    def test_auto_picks_non_empty_bucket(self):
        """某个桶空时，auto 应选另一桶；非选中桶的条目不会出现在结果里。"""
        cn_entries = [make_entry('中文桶最新推文 - x.com', 'cn-1', days_ago=1)]
        with patch.object(twitter, 'fetch_feed', side_effect=[cn_entries, []]) as mocked:
            ctx = twitter.ctx('wangwatchworld', auto=True)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(len(ctx['items']), 1)
        self.assertEqual(ctx['items'][0]['title'], '中文桶最新推文')

    def test_auto_keeps_newest_copy_of_cross_bucket_duplicate(self):
        """auto 选 cn，但某条推文在 us 有比 cn 更新的副本，应保留 us 那份而不是 cn 那份。"""
        cn_entries = [
            make_entry('跨桶推文 - x.com', 'cn-A', days_ago=10),    # 旧副本
            make_entry('CN-only newest - x.com', 'cn-B', days_ago=1),  # cn 桶整体最新
        ]
        us_entries = [
            make_entry('跨桶推文 - x.com', 'us-A', days_ago=2),     # 比 cn-A 新
        ]
        with patch.object(twitter, 'fetch_feed',
                          side_effect=[cn_entries, us_entries]) as mocked:
            ctx = twitter.ctx('wangwatchworld', auto=True)
        self.assertEqual(mocked.call_count, 2)
        items = {item['title']: item for item in ctx['items']}
        self.assertIn('CN-only newest', items)
        self.assertIn('跨桶推文', items)
        self.assertEqual(items['跨桶推文']['guid'], 'us-A',
                         '跨桶重复应保留时间最新那份（不限桶）')


class RouteTestCase(BaseTestCase):
    def test_route_renders_deduped_feed(self):
        entries = [make_entry('沃仕加息25个基点 - x.com', 'id-1'),
                   make_entry('沃仕加息25个基点 - x.com', 'id-2')]
        with patch.object(twitter, 'fetch_feed', side_effect=[entries, []]) as mocked:
            response = self.client.get('/x/wangwatchworld')
        self.assertEqual(response.status_code, 200)
        body = response.data.decode('utf-8')
        self.assertEqual(body.count('<entry>'), 1)
        self.assertEqual(mocked.call_args_list[0][0][0]['q'],
                         'site:x.com/wangwatchworld when:7d')

    def test_invalid_username_returns_empty_feed(self):
        response = self.client.get('/x/not-a-valid-name!')
        self.assertEqual(response.status_code, 200)
        self.assertIn('用户名不合法', response.data.decode('utf-8'))
