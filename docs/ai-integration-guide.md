# AI Integration Setup and Backend Usage Guide

Complete guide for understanding how Fluence's AI-related backend features work together. This document covers the training data flow, external disease data usage, and AI risk output usage.

## Architecture Overview

The AI system is built from four backend modules:

```
                    ┌─────────────┐
  Supabase DB ────► │ai_validation│  Cleans and normalizes raw case rows
  (cases,           │  .py        │  from Supabase into a consistent shape.
   diseases,        └──────┬──────┘
   locations)              │
                           ▼
                    ┌─────────────┐
                    │ai_pipeline  │  Builds feature rows (per disease+
                    │  .py        │  location), trains baseline model,
                    └──────┬──────┘  and scores risk output.
                           │
                           ▼
                    ┌──────────────┐
                    │ai_integration│  Orchestrates the full pipeline:
                    │  .py         │  query DB → validate → train → score.
                    └──────┬───────┘  Caches model in Flask app context.
                           │
                           ▼
                    ┌─────────────┐
                    │routes.py    │  Exposes API endpoints for frontend
                    │             │  and external consumers.
                    └─────────────┘
```

### Module Responsibilities

| Module | Purpose | Key Functions |
|:---|:---|:---|
| `ai_validation.py` | Cleans raw Supabase rows into normalized dicts. Handles missing/malformed data. | `normalize_case_rows()`, `normalize_case_row()`, `parse_iso_date()`, `parse_bool()` |
| `ai_pipeline.py` | Builds feature vectors per disease+location group, trains the baseline model, and scores risk. | `build_feature_rows()`, `train_baseline_pipeline()`, `score_risk_output()` |
| `ai_integration.py` | Orchestrates the end-to-end pipeline. Queries Supabase, runs validation, trains model, caches result. | `train_ai_pipeline()`, `get_or_train_ai_pipeline()` |
| `routes.py` | Exposes HTTP endpoints. Delegates to `ai_integration.py`. | `ai_train()`, `ai_risk_output()`, `ui_ai_risk()` |

---

## Data Flow

### Step 1: Raw Data (Supabase)

The pipeline starts with the `cases` table joined with `diseases` and `locations`:

```sql
SELECT case_id, case_count, date_reported, severity, verified, data_source, source_api,
       diseases(name),
       locations(city, state_province, country)
FROM cases
WHERE verified = true
ORDER BY date_reported ASC
```

### Step 2: Validation and Normalization (`ai_validation.py`)

Each row is cleaned into a consistent shape:

```json
{
  "case_id": 42,
  "disease": "COVID-19",
  "location": "Chicago, Illinois, USA",
  "case_count": 150,
  "date_reported": "2026-03-28",
  "severity": "high",
  "severity_score": 3,
  "verified": true,
  "data_source": "manual_submission",
  "source_api": null
}
```

Invalid rows (missing date, negative case count, malformed data) are dropped and logged in the `meta` field:

```json
{
  "meta": {
    "input_rows": 100,
    "valid_rows": 97,
    "dropped_rows": 3,
    "dropped_examples": [
      {"index": 5, "reason": "Missing date_reported"},
      {"index": 22, "reason": "Invalid case_count"}
    ]
  }
}
```

### Step 3: Feature Extraction (`ai_pipeline.py`)

Normalized rows are grouped by `(disease, location)` and aggregated into feature vectors:

```json
{
  "disease": "COVID-19",
  "location": "Chicago, Illinois, USA",
  "date": "2026-03-28",
  "current_cases": 150,
  "previous_cases": 120,
  "avg_cases": 95.5,
  "max_cases": 150,
  "trend_pct": 25.0,
  "severity_score": 3,
  "verified_ratio": 1.0,
  "history_points": 8
}
```

### Step 4: Risk Scoring (`ai_pipeline.py`)

Each feature row is scored using a weighted formula:

| Component | Weight | Source |
|:---|:---|:---|
| Case volume | 40% | `current_cases / max_current_cases` |
| Average cases | 20% | `avg_cases / max_avg_cases` |
| Trend | 20% | `abs(trend_pct) / max_trend_pct` |
| Severity | 15% | `severity_score / 4.0` |
| Verification | 5% | `verified_ratio` |

Score is clamped to `[0.0, 1.0]` and mapped to a risk level:

| Score Range | Risk Level |
|:---|:---|
| `>= 0.80` | Critical |
| `>= 0.60` | High |
| `>= 0.35` | Medium |
| `< 0.35` | Low |

---

## API Endpoints

### 1. Train AI Pipeline

**`POST /api/ai/train`**

Triggers a fresh training run. Returns model metadata and validation summary.

