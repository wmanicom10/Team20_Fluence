# AI Training Dataset Export

This feature covers two Jira stories:
- **TM20-116** Create Training Dataset Export from Verified Case Data
- **TM20-117** Implement AI Data Validation and Normalization Module

## What was added

### 1) Validation + normalization module
Backend now normalizes joined `cases`, `diseases`, and `locations` rows into a consistent AI-training schema.

Normalized output fields:
- `case_id`
- `disease_id`
- `disease`
- `disease_category`
- `location_id`
- `location`
- `city`
- `state_province`
- `country`
- `region_type`
- `latitude`
- `longitude`
- `case_count`
- `date_reported`
- `report_year`
- `report_month`
- `report_day`
- `severity`
- `severity_score`
- `verified`
- `data_source`
- `source_api`

Handled validation cases:
- missing or invalid `date_reported`
- invalid or negative `case_count`
- missing disease name
- missing location data
- malformed latitude / longitude
- invalid boolean values for `verified`

Invalid rows are dropped consistently and reported in `meta.dropped_examples`.

### 2) Dataset export endpoint
New endpoint:

`GET /api/ai/training-dataset`

Query params:
- `start_date` - optional, `YYYY-MM-DD`
- `end_date` - optional, `YYYY-MM-DD`
- `disease` - optional disease name
- `verified_only` - optional `true/false`, defaults to `true`
- `format` - optional `json` or `csv`, defaults to `json`

#### Example JSON request

```http
GET /api/ai/training-dataset?start_date=2026-03-01&end_date=2026-03-31
```

#### Example CSV request

```http
GET /api/ai/training-dataset?start_date=2026-03-01&end_date=2026-03-31&format=csv
```

### Example JSON response

```json
{
  "status": "success",
  "data": {
    "schema_version": "v1",
    "generated_at": "2026-04-07T18:20:00Z",
    "filters": {
      "disease": null,
      "start_date": "2026-03-01",
      "end_date": "2026-03-31",
      "verified_only": true
    },
    "meta": {
      "input_rows": 120,
      "valid_rows": 118,
      "dropped_rows": 2,
      "dropped_examples": [
        {
          "index": 14,
          "case_id": 52,
          "reason": "Invalid date_reported"
        }
      ]
    },
    "rows": []
  }
}
```

## CLI export script
A standalone export script was also added:

```bash
cd backend
python export_training_dataset.py --start-date 2026-03-01 --end-date 2026-03-31 --format csv --output exports/training_dataset.csv
```

JSON example:

```bash
python export_training_dataset.py --start-date 2026-03-01 --end-date 2026-03-31 --format json --output exports/training_dataset.json
```

## Tests added
- validation accepts good rows and drops malformed rows
- dataset export respects date filters
- CSV export uses a consistent schema header
- API route returns both JSON and CSV formats
