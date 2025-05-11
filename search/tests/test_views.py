from django.test import TestCase, Client
from unittest.mock import patch


class SearchViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("search.views.engine.regular_search_with_yt_api")
    def test_search_success(self, mock_search):
        mock_search.return_value = [
            {
                "title": "Test Song",
                "duration": 200,
                "uploader": "Test Uploader",
                "thumbnail": "thumb.jpg",
                "webpage_url": "https://yt.com/video",
                "upload_date": "2020-01-01T00:00:00Z",
                "largest_thumbnail": "large.jpg",
                "smallest_thumbnail": "small.jpg"
            }
        ]

        response = self.client.get("/search/?query=Man%20of%20Steel")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json()[0]["title"], "Test Song")

    def test_search_missing_query(self):
        response = self.client.get("/search/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("search.views.engine.bulk_search")
    def test_bulk_search_success(self, mock_bulk):
        mock_bulk.return_value = [
            {
                "search_term": {"type": "search", "query": "Adele Hello"},
                "results": [
                    {
                        "title": "Test Adele Song",
                        "duration": 300,
                        "uploader": "Test VEVO",
                        "thumbnail": "thumb.jpg",
                        "webpage_url": "https://yt.com/adele",
                        "upload_date": "2020-01-01T00:00:00Z",
                        "largest_thumbnail": "large.jpg",
                        "smallest_thumbnail": "small.jpg"
                    }
                ],
                "count": 1
            }
        ]

        response = self.client.get("/search/bulk/?queries=Adele%20Hello")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json()[0]["search_term"]["query"], "Adele Hello")

    def test_bulk_search_no_queries(self):
        response = self.client.get("/search/bulk/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())


    
# Use this to run it:    python manage.py test search.tests.test_views