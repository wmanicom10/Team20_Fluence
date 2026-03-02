# Fluence Backend (Flask + Supabase)

This backend is connected to Supabase and exposes API endpoints for diseases, locations, and case data.

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

Use your own key values. Do not commit real keys.

## 3) Run
```bash
cd backend
python app.py
```

## API endpoints

### Health
- `GET /health`

### Diseases
- `GET /diseases`
- `GET /diseases?active_only=true`
- `POST /diseases`

Example `POST /diseases` body:
```json
{
  "name": "Measles",
  "category": "viral",
  "severity_level": "moderate",
  "description": "Highly contagious viral infection",
  "is_active": true
}
```

### Locations
- `GET /locations`
- `GET /locations?country=USA&state_province=New York`
- `POST /locations`

Example `POST /locations` body:
```json
{
  "country": "USA",
  "state_province": "Massachusetts",
  "city": "Boston",
  "latitude": 42.3601,
  "longitude": -71.0589,
  "population": 675647,
  "region_type": "city"
}
```

### Cases
- `GET /cases`
- `GET /cases?disease_name=COVID-19&date_from=2026-02-01&date_to=2026-02-15&verified_only=true`
- `GET /cases?disease_id=3`
- `POST /cases`
- `PATCH /cases/<case_id>`

Example `POST /cases` body:
```json
{
  "disease_id": 1,
  "location_id": 2,
  "case_count": 25,
  "date_reported": "2026-02-15",
  "data_source": "manual_submission",
  "source_api": null,
  "severity": "moderate",
  "verified": true
}
```

Example `PATCH /cases/<case_id>` body:
```json
{
  "case_count": 40,
  "severity": "severe",
  "verified": true
}
```

### Stats
- `GET /stats/cases-by-disease`
- `GET /stats/cases-by-disease?verified_only=false`
