# Fluence Backend (Flask + Supabase)

This backend follows REST-style API conventions with `/api/...` resource paths and a consistent response structure.

## Response contract
All responses return one of these shapes:

Success:
```json
{
  "status": "success",
  "data": {}
}
```

Error:
```json
{
  "status": "error",
  "error": {
    "message": "...",
    "details": {}
  }
}
```

## 1) Install dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

## 2) Configure environment
Create `backend/.env`:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_KEY
FLASK_DEBUG=true
SECRET_KEY=dev-key
```

## 3) Run
```bash
cd backend
python app.py
```

## API endpoints

### Health
- `GET /api/health`

### Diseases
- `GET /api/diseases`
- `GET /api/diseases?active_only=true`
- `POST /api/diseases`

### Locations
- `GET /api/locations`
- `GET /api/locations?country=USA&state_province=New York`
- `POST /api/locations`

### Cases
- `GET /api/cases`
- `GET /api/cases/<case_id>`
- `GET /api/cases?disease_name=COVID-19&date_from=2026-02-01&date_to=2026-02-15&verified_only=true`
- `POST /api/cases`
- `PATCH /api/cases/<case_id>`
- `DELETE /api/cases/<case_id>`

### Metrics
- `GET /api/metrics/cases-by-disease`
- `GET /api/metrics/cases-by-disease?verified_only=false`

## Validation highlights
- All write endpoints require valid JSON bodies.
- Required fields are enforced for `POST /api/diseases`, `POST /api/locations`, and `POST /api/cases`.
- `date_reported`, `date_from`, and `date_to` must be `YYYY-MM-DD`.
- Integer fields (such as `case_count`, `disease_id`, and `location_id`) are validated.
- Boolean query/body values (for example `verified_only`, `verified`, `is_active`) are validated.
