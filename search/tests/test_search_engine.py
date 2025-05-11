import os
import unittest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from search.search_engine import SearchEngine

class TestSearchEngine(unittest.TestCase):
    def setUp(self):
        os.environ.pop('BULK_SEARCH_YOUTUBE_API_KEY', None)
        os.environ.pop('NORMAL_SEARCH_YOUTUBE_API_KEY', None)
        self.engine = SearchEngine()
        # self.loop = asyncio.get_event_loop()


    def test_init_default_and_custom(self):
        eng = SearchEngine()
        self.assertEqual(eng.max_results, 10)
        self.assertEqual(eng.retries, 5)
        # custom config
        custom = {'format': 'bestvideo'}
        eng2 = SearchEngine(config=custom)
        self.assertIs(eng2.config, custom)

    def test_is_youtube_link(self):
        eng = SearchEngine()
        good = [
            "https://www.youtube.com/watch?v=abcdefghiJK",
            "http://youtu.be/abcdefghiJK",
            "https://m.youtube.com/watch?v=abcdefghiJK",
            "https://www.youtube.com/shorts/abcdefghiJK",
            "https://www.youtube.com/embed/abcdefghiJK"
        ]
        for url in good:
            self.assertTrue(eng._is_youtube_link(url), msg=url)
        bad = ["", "https://example.com/watch?v=xxx", "not a url"]
        for url in bad:
            self.assertFalse(eng._is_youtube_link(url), msg=url)

    def test_clean_query_and_validate(self):
        eng = SearchEngine()
        raw = "  héllo   world  "
        cleaned = eng._clean_query(raw)
        self.assertEqual(cleaned, "héllo world")

        # validate empty
        obj, ok = eng._validate_query("")
        self.assertFalse(ok)
        self.assertIn("empty", obj['reason'])

        # validate too long
        long_q = "x" * (eng.max_query_length + 1)
        obj, ok = eng._validate_query(long_q)
        self.assertFalse(ok)
        self.assertIn("too long", obj['reason'])

        # valid
        obj, ok = eng._validate_query("foo")
        self.assertTrue(ok)
        self.assertEqual(obj['type'], 'valid')

    def test_clean_and_classify_query(self):
        eng = SearchEngine()
        # empty
        res = eng.clean_and_classify_query("")
        self.assertEqual(res['type'], 'invalid')
        # youtube
        url = "https://youtu.be/abcdefghiJK"
        res = eng.clean_and_classify_query(f"  {url}  ")
        self.assertEqual(res['type'], 'youtube')
        self.assertEqual(res['query'], url)
        # search
        res = eng.clean_and_classify_query("  some   term ")
        self.assertEqual(res['type'], 'search')
        self.assertEqual(res['query'], "some term")

    def test_parse_duration(self):
        eng = SearchEngine()
        self.assertEqual(eng._parse_duration("PT1H2M3S"), 3600 + 120 + 3)
        self.assertEqual(eng._parse_duration("PT45M"), 2700)
        self.assertEqual(eng._parse_duration("PT5S"), 5)
        self.assertEqual(eng._parse_duration("PT0S"), 0)

    @patch.object(SearchEngine, "_execute_search")
    def test_regular_search_single(self, mock_exec):
        # simulate a single-video result
        mock_exec.return_value = {
            'title': 'T', 'duration': 42, 'uploader': 'U',
            'thumbnail': 'thumb.jpg', 'webpage_url': 'u',
            'upload_date': '2025-01-01', 'thumbnails': []
        }
        eng = SearchEngine()
        coro = eng.regular_search({'type':'search','query':'foo'})
        result = asyncio.run(coro)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['title'], 'T')
        self.assertEqual(result[0]['duration'], 42)

    @patch.object(SearchEngine, "_execute_search")
    def test_regular_search_playlist(self, mock_exec):
        # simulate playlist of 3 entries
        entries = []
        for i in range(3):
            entries.append({
                'title': f'T{i}', 'duration': i,
                'uploader': f'U{i}', 'thumbnail': f't{i}.jpg',
                'webpage_url': f'u{i}', 'upload_date': '2025-01-01',
                'thumbnails': [
                    {'url':'small','filesize':10, 'height':9,'width':9},
                    {'url':'big','filesize':100,'height':90,'width':90}
                ]
            })
        mock_exec.return_value = {'_type':'playlist','entries':entries}
        eng = SearchEngine()
        # ask for 2 results
        coro = eng.regular_search({'type':'search','query':'foo'}, max_results=2)
        result = asyncio.run(coro)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'T0')
        self.assertEqual(result[1]['title'], 'T1')
        # thumbnails
        self.assertEqual(result[0]['largest_thumbnail'], 'big')
        self.assertEqual(result[0]['smallest_thumbnail'], 'small')


    @patch.object(SearchEngine, "_execute_search", side_effect=[
    Exception("fail 1"), Exception("fail 2"), 
        {
            'title': 'Recovered',
            'duration': 42,
            'uploader': 'U',
            'thumbnail': 'thumb.jpg',
            'webpage_url': 'u',
            'upload_date': '2025-01-01',
            'thumbnails': [
                {'url': 'small', 'filesize': 10},
                {'url': 'big', 'filesize': 100}
            ]
        }
    ])
    def test_regular_search_eventual_success(self, mock_exec):
        eng = SearchEngine()
        coro = eng.regular_search({'type': 'search', 'query': 'foo'})
        result = asyncio.run(coro)
        self.assertEqual(result[0]['title'], 'Recovered')


    def test_lan_search_raises(self):
        eng = SearchEngine()
        with self.assertRaises(NotImplementedError):
            eng.lan_search("foo")

    @patch.object(SearchEngine, "regular_search_with_yt_api", new_callable=AsyncMock)
    def test_wrapped_search_and_bulk(self, mock_api):
        # simulate single term
        mock_api.return_value = [ {'title':'X'} ]
        eng = SearchEngine()
        wrapped = asyncio.run(eng._wrapped_search({'type':'search','query':'foo'}, 1))
        self.assertEqual(wrapped['count'], 1)
        # bulk
        bulk = asyncio.run(eng.bulk_search([{'type':'search','query':'a'}, {'type':'search','query':'b'}]))
        self.assertEqual(len(bulk), 2)
        self.assertIn('results', bulk[0])

    @patch.object(SearchEngine, '_retry_request')
    def test_regular_search_api_quota_limit(self, mock_retry):
        self.engine.NORMAL_API_KEY = 'fake-key'  # Simulate valid key
        mock_retry.side_effect = Exception("HTTP Error 403: quotaExceeded")
        
        result = asyncio.run(self.engine.regular_search_with_yt_api(
            {'type': 'search', 'query': 'quota-test'}
        ))
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn('title', result[0])



    @patch.object(SearchEngine, '_execute_search')
    def test_regular_search_rate_limited(self, mock_exec):
        mock_exec.side_effect = Exception("HTTP Error 429: Too Many Requests")
        result = asyncio.run(self.engine.regular_search({'type': 'search', 'query': 'Requests'}))
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('Too Many Requests', result['error'])
        

    @patch.object(SearchEngine, '_execute_search')
    def test_regular_search_extraction_error(self, mock_exec):
        mock_exec.side_effect = Exception("Unable to extract video data")
        result = asyncio.run(self.engine.regular_search({'type': 'search', 'query': 'extract'}))
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('Unable to extract video data', result['error'])

        

    @patch.object(SearchEngine, '_execute_search')
    def test_regular_search_unsupported_url(self, mock_exec):
        mock_exec.side_effect = Exception("Unsupported URL")
        result = asyncio.run(self.engine.regular_search({'type': 'search', 'query': 'URL'}))
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('Unsupported URL', result['error'])

        



if __name__ == '__main__':
    unittest.main()

    # Run with :   python -m unittest -f search.tests.test_search_engine
