# Fluence Backend (Flask + Supabase)

This backend now reads from Supabase using the same tables used in your partner's Node scripts.

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

## Endpoints
- `GET /health`
- `GET /diseases`
- `GET /diseases?active_only=true`
- `GET /cases`
- `GET /cases?disease_name=COVID-19&date_from=2026-02-01&date_to=2026-02-15&verified_only=true`
- `GET /cases?disease_id=3`
