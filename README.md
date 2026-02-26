# Team20_Fluence

## Project Overview
Fluence is a public health disease surveillance web app built for CIS454. It integrates a React/Vite frontend, Node/Express and Flask backend, Supabase database, and disease.sh API.

## Branch Structure
- **prototype**: Integrated branch with all core project code (frontend, backend, database, docs, API)
- **main**: Backend and API development (Flask, Node/Express)
- **docs**: Frontend and database development (React, Supabase, docs)

## Prototype Branch Contents
- `frontend/`: React/Vite app with map, filters, and disease data views
- `backend/`: Flask backend structure
- `api_stuff/`: Node/Express API scripts, filter logic, API documentation
- `database-test/`: Supabase queries, test scripts
- `docs/`: Project documentation

## How to Run
1. Clone the repo and checkout the `prototype` branch
2. Install dependencies for frontend and backend
   - `cd frontend && npm install`
   - `cd backend && pip install -r requirements.txt`
   - `cd api_stuff && npm install`
3. Start frontend: `cd frontend && npm run dev`
4. Start backend: `cd backend && python app.py`
5. Start API server: `cd api_stuff && node api_with_filters.js`

## Contributors
- Sebastian Lassander (frontend, integration)
- Ethan Batick (API, docs)
- Will Manicom (database, queries)
- Jason Riek (backend, Flask)

