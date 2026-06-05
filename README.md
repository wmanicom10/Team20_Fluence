# Team20_Fluence

## Project Overview

Fluence is a public health disease surveillance web application developed for CIS454. It allows users to explore disease data by location and time, view trends, and submit case information. The system integrates a React/Vite frontend, Flask backend, Supabase database, and external disease APIs.

---

## Branch Structure

* prototype: final integrated version of the project
* main: earlier backend and API work
* docs: earlier frontend and database work

---

## Repository Structure

```
├── frontend/          # React/Vite app (map, filters, data views, case submission, auth)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── data/
│   └── public/
├── backend/           # Flask API server + Supabase integration
│   ├── app.py
│   ├── routes.py
│   ├── db.py
│   ├── config.py
│   └── proof-of-concept.py
├── api_stuff/         # Node/Express API scripts
├── database-test/     # Supabase queries and SQL tests
├── docs/              # documentation and artifacts
│   ├── initial-database-schema.md
│   ├── Fluence_Demo_API_Documentation.md
│   ├── Fluence_AI_Model_Research_Document.docx
│   ├── Fluence_API_to_Supabase_Integration_Documentation.docx
│   ├── Fluence Coding Conventions.pdf
│   ├── coding-standards-evidence.md
│   └── ...
└── .gitignore
```

---

## How to Run

1. Clone the repo and checkout the prototype branch

```
git clone <repo-url>
git checkout prototype
```

2. Install dependencies

```
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
cd ../api_stuff && npm install
```

3. Set environment variables

```
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
```

4. Start services

Frontend:

```
cd frontend
npm run dev
```

Backend:

```
cd backend
python app.py
```

API:

```
cd api_stuff
node api_with_filters.js
```

---

## Documentation

All supporting materials are in the docs folder.

This includes:

* API documentation
* database schema
* AI research and integration notes
* performance and testing documentation
* coding standards evidence

Coding standards evidence:

```
docs/coding-standards-evidence.md
```

---

## Coding Standards

The project follows consistent conventions across all parts of the codebase.

* Python backend uses standard formatting and modular structure
* React frontend is organized into components and pages
* API endpoints follow consistent naming and response formats
* ESLint is used to keep frontend code consistent

Details are documented in the coding standards evidence file.

---

## Contributors

* Sebastian Lassander
* Ethan Batick
* Will Manicom
* Jason Riek

---

## Summary

Fluence is a full-stack application that combines a frontend interface, backend API, database integration, and external data sources. It demonstrates how these pieces work together to support a data-driven application.
