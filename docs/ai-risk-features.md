# AI And Risk Features Guide

This document explains the current Fluence AI/risk-related backend features with request and response examples.

## Purpose

Use this guide to:
- understand which endpoints power risk-aware dashboard behavior,
- see the expected request and response format quickly,
- onboard new team members without reading backend source first.

## System Flow (Simple)

1. Frontend requests disease summary data from `/api/ui/disease-data`.
2. Backend reads normalized case data from Supabase (`cases`, `diseases`, `locations`).
3. Backend formats each result into dashboard-friendly rows (disease, location, severity, counts, change).
4. Frontend renders cards/table and can sort/filter by disease and dates.
5. When external disease snapshots are needed, frontend/backend can call `/api/external/covid/countries`.
6. External requests are cached for a short TTL so repeated filter requests do not repeatedly hit disease.sh.
7. If disease.sh is temporarily unavailable, backend returns stale cached data when available.

## Endpoint 1: Dashboard Data

### GET `/api/ui/disease-data`

Returns dashboard-ready disease records.

Query parameters:
- `disease` (optional): disease name, or `All Diseases`
- `startDate` (optional): `YYYY-MM-DD`
- `endDate` (optional): `YYYY-MM-DD`
- `verified_only` (optional): `true` or `false` (default is `true`)

Example request:

```http
GET /api/ui/disease-data?disease=COVID-19&startDate=2026-03-01&endDate=2026-03-31
```

Example success response:

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "disease": "COVID-19",
      "location": "Chicago, Illinois",
      "caseCount": 182,
      "date": "2026-03-30",
      "severity": "High",
      "newCases24h": 182,
      "rateOfChange": 6.4
    }
  ]
}
```

## Endpoint 2: Disease Totals Metric

### GET `/api/metrics/cases-by-disease`

Returns aggregated totals by disease.

Query parameters:
- `verified_only` (optional): `true` or `false` (default is `true`)

Example request:

```http
GET /api/metrics/cases-by-disease?verified_only=true
```

Example success response:

```json
{
  "status": "success",
  "data": [
    {
      "disease_name": "COVID-19",
      "total_cases": 1402
    },
    {
      "disease_name": "Influenza",
      "total_cases": 410
    }
  ]
}
```

## Endpoint 3: AI Risk Output

### GET `/api/ai/risk-output`

Returns a location-based risk summary for a given date using existing case data.

Why this endpoint exists:
- gives the frontend a single backend contract for AI/risk-style summary output,
- summarizes case totals, disease breakdown, trend, and severity into a dashboard-friendly shape,
- handles empty result sets without requiring frontend-side aggregation.

Query parameters:
- `date` (required): `YYYY-MM-DD`
- `location_id` (optional): numeric location id
- `city` (optional if `location_id` provided): city name
- `state_province` (optional): state or province name
- `country` (optional): country name
- `window_days` (optional): integer from `1` to `30` (default `7`)
- `verified_only` (optional): `true` or `false` (default is `true`)

Example request:

```http
GET /api/ai/risk-output?city=Boston&state_province=Massachusetts&date=2026-03-31
```

Example success response:

```json
{
  "status": "success",
  "data": {
    "location": {
      "location_id": 7,
      "city": "Boston",
      "state_province": "Massachusetts",
      "country": "USA",
      "latitude": 42.3601,
      "longitude": -71.0589,
      "region_type": "city"
    },
    "as_of_date": "2026-03-31",
    "window_days": 7,
    "filters": {
      "verified_only": true
    },
    "summary": {
      "total_cases": 120,
      "disease_count": 2,
      "latest_reported_date": "2026-03-31",
      "latest_day_cases": 90,
      "previous_window_cases": 30,
      "trend_percentage": 200.0,
      "highest_severity": "High",
      "risk_score": 4,
      "risk_level": "High"
    },
    "diseases": [
      {
        "disease": "Influenza A",
        "total_cases": 90,
        "latest_reported_date": "2026-03-31",
        "severity": "High"
      },
      {
        "disease": "COVID-19",
        "total_cases": 30,
        "latest_reported_date": "2026-03-29",
        "severity": "Medium"
      }
    ]
  }
}
```

Example success response with no matching case data:

```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_cases": 0,
      "risk_level": "Low"
    },
    "diseases": []
  }
}
```

Example failure response:

```json
{
  "status": "error",
  "error": {
    "message": "date query parameter is required"
  }
}
```

## Endpoint 4: Cached External API Proxy

### GET `/api/external/covid/countries`

Provides filtered country-level snapshots from disease.sh with in-memory caching.

Why this endpoint exists:
- reduces repeated external API calls for common filter combinations,
- applies a short cache expiration,
- returns stale cached data if upstream fails.

Query parameters:
- `countries` (optional): comma-separated country codes, example `US,CA`
- `sort` (optional): `cases`, `deaths`, `recovered` (default `cases`)
- `allowNull` (optional): `true` or `false` (default `true`)
- `yesterday` (optional): `true` or `false`
- `twoDaysAgo` (optional): `true` or `false`

Example request:

```http
GET /api/external/covid/countries?countries=US,CA&sort=cases&yesterday=true
```

Example success response (cache miss -> upstream fetch):

```json
{
  "status": "success",
  "data": {
    "source": "disease.sh",
    "filters": {
      "allowNull": true,
      "yesterday": true,
      "twoDaysAgo": false,
      "sort": "cases",
      "countries": ["US", "CA"]
    },
    "rows": [
      {
        "country": "USA",
        "cases": 123,
        "deaths": 4,
        "recovered": 100,
        "countryInfo": {
          "lat": 37.09,
          "long": -95.71
        }
      }
    ],
    "cache": {
      "hit": false,
      "stale_fallback": false,
      "ttl_seconds": 120,
      "cached_at": "2026-03-31T18:22:10.000000Z",
      "expires_at": "2026-03-31T18:24:10.000000Z"
    },
    "meta": {
      "upstream": "https://disease.sh/v3/covid-19/countries/US%2CCA?allowNull=true&sort=cases&yesterday=true",
      "generated_at": "2026-03-31T18:22:10.000000Z"
    }
  }
}
```

Example success response when upstream fails but stale cache exists:

```json
{
  "status": "success",
  "data": {
    "cache": {
      "hit": false,
      "stale_fallback": true,
      "ttl_seconds": 120
    },
    "meta": {
      "warning": "Upstream request failed; returned stale cache: ..."
    }
  }
}
```

Example failure when no cache is available:

```json
{
  "status": "error",
  "error": {
    "message": "Failed to load external disease data",
    "details": "..."
  }
}
```

## Configuration

Set these in `backend/.env`:

```env
EXTERNAL_API_CACHE_TTL_SECONDS=120
EXTERNAL_API_TIMEOUT_SECONDS=8
```

## Quick Test Commands

From project root:

```bash
# first request (usually cache miss)
curl "http://127.0.0.1:5000/api/external/covid/countries?countries=US,CA"

# second identical request (cache hit)
curl "http://127.0.0.1:5000/api/external/covid/countries?countries=US,CA"
```

## Notes For New Team Members

- Use `/api/ui/disease-data` for dashboard UI data, not raw Supabase tables.
- Use `/api/ai/risk-output` when the UI needs summarized risk data for a location/date.
- Use `/api/external/covid/countries` when you need temporary external disease snapshots.
- Always check `data.cache` in external API responses to see whether data is fresh, cached, or stale fallback.
