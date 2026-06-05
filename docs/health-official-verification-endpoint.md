# Health Official Verification Endpoint

This document describes the backend endpoint used by the existing frontend verification form at `frontend/src/pages/HealthOfficialAuth.jsx`.

## Endpoint

`POST /api/auth/verify-official`

Submits a health official's credentials for manual review and stores the request in the `official_verifications` table.

## Request body

```json
{
  "full_name": "Dr. Jane Smith",
  "email": "jane.smith@health.gov",
  "license_number": "MD-123456",
  "issuing_state": "New York",
  "organization": "Syracuse Department of Health",
  "title": "Epidemiologist"
}
```

## Required fields

- `full_name`
- `email`
- `license_number`
- `issuing_state`
- `organization`

Each required field must be present and must be a non-empty string.

## Success response

The endpoint returns the standard backend success envelope with a frontend-friendly verification status and role.

```json
{
  "status": "success",
  "data": {
    "message": "Verification request submitted successfully.",
    "verification_status": "pending",
    "role": "pending_official"
  }
}
```

### Notes for frontend consumers

- `verification_status` is set to `pending` immediately after submission.
- `role` is set to `pending_official` so the UI can gate restricted workflows.
- Optional field `title` is stored when provided.

## Error responses

### Missing fields

```json
{
  "status": "error",
  "error": {
    "message": "Missing required fields",
    "details": {
      "missing": ["issuing_state", "license_number"]
    }
  }
}
```

### Blank required field

```json
{
  "status": "error",
  "error": {
    "message": "full_name must be a non-empty string"
  }
}
```

### Server failure

```json
{
  "status": "error",
  "error": {
    "message": "Failed to submit verification request",
    "details": "Database error details"
  }
}
```

## Related endpoints

- `GET /api/auth/verify-official/status?email=<email>` returns the latest verification status for role gating after login.
