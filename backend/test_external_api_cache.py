import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from app import create_app
import routes


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class ExternalApiCacheTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        app.config["EXTERNAL_API_CACHE_TTL_SECONDS"] = 60
        self.client = app.test_client()
        routes._external_api_cache.clear()

    def test_second_request_uses_cache(self):
        payload = [{"country": "US", "cases": 1000, "countryInfo": {"lat": 1, "long": 2}}]

        with patch("routes.urllib_request.urlopen", return_value=FakeResponse(payload)) as mocked_urlopen:
            first = self.client.get("/api/external/covid/countries?countries=US")
            second = self.client.get("/api/external/covid/countries?countries=US")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"]["cache"]["hit"], False)
        self.assertEqual(second.get_json()["data"]["cache"]["hit"], True)
        self.assertEqual(mocked_urlopen.call_count, 1)

    def test_stale_cache_is_returned_when_upstream_fails(self):
        payload = [{"country": "US", "cases": 1000, "countryInfo": {"lat": 1, "long": 2}}]

        with patch("routes.urllib_request.urlopen", return_value=FakeResponse(payload)):
            first = self.client.get("/api/external/covid/countries?countries=US")

        self.assertEqual(first.status_code, 200)

        cache_key = next(iter(routes._external_api_cache.keys()))
        routes._external_api_cache[cache_key]["expires_at"] = 0

        with patch("routes.urllib_request.urlopen", side_effect=URLError("network down")):
            stale = self.client.get("/api/external/covid/countries?countries=US")

        self.assertEqual(stale.status_code, 200)
        self.assertEqual(stale.get_json()["data"]["cache"]["stale_fallback"], True)

    def test_upstream_failure_without_cache_returns_502(self):
        with patch("routes.urllib_request.urlopen", side_effect=URLError("network down")):
            response = self.client.get("/api/external/covid/countries?countries=US")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["status"], "error")


if __name__ == "__main__":
    unittest.main()