```bash
curl -X POST http://127.0.0.1:5000/api/ai/train \
  -H "Content-Type: application/json" \
  -d '{"disease": "COVID-19", "startDate": "2026-03-01", "endDate": "2026-03-31"}'
```

**Success response:**

```json
{
  "status": "success",
  "data": {
    "model": {
      "model_version": "baseline-v1",
      "generated_at": "2026-04-07T15:30:00.000000Z",
      "training_examples": 12
    },
    "validation": {
      "input_rows": 50,
      "valid_rows": 48,
      "dropped_rows": 2,
      "dropped_examples": []
    },
    "risk_output_count": 12
  }
}
```

All filter fields are optional. Omitting all filters trains on all verified cases.

---

### 2. Full AI Risk Output

**`GET /api/ai/risk-output`**

Returns risk-scored items with model metadata. Designed for detailed analysis.

```bash
curl "http://127.0.0.1:5000/api/ai/risk-output?disease=COVID-19&startDate=2026-03-01&endDate=2026-03-31"
```

**Query parameters:**

| Param | Required | Description |
|:---|:---|:---|
| `disease` | No | Disease name filter (e.g., `COVID-19`) |
| `startDate` | No | Start of date range (`YYYY-MM-DD`) |
| `endDate` | No | End of date range (`YYYY-MM-DD`) |
| `verified_only` | No | `true` (default) or `false` |

**Success response:**

```json
{
  "status": "success",
  "data": {
    "model": {
      "model_version": "baseline-v1",
      "generated_at": "2026-04-07T15:30:00.000000Z",
      "training_examples": 12
    },
    "validation": {
      "input_rows": 50,
      "valid_rows": 48,
      "dropped_rows": 2,
      "dropped_examples": []
    },
    "items": [
      {
        "id": 1,
        "disease": "COVID-19",
        "location": "Chicago, Illinois, USA",
        "date": "2026-03-28",
        "riskScore": 0.72,
        "riskLevel": "High",
        "caseCount": 150,
        "previousCaseCount": 120,
        "averageCases": 95.5,
        "trendPct": 25.0,
        "severityScore": 3,
        "verifiedRatio": 1.0,
        "historyPoints": 8,
        "recommendedAction": "Monitor closely and flag for review.",
        "modelVersion": "baseline-v1"
      }
    ]
  }
}
```

---

### 3. Dashboard AI Risk (Simplified)

**`GET /api/ui/ai-risk`**

Returns only the risk items array — no model metadata. Used by the frontend `AiRiskSummary` component.

```bash
curl "http://127.0.0.1:5000/api/ui/ai-risk?disease=COVID-19"
```

