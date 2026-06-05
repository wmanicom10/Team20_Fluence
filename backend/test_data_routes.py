import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)
        self._limit = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.rows = [row for row in self.rows if row.get(field) == value]
        return self

    def gte(self, field, value):
        self.rows = [row for row in self.rows if row.get(field) is not None and row.get(field) >= value]
        return self

    def lte(self, field, value):
        self.rows = [row for row in self.rows if row.get(field) is not None and row.get(field) <= value]
        return self

    def ilike(self, field, value):
        needle = str(value).lower()
        self.rows = [row for row in self.rows if str(row.get(field, "")).lower() == needle]
        return self

    def order(self, field, desc=False):
        self.rows = sorted(self.rows, key=lambda row: row.get(field) or "", reverse=desc)
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        rows = self.rows[: self._limit] if self._limit is not None else self.rows
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return FakeQuery(self.tables.get(name, []))


class DataRouteTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_cases_rejects_invalid_date_filters(self):
        fake_client = FakeClient({"cases": []})

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.get("/api/cases?date_from=03-31-2026")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"]["message"],
            "date_from must use YYYY-MM-DD format",
        )

    def test_ui_disease_data_formats_frontend_payload(self):
        fake_client = FakeClient(
            {
                "cases": [
                    {
                        "case_count": 120,
                        "date_reported": "2026-03-31",
                        "severity": "high",
                        "verified": True,
                        "diseases": {"name": "Influenza A"},
                        "locations": {"city": "Boston", "state_province": "Massachusetts"},
                    },
                    {
                        "case_count": 80,
                        "date_reported": "2026-03-30",
                        "severity": "medium",
                        "verified": True,
                        "diseases": {"name": "Influenza A"},
                        "locations": {"city": "Boston", "state_province": "Massachusetts"},
                    },
                    {
                        "case_count": 45,
                        "date_reported": "2026-03-31",
                        "severity": "low",
                        "verified": True,
                        "diseases": {"name": "RSV"},
                        "locations": {"city": "Chicago", "state_province": "Illinois"},
                    },
                ]
            }
        )

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.get("/api/ui/disease-data")

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(len(body["data"]), 2)
        self.assertEqual(body["data"][0]["disease"], "Influenza A")
        self.assertEqual(body["data"][0]["location"], "Boston, Massachusetts")
        self.assertEqual(body["data"][0]["caseCount"], 120)
        self.assertEqual(body["data"][0]["severity"], "High")
        self.assertEqual(body["data"][0]["rateOfChange"], 50.0)

    def test_metrics_cases_by_disease_aggregates_verified_rows(self):
        fake_client = FakeClient(
            {
                "cases": [
                    {"case_count": 20, "verified": True, "diseases": {"name": "COVID-19"}},
                    {"case_count": 15, "verified": True, "diseases": {"name": "COVID-19"}},
                    {"case_count": 11, "verified": True, "diseases": {"name": "RSV"}},
                    {"case_count": 99, "verified": False, "diseases": {"name": "RSV"}},
                ]
            }
        )

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.get("/api/metrics/cases-by-disease")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["data"],
            [
                {"disease_name": "COVID-19", "total_cases": 35},
                {"disease_name": "RSV", "total_cases": 11},
            ],
        )

    def test_ai_risk_output_returns_summary_for_location_and_date(self):
        fake_client = FakeClient(
            {
                "locations": [
                    {
                        "location_id": 7,
                        "city": "Boston",
                        "state_province": "Massachusetts",
                        "country": "USA",
                        "latitude": 42.3601,
                        "longitude": -71.0589,
                        "region_type": "city",
                    }
                ],
                "cases": [
                    {
                        "location_id": 7,
                        "case_count": 90,
                        "date_reported": "2026-03-31",
                        "severity": "high",
                        "verified": True,
                        "diseases": {"name": "Influenza A"},
                    },
                    {
                        "location_id": 7,
                        "case_count": 30,
                        "date_reported": "2026-03-29",
                        "severity": "moderate",
                        "verified": True,
                        "diseases": {"name": "COVID-19"},
                    },
                    {
                        "location_id": 7,
                        "case_count": 10,
                        "date_reported": "2026-03-28",
                        "severity": "critical",
                        "verified": False,
                        "diseases": {"name": "RSV"},
                    },
                ],
            }
        )

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.get(
                "/api/ai/risk-output?city=Boston&state_province=Massachusetts&date=2026-03-31"
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["location"]["location_id"], 7)
        self.assertEqual(body["data"]["summary"]["total_cases"], 120)
        self.assertEqual(body["data"]["summary"]["disease_count"], 2)
        self.assertEqual(body["data"]["summary"]["highest_severity"], "High")
        self.assertEqual(body["data"]["summary"]["risk_level"], "High")
        self.assertEqual(body["data"]["summary"]["trend_percentage"], 200.0)
        self.assertEqual(body["data"]["diseases"][0]["disease"], "Influenza A")

    def test_ai_risk_output_handles_empty_results(self):
        fake_client = FakeClient(
            {
                "locations": [
                    {
                        "location_id": 22,
                        "city": "Seattle",
                        "state_province": "Washington",
                        "country": "USA",
                        "latitude": 47.6062,
                        "longitude": -122.3321,
                        "region_type": "city",
                    }
                ],
                "cases": [],
            }
        )

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.get("/api/ai/risk-output?location_id=22&date=2026-03-31")

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["data"]["summary"]["total_cases"], 0)
        self.assertEqual(body["data"]["summary"]["risk_level"], "Low")
        self.assertEqual(body["data"]["diseases"], [])

    def test_ai_risk_output_validates_required_inputs(self):
        response = self.client.get("/api/ai/risk-output?city=Boston")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"]["message"],
            "date query parameter is required",
        )

    def test_ai_risk_output_returns_500_on_backend_error(self):
        with patch("routes.get_supabase_client", side_effect=Exception("database offline")):
            response = self.client.get("/api/ai/risk-output?location_id=7&date=2026-03-31")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json()["error"]["message"],
            "Failed to build AI risk output",
        )


if __name__ == "__main__":
    unittest.main()
