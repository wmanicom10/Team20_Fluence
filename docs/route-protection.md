# Route Protection Architecture — TM20-90

## Overview

This document describes the routing architecture and protection behavior implemented in Sprint 6 (TM20-90). All routes are defined in `frontend/src/App.jsx` and use `ProtectedRoute` from `frontend/src/components/ProtectedRoute.jsx` for authentication gating.

## Route Map

| Route | Component | Auth Required | Notes |
|:------|:----------|:-------------|:------|
| `/` | `Home` | No | Public landing page |
| `/data` | `DiseaseDataView` | No | Public disease data browser |
| `/map` | `MapView` | No | Public outbreak map |
| `/login` | `Login` | No | Login form |
| `/signup` | `Signup` | No | Registration form |
| `/forgot-password` | `ForgotPassword` | No | Password reset request |
| `/reset-password` | `ResetPassword` | No | Password reset form (Supabase link) |
| `/verify-email` | `VerifyEmail` | No | Email verification guidance |
| `/verify` | `HealthOfficialAuth` | **Yes** | Health official credential submission |
| `/submit` | `CaseSubmission` | **Yes** | Case submission (also requires official verification) |
| `*` (catch-all) | `NotFound` | No | 404 page for undefined routes |

## ProtectedRoute Behavior

**Component:** `frontend/src/components/ProtectedRoute.jsx`

```
ProtectedRoute({ children, redirectTo = '/login' })
```

1. **Loading state**: While Supabase is checking the session (initial page load), shows a loading indicator. Prevents flash-of-unauthenticated-content.
2. **Unauthenticated**: Redirects to `/login` (or custom `redirectTo` prop). Uses `<Navigate replace />` to avoid polluting browser history.
3. **Authenticated**: Renders the wrapped child component.

## Route Conflicts Resolved

**Problem (pre-TM20-90):** `App.jsx` contained two declarations for `/submit`:
```jsx
// BEFORE — duplicate route
<Route path="/submit" element={<CaseSubmission />} />
<Route path="/submit" element={<ProtectedRoute><CaseSubmission /></ProtectedRoute>} />
```

React Router matches the first declaration, so the unprotected version was active. The ProtectedRoute wrapper was never reached.

**Fix:** Removed the duplicate unprotected route. Single `/submit` route now uses `ProtectedRoute` guard consistently.

## Test Scenarios

| Scenario | Expected Behavior | Status |
|:---------|:-----------------|:-------|
| Unauthenticated user visits `/submit` | Redirected to `/login` | ✅ Verified |
| Unauthenticated user visits `/verify` | Redirected to `/login` | ✅ Verified |
| Authenticated user visits `/submit` | CaseSubmission page loads (with verification gate) | ✅ Verified |
| Authenticated user visits `/verify` | HealthOfficialAuth form loads | ✅ Verified |
| User visits `/nonexistent-page` | NotFound 404 page shown | ✅ Verified |
| Page load while session is being checked | Loading indicator shown, no content flash | ✅ Verified |
| Public routes (`/`, `/data`, `/map`) | Accessible without auth | ✅ Verified |

## Files Changed

- `frontend/src/App.jsx` — route declarations, protection wrapping, 404 catch-all
- `frontend/src/components/ProtectedRoute.jsx` — loading state, redirect logic
- `frontend/src/pages/NotFound.jsx` — 404 page component (new)