**Success response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "disease": "COVID-19",
      "location": "Chicago, Illinois, USA",
      "date": "2026-03-28",
      "riskScore": 0.72,
      "riskLevel": "High",
      "caseCount": 150,
      "previousCaseCount": 120,
      "averageCases": 95.5,
      "trendPct": 25.0,
      "severityScore": 3,
      "verifiedRatio": 1.0,
      "historyPoints": 8,
      "recommendedAction": "Monitor closely and flag for review.",
      "modelVersion": "baseline-v1"
    }
  ]
}
```

The frontend `AiRiskSummary` component reads `data[0].riskLevel` for display and `data[0].caseCount` or `data[0].trendPct` as the supporting metric.

---

### 4. Dashboard Disease Data (Cached)

**`GET /api/ui/disease-data`**

Returns formatted disease data for the dashboard cards/table. Includes in-memory caching (30s TTL).

```bash
curl "http://127.0.0.1:5000/api/ui/disease-data?disease=COVID-19&limit=5"
```

**Query parameters:**

| Param | Required | Description |
|:---|:---|:---|
| `disease` | No | Disease name or `All Diseases` |
| `startDate` | No | Start of date range (`YYYY-MM-DD`) |
| `endDate` | No | End of date range (`YYYY-MM-DD`) |
| `verified_only` | No | `true` (default) or `false` |
| `limit` | No | Max number of results to return |

**Success response:**

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

Response headers include `X-Cache: HIT` or `X-Cache: MISS` and `Cache-Control: public, max-age=30`.
See `docs/ui-disease-data-optimization.md` for caching details.

---

### 5. External Disease Data Proxy

**`GET /api/external/covid/countries`**

Proxies country-level COVID data from disease.sh with in-memory caching.

```bash
curl "http://127.0.0.1:5000/api/external/covid/countries?countries=US,CA&sort=cases"
```

**Query parameters:**

| Param | Required | Description |
|:---|:---|:---|
| `countries` | No | Comma-separated country codes |
| `sort` | No | Sort field: `cases`, `deaths`, `recovered` |
| `allowNull` | No | Include null values (`true`/`false`) |
| `yesterday` | No | Use yesterday's data (`true`/`false`) |
| `twoDaysAgo` | No | Use two days ago data (`true`/`false`) |

See `docs/ai-risk-features.md` for detailed response examples including cache hit/miss/stale fallback behavior.

---

## How Features Connect

```
┌────────────────────────────────────────────────────────────┐
│                     FRONTEND                               │
│                                                            │
│  DiseaseDataView ──► GET /api/ui/disease-data              │
│       │                                                    │
│       └── AiRiskSummary ──► GET /api/ui/ai-risk            │
│                                                            │
│  MapView ──► GET /api/cases (with location coordinates)    │
│                                                            │
│  CaseSubmission ──► POST /api/cases                        │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                     BACKEND                                │
│                                                            │
│  POST /api/cases ──► Supabase (new case records)           │
│                                                            │
│  GET /api/ui/disease-data ──► Supabase ──► _format_for_    │
│                                            frontend()      │
│                                                            │
│  GET /api/ui/ai-risk ──► ai_integration ──► ai_validation  │
│                          ──► ai_pipeline ──► risk scores   │
│                                                            │
│  GET /api/external/covid/countries ──► disease.sh (cached) │
└────────────────────────────────────────────────────────────┘
```

1. **Cases are submitted** via `POST /api/cases` (from CaseSubmission page).
2. **Dashboard reads** formatted case data via `GET /api/ui/disease-data` (cached 30s).
3. **AI Risk component** calls `GET /api/ui/ai-risk` which runs the full validation → training → scoring pipeline on the same case data.
4. **External data** is available via `GET /api/external/covid/countries` for supplementary disease snapshots from disease.sh.
5. **Training can be triggered** manually via `POST /api/ai/train` to refresh the model.

---

## Configuration

Set these environment variables in `backend/.env`:

| Variable | Default | Description |
|:---|:---|:---|
| `SUPABASE_URL` | *(required)* | Supabase project URL |
| `SUPABASE_KEY` | *(required)* | Supabase anon/service key |
| `AI_MODEL_VERSION` | `baseline-v1` | Version string embedded in model output |
| `AI_AUTO_TRAIN_ON_READ` | `true` | If `true`, risk-output endpoints always retrain from fresh data. If `false`, cached model is reused. |
| `FLASK_DEBUG` | `true` | Enable Flask debug mode |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |
| `EXTERNAL_API_CACHE_TTL_SECONDS` | `120` | TTL for external disease.sh cache |
| `EXTERNAL_API_TIMEOUT_SECONDS` | `8` | Timeout for upstream disease.sh requests |

---

## Local Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- A Supabase project with `cases`, `diseases`, and `locations` tables

### Backend

```bash
cd backend
pip install -r requirements.txt

# Create .env with your Supabase credentials
echo "SUPABASE_URL=https://your-project.supabase.co" > .env
echo "SUPABASE_KEY=your-anon-key" >> .env

# Start backend
python app.py
# Backend runs on http://127.0.0.1:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

### Quick Verification

After starting both:

```bash
# Health check
curl http://127.0.0.1:5000/api/health

# Dashboard data
curl http://127.0.0.1:5000/api/ui/disease-data

# AI risk data
curl http://127.0.0.1:5000/api/ui/ai-risk

# Train model
curl -X POST http://127.0.0.1:5000/api/ai/train
```

---

## Troubleshooting

| Issue | Cause | Fix |
|:---|:---|:---|
| `SUPABASE_URL and SUPABASE_KEY must be set` | Missing `.env` file or env vars | Create `backend/.env` with valid credentials |
| AI risk returns empty `data: []` | No verified cases in database | Add cases via `POST /api/cases` with `verified: true`, or use CaseSubmission page |
| `Failed to load external disease data` | disease.sh is down or unreachable | Wait and retry — stale cache will be used if available |
| Frontend shows "Loading…" indefinitely | Backend not running or CORS mismatch | Start backend with `python app.py`, check `CORS_ORIGINS` includes frontend URL |
| `X-Cache: MISS` on every request | Cache TTL too short or different filter params each time | Check query params are consistent; TTL is 30s by default |

---

## Related Documentation

- [`docs/ai-risk-features.md`](ai-risk-features.md) — Detailed endpoint examples for risk output and external API proxy
- [`docs/ui-disease-data-optimization.md`](ui-disease-data-optimization.md) — Caching strategy for the disease data endpoint
- [`docs/auth-endpoints.md`](auth-endpoints.md) — Authentication endpoints
- [`docs/role-gating.md`](role-gating.md) — Role-based access control
- [`docs/route-protection.md`](route-protection.md) — Frontend route protection
