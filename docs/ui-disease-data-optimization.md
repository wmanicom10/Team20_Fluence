# UI Disease Data Endpoint Optimization

Documents the performance optimization applied to `GET /api/ui/disease-data` in Sprint 8 (TM20-119).

## What Changed

### In-Memory TTL Cache

Repeated requests with the same filter combination now return cached results instead of re-querying Supabase and re-running Python-side aggregation.

- **Cache key:** MD5 hash of `disease|startDate|endDate|verified_only` parameters.
- **TTL:** 30 seconds (configurable via `UI_DISEASE_DATA_CACHE_TTL` in `routes.py`).
- **Cache location:** Module-level `_ui_disease_data_cache` dictionary in `routes.py`.
- **Invalidation:** Entries expire after TTL. No manual invalidation is needed for normal use. The cache is reset when the backend process restarts.

### Cache-Control Response Headers

Every response from the endpoint now includes:

```http
Cache-Control: public, max-age=30
X-Cache: HIT   (or MISS on first request for a filter combo)
```

This allows the browser to skip re-fetching unchanged data within the TTL window, reducing both network traffic and perceived latency.

### Optional `limit` Parameter

A new optional `limit` query parameter lets the frontend request fewer rows:

```http
GET /api/ui/disease-data?limit=10
```

- Must be a positive integer (`>= 1`).
- Applied after sorting, so the top-N results are returned.
- Useful for summary widgets that only need a few rows.

## What Did NOT Change

- **Response JSON shape:** The `data` array structure is identical. No frontend changes required.
- **Filter behavior:** `disease`, `startDate`, `endDate`, `verified_only` all work the same way.
- **Default verified filter:** Still defaults to `verified=true` when `verified_only` is not provided.
- **Sorting:** Results are still sorted by `caseCount` descending.

## How to Verify

### Check cache behavior

```bash
# First request (cache miss)
curl -v "http://127.0.0.1:5000/api/ui/disease-data"
# Look for: X-Cache: MISS

# Second identical request within 30s (cache hit)
curl -v "http://127.0.0.1:5000/api/ui/disease-data"
# Look for: X-Cache: HIT
```

### Check limit parameter

```bash
curl "http://127.0.0.1:5000/api/ui/disease-data?limit=3"
# Returns at most 3 items in the data array
```

### Existing tests

```bash
cd backend
python -m pytest test_data_routes.py -v
```

All existing tests should continue to pass since the response format is unchanged.

## Configuration

| Variable | Location | Default | Description |
|:---|:---|:---|:---|
| `UI_DISEASE_DATA_CACHE_TTL` | `routes.py` | `30` | Cache time-to-live in seconds |

## Technical Notes

- The cache is per-process. If running multiple backend workers, each worker maintains its own cache. This is acceptable for Fluence's current scale.
- Input validation (date format, boolean parsing, limit parsing) happens **before** the cache lookup so invalid requests never pollute the cache.
- The cache stores the full formatted result set; the `limit` parameter slices from the cached copy, so different `limit` values for the same filters share one cache entry.
