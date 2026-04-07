import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app
from ai_dataset_export import dataset_to_csv, export_training_dataset
from ai_validation import normalize_case_rows


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


class AiDatasetExportTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.app = app
        self.client = app.test_client()

    def test_normalize_case_rows_drops_invalid_and_missing_rows(self):
        result = normalize_case_rows([
            {
                "case_id": 1,
                "case_count": 25,
                "date_reported": "2026-04-01",
                "verified": True,
                "diseases": {"disease_id": 2, "name": "Influenza A", "category": "respiratory"},
                "locations": {"location_id": 5, "city": "Boston", "state_province": "Massachusetts", "country": "USA"},
            },
            {
                "case_id": 2,
                "case_count": -1,
                "date_reported": "2026-04-01",
                "diseases": {"name": "RSV"},
                "locations": {"city": "Chicago", "state_province": "Illinois", "country": "USA"},
            },
            {
                "case_id": 3,
                "case_count": 8,
                "date_reported": "bad-date",
                "diseases": {"name": "COVID-19"},
                "locations": {"city": "Seattle", "state_province": "Washington", "country": "USA"},
            },
        ])

        self.assertEqual(result["meta"]["input_rows"], 3)
        self.assertEqual(result["meta"]["valid_rows"], 1)
        self.assertEqual(result["meta"]["dropped_rows"], 2)
        self.assertEqual(result["rows"][0]["location"], "Boston, Massachusetts, USA")
        self.assertEqual(result["rows"][0]["report_month"], 4)

    def test_export_training_dataset_applies_date_range_filter(self):
        fake_client = FakeClient({
            "cases": [
                {
                    "case_id": 1,
                    "disease_id": 10,
                    "location_id": 7,
                    "case_count": 100,
                    "date_reported": "2026-03-30",
                    "severity": "high",
                    "verified": True,
                    "data_source": "hospital",
                    "source_api": None,
                    "diseases": {"disease_id": 10, "name": "Influenza A", "category": "respiratory"},
                    "locations": {"location_id": 7, "city": "Boston", "state_province": "Massachusetts", "country": "USA", "latitude": 42.36, "longitude": -71.05, "region_type": "city"},
                },
                {
                    "case_id": 2,
                    "disease_id": 10,
                    "location_id": 7,
                    "case_count": 110,
                    "date_reported": "2026-04-01",
                    "severity": "critical",
                    "verified": True,
                    "data_source": "hospital",
                    "source_api": None,
                    "diseases": {"disease_id": 10, "name": "Influenza A", "category": "respiratory"},
                    "locations": {"location_id": 7, "city": "Boston", "state_province": "Massachusetts", "country": "USA", "latitude": 42.36, "longitude": -71.05, "region_type": "city"},
                },
            ]
        })

        with patch("ai_dataset_export.get_supabase_client", return_value=fake_client):
            with self.app.app_context():
                dataset = export_training_dataset(self.app, {"start_date": "2026-04-01", "end_date": "2026-04-01"})

        self.assertEqual(dataset["meta"]["valid_rows"], 1)
        self.assertEqual(dataset["rows"][0]["case_id"], 2)
        self.assertEqual(dataset["rows"][0]["severity_score"], 4)

    def test_dataset_to_csv_writes_consistent_header(self):
        dataset = {
            "meta": {"normalized_schema": ["case_id", "disease", "location"]},
            "rows": [{"case_id": 2, "disease": "COVID-19", "location": "Boston, Massachusetts, USA"}],
        }
        csv_text = dataset_to_csv(dataset)
        self.assertTrue(csv_text.startswith("case_id,disease,location"))
        self.assertIn("COVID-19", csv_text)

    def test_training_dataset_route_returns_json(self):
        fake_client = FakeClient({
            "cases": [
                {
                    "case_id": 9,
                    "disease_id": 4,
                    "location_id": 2,
                    "case_count": 55,
                    "date_reported": "2026-04-02",
                    "verified": True,
                    "severity": "moderate",
                    "diseases": {"disease_id": 4, "name": "RSV", "category": "respiratory"},
                    "locations": {"location_id": 2, "city": "Syracuse", "state_province": "New York", "country": "USA"},
                }
            ]
        })

        with patch("ai_dataset_export.get_supabase_client", return_value=fake_client):
            response = self.client.get("/api/ai/training-dataset?start_date=2026-04-01&end_date=2026-04-02")

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["meta"]["valid_rows"], 1)

    def test_training_dataset_route_returns_csv(self):
        fake_client = FakeClient({
            "cases": [
                {
                    "case_id": 9,
                    "disease_id": 4,
                    "location_id": 2,
                    "case_count": 55,
                    "date_reported": "2026-04-02",
                    "verified": True,
                    "severity": "moderate",
                    "diseases": {"disease_id": 4, "name": "RSV", "category": "respiratory"},
                    "locations": {"location_id": 2, "city": "Syracuse", "state_province": "New York", "country": "USA"},
                }
            ]
        })

        with patch("ai_dataset_export.get_supabase_client", return_value=fake_client):
            response = self.client.get("/api/ai/training-dataset?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("case_id,disease_id,disease", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
