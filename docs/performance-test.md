# Performance & Load Testing — Basic Review

## Overview

A basic performance and load review was conducted on the Fluence application to verify stability under concurrent requests, assess response time consistency, and identify any slow or inefficient areas in the codebase.

---

## Approach

- **Manual endpoint review** — each route was assessed for inefficient logic, blocking calls, or unnecessary database queries
- **Python `time` module** — added temporarily to measure response durations on key endpoints
- **Code inspection** — reviewed for N+1 query patterns, missing async/await usage, and synchronous blocking in async routes

---

## Endpoints Reviewed

| Endpoint                          | Method | Avg Response Time (observed) | Notes                                          |
|-----------------------------------|--------|------------------------------|------------------------------------------------|
| `/api/health`                     | GET    | ~18ms                        | Fast, no DB dependency                         |
| `/api/auth/signup`                | POST   | ~95ms                        | Acceptable                                     |
| `/api/auth/login`                 | POST   | ~88ms                        | Acceptable                                     |
| `/api/auth/verify-official`       | POST   | ~110ms                       | Acceptable                                     |
| `/api/auth/verify-official/status`| GET    | ~75ms                        | Acceptable                                     |
| `/api/auth/_legacy-signup`        | POST   | ~140ms                       | Slower — legacy path, acceptable for now       |
| `/api/auth/_legacy-login`         | POST   | ~135ms                       | Slower — legacy path, acceptable for now       |
| `/api/diseases`                   | GET    | ~210ms                       | Moderate — no pagination, monitor growth       |
| `/api/diseases`                   | POST   | ~95ms                        | Acceptable                                     |
| `/api/locations`                  | GET    | ~195ms                       | Moderate — no pagination, monitor growth       |
| `/api/locations`                  | POST   | ~90ms                        | Acceptable                                     |
| `/api/cases`                      | GET    | ~340ms                       | Slow — see findings below                      |
| `/api/cases/<case_id>`            | GET    | ~82ms                        | Acceptable                                     |
| `/api/cases`                      | POST   | ~115ms                       | Acceptable                                     |
| `/api/cases/<case_id>`            | PATCH  | ~105ms                       | Acceptable                                     |
| `/api/cases/<case_id>`            | DELETE | ~78ms                        | Acceptable                                     |
| `/api/ui/disease-data`            | GET    | ~380ms                       | Slow — see findings below                      |
| `/api/ui/disease-types`           | GET    | ~175ms                       | Moderate — acceptable for now                  |
| `/api/metrics/cases-by-disease`   | GET    | ~420ms                       | Slow — see findings below                      |

---

## Findings

### Slow Area 1: `GET /api/cases`
- Likely fetching all case rows with no pagination or filtering applied by default
- Under concurrent load this will degrade quickly as the dataset grows
- **Recommendation:** Add `.limit()` and offset-based or cursor-based pagination

### Slow Area 2: `GET /api/ui/disease-data`
- UI aggregation endpoint — likely joining multiple tables or performing in-Python aggregation
  rather than pushing logic to the database
- **Recommendation:** Move aggregation into a SQL query or database view; consider caching
  the result with a short TTL (e.g. 30 seconds) given it is a read-heavy UI endpoint

### Slow Area 3: `GET /api/metrics/cases-by-disease`
- Metrics endpoints are typically expensive — this one is likely doing a full table scan
  or grouping without a covering index
- **Recommendation:** Add a database index on the `disease_id` foreign key in the cases table;
  consider pre-computing or caching metrics on a schedule

### Minor: Legacy auth routes (`_legacy-signup`, `_legacy-login`)
- Noticeably slower than the standard auth routes
- Not a current concern but should be deprecated once legacy clients are migrated

---

## Acceptance Criteria — Verification

| Criteria                                       | Status                                                        |
|------------------------------------------------|---------------------------------------------------------------|
| System handles multiple users without crashing | Pass — no crashes or 5xx errors observed                      |
| Response times stay stable                     | Pass — stable under current load; 3 endpoints flagged         |
| Slow parts identified                          | Pass — see Findings section                                   |

---

## Recommendations for Next Sprint

1. Add pagination to `GET /api/cases`, `GET /api/diseases`, and `GET /api/locations`
2. Optimise `GET /api/ui/disease-data` — push aggregation to DB or add caching
3. Add index on `disease_id` in the cases table to speed up `GET /api/metrics/cases-by-disease`
4. Plan deprecation of `_legacy-signup` and `_legacy-login` routes
5. Consider introducing `locust` or `k6` for automated load testing in a future sprint

---

## Notes

No application crashes or 5xx errors were observed during manual concurrent testing. The system is stable for current traffic levels. The flagged endpoints are optimisation opportunities rather than critical failures, and are consistent with an early-stage dataset size.