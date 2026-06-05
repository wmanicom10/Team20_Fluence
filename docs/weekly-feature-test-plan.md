# Fluence Weekly Feature Test Plan

Date: 2026-03-17

## Goal

Test the features that are implemented enough to be considered complete, record their current status, and separate those from placeholder or still-in-progress flows.

## Completed Feature Scope

These areas appear complete enough to test this week:

- Frontend navigation and page routing
- Home page
- Disease Data Dashboard (`/data`)
- Map View (`/map`)
- Case Submission flow (`/submit`)
- Backend disease, location, case, UI, health, and metrics endpoints

These areas are not complete and should be tracked as UI placeholders, not full feature tests:

- Login (`/login`) only logs to console and redirects home
- Signup (`/signup`) only validates password match, logs to console, and redirects home
- Health Official Verification (`/verify`) simulates success and is marked for future backend wiring

## Automated Checks Run

Run on 2026-03-17 in the local workspace:

- `frontend`: `npm run lint` -> PASS
- `frontend`: `npm run build` -> PASS

Not fully executed here:

- `backend`: Python-based runtime checks could not be run because Python is not installed on this machine
- `database-test`: existing scripts were not run because they depend on Supabase access and some of them insert live records

## Test Matrix

Use `PASS`, `FAIL`, or `BLOCKED` in the Status column as you work.

| Area | Test | Expected Result | Status | Notes |
| --- | --- | --- | --- | --- |
| Navigation | Open `/` and use navbar links | All links render and route correctly without blank screens | TODO | |
| Navigation | Refresh on `/data`, `/map`, `/submit`, `/verify`, `/login`, `/signup` | Direct route loads without client-side crash | TODO | |
| Home | Open home page | Hero text, CTA, and feature cards render | TODO | |
| Home | Click `View Disease Data` CTA | Navigates to `/data` | TODO | |
| Disease Data | Load `/data` with backend running | Disease types load, dashboard data renders, no uncaught errors | TODO | |
| Disease Data | Switch between Cards and Table view | Same dataset is visible in both views | TODO | |
| Disease Data | Change disease filter | Results update to selected disease | TODO | |
| Disease Data | Change sort field and order | Data reorders correctly | TODO | |
| Disease Data | Use disease with no matching data | Empty-state message appears | TODO | |
| Disease Data | Stop backend or break API URL | Error-state message appears | TODO | |
| Map View | Load `/map` with backend running | Map renders, disease filter loads, markers appear when data exists | TODO | |
| Map View | Filter by disease | Marker count and popup set update | TODO | |
| Map View | Apply valid date range | Marker set reflects filtered date range | TODO | |
| Map View | Set start date later than end date | Validation message appears and no data is shown | TODO | |
| Map View | Click `Clear Filters` | Disease and date filters reset | TODO | |
| Map View | Use filters with no matching cases | Empty-state message appears | TODO | |
| Case Submission | Submit with missing required fields | Inline validation prevents submit | TODO | |
| Case Submission | Submit with `Date From > Date To` | Inline validation error appears | TODO | |
| Case Submission | Submit valid case for existing disease and existing location | Success message appears and form resets | TODO | Requires backend + writable database |
| Case Submission | Submit valid case for existing disease and new location | Location is created, case is created, success message appears | TODO | Requires backend + writable database |
| Case Submission | Submit disease not present in backend database | User sees disease lookup failure message | TODO | |
| API Health | `GET /api/health` | Returns success payload and database connectivity status | TODO | Requires Python runtime |
| API Diseases | `GET /api/diseases` | Returns disease list ordered by name | TODO | |
| API Diseases | `POST /api/diseases` with valid body | Creates disease and returns success payload | TODO | Writes to DB |
| API Diseases | `POST /api/diseases` with missing fields | Returns 400 with error payload | TODO | |
| API Locations | `GET /api/locations` with filters | Returns matching locations only | TODO | |
| API Locations | `POST /api/locations` valid body | Creates location and returns success payload | TODO | Writes to DB |
| API Cases | `GET /api/cases` | Returns case rows with disease and location joins | TODO | |
| API Cases | `GET /api/cases?verified_only=true` | Only verified records returned | TODO | |
| API Cases | `GET /api/cases` invalid dates | Returns 400 error payload | TODO | |
| API Cases | `POST /api/cases` valid body | Creates case and returns 201 | TODO | Writes to DB |
| API Cases | `POST /api/cases` negative `case_count` | Returns 400 validation error | TODO | |
| API Cases | `PATCH /api/cases/<id>` valid body | Updates selected fields | TODO | Writes to DB |
| API Cases | `DELETE /api/cases/<id>` | Deletes case and returns success | TODO | Writes to DB |
| API UI | `GET /api/ui/disease-types` | Returns `All Diseases` plus active diseases | TODO | |
| API UI | `GET /api/ui/disease-data` | Returns frontend-ready dashboard rows | TODO | |
| API Metrics | `GET /api/metrics/cases-by-disease` | Returns totals grouped by disease | TODO | |

## Recommended Test Order

1. Run backend and frontend locally.
2. Smoke test navigation and page rendering.
3. Test dashboard and map because they are read-only and quickest to verify.
4. Test case submission next because it exercises disease lookup, location lookup or creation, and case creation.
5. Test backend endpoints directly with Postman or curl for validation and error handling.
6. Record placeholder flows separately so they do not get reported as completed regressions.

## Suggested Evidence To Capture

- Screenshots of `/`, `/data`, `/map`, and `/submit`
- One screenshot for each empty-state or error-state message
- Request and response samples for backend validation failures
- A short defect list with reproduction steps and affected route

## Known Risks And Notes

- `Login`, `Signup`, and `Health Official Verification` are not backend-complete, so they should be reported as placeholder flows
- `Case Submission` depends on backend data integrity and a writable database
- `database-test/test-database.js` inserts records into Supabase, so use it carefully in a shared environment
- Backend execution is currently blocked on this machine because Python is not installed
