# Fluence Frontend Architecture & Component Map

This document outlines the architecture, routing, component structure, and backend integration strategy for the Fluence React/Vite frontend application.

## 1. Routing & Pages

The application utilizes `react-router-dom` for client-side routing. The application is split into public routes (accessible to anyone) and protected routes (accessible only to authenticated users).

### Public Routes
* **`/` (Home)**: The landing page introducing the Fluence platform with calls to action.
* **`/data` (DiseaseDataView)**: Main dashboard for viewing aggregated disease statistics, trends, and AI risk summaries.
* **`/map` (MapView)**: Interactive Leaflet map displaying heatmaps and global case pin clusters. Auto-centers to ensure markers are always globally visible.
* **`/login` (Login)**: User authentication entry point. Connects to Supabase Auth.
* **`/signup` (Signup)**: New user registration page.
* **`/forgot-password` (ForgotPassword)**: Initiates Supabase password reset flow.
* **`/reset-password` (ResetPassword)**: Form to securely update password after receiving an email link.
* **`/verify-email` (VerifyEmail)**: Guidance page displayed after sign-up requesting the user to verify their email address.
* **`*` (NotFound)**: Catch-all 404 page for undefined routes.

### Protected Routes
Protected routes are wrapped by the `<ProtectedRoute>` component, which redirects unauthenticated users to `/login`.
* **`/verify` (HealthOfficialAuth)**: Secure form where users can submit their credentials (license numbers, organization) to become a verified Health Official.
* **`/submit` (CaseSubmission)**: Secure form restricted to verified Health Officials. Allows submission of new disease case reports (disease type, lat/lng location, severity).

---

## 2. Shared Components

The `src/components/` directory holds reusable UI elements used across multiple pages.

* **`<Navbar />`**: The top navigation bar present on all routes. Handles responsive mobile menus and conditional rendering based on authentication state (e.g., showing a "Logout" button instead of "Login" when authenticated).
* **`<ProtectedRoute />`**: An authentication guard component that wraps sensitive routes. It checks the current session state via `AuthContext` and prevents flash-of-content while auth state resolves.
* **`<AiRiskSummary />`**: A dashboard widget used on the Data View page. Fetches and displays AI-driven neural network risk models (Risk Level, Scores) based on current active locations and diseases.
* **`<DiseaseCard />`**: A generic card container used to display high-level stats for a specific disease or data point (such as total cases, or CDC respiratory data points).
* **`<DiseaseTable />`**: A structured table component used for listing rows of case data with sortable columns for disease names, locations, severities, and trends.

---

## 3. Backend Integration & API Connectivity

The frontend connects to the Flask API backend (which proxies requests or talks directly to Supabase). 

* **API Base URL**: Configured via environment variables, defaulting to `http://localhost:5000/api` during local development.
* **Authentication**: The frontend uses `@supabase/supabase-js` to directly issue login/signup requests to Supabase (utilizing PKCE flow). It sets an active local session that is sent via JWT Bearer tokens to secure backend endpoints.

### Key API Endpoints Used
1. **`GET /api/ui/disease-data`**: Fetched by `DiseaseDataView.jsx` to populate dashboards. Cached heavily by the backend.
2. **`GET /api/ui/ai-risk`**: Fetched by `AiRiskSummary.jsx` to display current situational risk levels.
3. **`GET /api/ui/cdc-respiratory`**: Fetched by data views to list live CDC NSSP surveillance cases.
4. **`POST /api/cases`**: Hit by `CaseSubmission.jsx` to register a new reported illness.
5. **`GET /api/auth/verify-official/status`**: Hit by the `AuthContext` post-login to determine if the user has Health Official privileges, gating the `/submit` route.

---

## 4. Offline Resiliency & Fallback Architecture

To guarantee maximum uptime and a flawless demonstration even when the primary Supabase free-tier database is unreachable or paused, the frontend implements an **Offline Fallback Architecture**.

**How it works:**
Whenever a critical data-fetching or auth component (like `DiseaseDataView`, `MapView`, `AiRiskSummary`, `Login`, `CaseSubmission`) encounters a network timeout, `HTTP 500`, or `[Errno 11001]` DNS failure from the backend, a `catch` block intercepts the failure.

Instead of crashing or displaying infinite loading spinners, the app seamlessly defaults to in-memory **Mock Data**:
* **Dashboard & Map**: Populates with 10 hardcoded mock case pins distributed globally and sets the stats to a static (but realistic) snapshot.
* **Login/Signup**: Bypasses real Supabase auth, setting a fake functional session in context and proceeding to the protected routes.
* **Case Submission**: Intercepts the form POST and successfully completes the transaction in-memory.

> [!NOTE]  
> This feature ensures the frontend user experience remains 100% functional during stakeholder demos regardless of backend outages. When the backend recovers, real live data is automatically fetched upon the next navigation.
