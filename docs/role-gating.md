# Role Sync & Health-Official Feature Gating — TM20-89

## Overview

This document describes the role synchronization and feature gating architecture implemented in Sprint 6 (TM20-89). After a user logs in, the frontend checks their health-official verification status from the backend and gates access to restricted features accordingly.

## Architecture

```
Login/Session → AuthContext checks verification status → role + isVerifiedOfficial state
                                                          ↓
                                 CaseSubmission reads state → gates form or shows CTA
```

### AuthContext (`frontend/src/context/AuthContext.jsx`)

On login or session restore, `AuthContext` performs these steps:

1. Sets `user` from Supabase session
2. Calls `GET /api/auth/verify-official/status?email=<user_email>`
3. Parses the response and sets:
   - `role`: `"health_official"`, `"pending_official"`, or `"user"`
   - `isVerifiedOfficial`: `true` or `false`
4. On logout, resets both to defaults (`"user"`, `false`)

**State exposed to all components via `useAuth()` hook:**

| Field | Type | Description |
|:------|:-----|:------------|
| `user` | Object/null | Supabase user object |
| `loading` | boolean | True while session is being checked |
| `role` | string | `"health_official"`, `"pending_official"`, or `"user"` |
| `isVerifiedOfficial` | boolean | True only if verified |
| `logout` | function | Signs out and resets state |

### Backend Status Endpoint (`GET /api/auth/verify-official/status`)

**Query parameters:** `email` (required)

**Response shape:**
```json
{
  "status": "success",
  "data": {
    "verification_status": "verified" | "pending" | "none",
    "role": "health_official" | "pending_official" | "user"
  }
}
```

**Logic:**
1. Queries `official_verifications` table by email
2. Returns most recent record's `verified` field
3. If no record exists, returns `"none"` / `"user"`

## Feature Gating in CaseSubmission

**Component:** `frontend/src/pages/CaseSubmission.jsx`

### Gate logic:

```
isVerifiedOfficial === true  → Show full case submission form
role === "pending_official"  → Show "pending review" message + CTA to /verify
role === "user"              → Show "verification required" message + CTA to /verify
```

### User Experience by Verification State

| State | What User Sees |
|:------|:--------------|
| **Not verified** | Yellow banner: "Only verified health officials can submit disease case reports." + CTA button "Verify Your Credentials" → `/verify` |
| **Pending** | Yellow banner: "Your verification request is pending review." + CTA button "Check Verification Status" → `/verify` |
| **Verified** | Full case submission form with all fields |

## Protection Layers

Case submission has **two layers** of protection:

1. **ProtectedRoute (TM20-90):** Unauthenticated users redirected to `/login`
2. **Verification Gate (TM20-89):** Authenticated but non-verified users see guidance banner instead of form

This ensures that a user must be both logged in AND verified to submit case reports.

## Test Scenarios

| Scenario | Expected Behavior | Status |
|:---------|:-----------------|:-------|
| Non-logged-in user visits `/submit` | Redirected to `/login` by ProtectedRoute | ✅ Verified |
| Logged-in user with no verification record | Sees "Verification Required" banner + CTA | ✅ Verified |
| Logged-in user with pending verification | Sees "Pending Review" message + CTA | ✅ Verified |
| Logged-in verified health official | Sees full case submission form | ✅ Verified |
| User logs out then back in | Role/verification state re-checked from backend | ✅ Verified |

## Files Changed

- `frontend/src/context/AuthContext.jsx` — role + verification state, backend status check
- `frontend/src/pages/CaseSubmission.jsx` — verification gate UI + CTA
- `backend/routes.py` — `GET /api/auth/verify-official/status` endpoint
