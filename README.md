# Team20_Fluence

## Project Overview
Fluence is a public health disease surveillance web app built for CIS454. It integrates a React/Vite frontend, Flask backend, Supabase database, and disease.sh API.

## Branch Structure
- **prototype**: Integrated branch with all project code (frontend, backend, database, API, docs)
- **main**: Legacy — backend and API development
- **docs**: Legacy — frontend and database development

## Repository Structure
```
├── frontend/          # React/Vite app (map, filters, data views, case submission, auth)
│   ├── src/
│   │   ├── components/    # Reusable UI (Navbar, DiseaseCard, DiseaseTable)
│   │   ├── pages/         # Route pages (Home, MapView, DiseaseDataView, CaseSubmission, Login, Signup)
│   │   └── data/          # Mock data
│   └── public/
├── backend/           # Flask API server + Supabase integration
│   ├── app.py             # Flask app entry point
│   ├── routes.py          # All API endpoints (/api/cases, /api/diseases, /api/locations, etc.)
│   ├── db.py              # Supabase client
│   ├── config.py          # Environment config
│   └── proof-of-concept.py
├── api_stuff/         # Node/Express API scripts (disease.sh proxy, filters)
├── database-test/     # Supabase query scripts and SQL tests
├── docs/              # All project documentation
│   ├── initial-database-schema.md
│   ├── Fluence_Demo_API_Documentation.md
│   ├── Fluence_AI_Model_Research_Document.docx
│   ├── Fluence_API_to_Supabase_Integration_Documentation.docx
│   ├── Fluence Coding Conventions.pdf
│   └── ...
└── .gitignore
```

## How to Run
1. Clone the repo and checkout the `prototype` branch
2. Install dependencies:
   ```
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   cd ../api_stuff && npm install
   ```
3. Set up environment variables for the backend:
   ```
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_KEY=<your-supabase-key>
   ```
4. Start services:
   - Frontend: `cd frontend && npm run dev`
   - Backend: `cd backend && python app.py`
   - API server: `cd api_stuff && node api_with_filters.js`

## Contributors
- Sebastian Lassander (frontend, integration)
- Ethan Batick (API, docs)
- Will Manicom (database, queries)
- Jason Riek (backend, Flask)

