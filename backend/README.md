# Fluence Backend Starter (Flask)

Sprint-1 friendly Flask backend structure:
- **No database implementation** (DB already exists / handled by another task)
- A few **stub endpoints** to prove the backend runs
- Clean separation: `app.py` (app factory) + `routes.py` (endpoints) + `config.py` (settings)

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

## Endpoints
- `GET /health`
- `GET /cases` (stub)
- `GET /diseases` (stub)
