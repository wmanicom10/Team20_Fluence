# Fluence Backend (Flask + Supabase)

This backend follows REST-style API conventions with `/api/...` paths and a consistent response structure.

## Response contract
Success:
```json
{ "status": "success", "data": {} }
```

Error:
```json
{ "status": "error", "error": { "message": "...", "details": {} } }
```

## Frontend integration
The frontend branch can replace mock data with these two endpoints directly:

- `GET /api/ui/disease-data`
- `GET /api/ui/disease-types`

`/api/ui/disease-data` supports query params used by UI filters:
- `disease` (example: `COVID-19`, or `All Diseases`)
- `startDate` (`YYYY-MM-DD`)
- `endDate` (`YYYY-MM-DD`)
- `verified_only` (`true/false`, default `true`)

Example response item shape (matches current frontend mock model):
```json
{
  "id": 1,
  "disease": "COVID-19",
  "location": "New York City, New York",
  "caseCount": 523,
  "date": "2026-02-10",
  "severity": "High",
  "newCases24h": 523,
  "rateOfChange": 0.0
}
```

## Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_KEY
FLASK_DEBUG=true
SECRET_KEY=dev-key
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Run:
```bash
cd backend
python app.py
```

## Core API endpoints
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/verify-official`
- `GET /api/auth/verify-official/status`
- `GET /api/health`
- `GET/POST /api/diseases`
- `GET/POST /api/locations`
- `GET/POST /api/cases`
- `GET/PATCH/DELETE /api/cases/<case_id>`
- `GET /api/metrics/cases-by-disease`

Auth request/response examples are documented in [docs/auth-endpoints.md](../docs/auth-endpoints.md).
Health official verification request/response examples are documented in [docs/health-official-verification-endpoint.md](../docs/health-official-verification-endpoint.md).
