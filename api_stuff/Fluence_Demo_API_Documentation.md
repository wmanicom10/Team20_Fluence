# 🦠 Fluence Demo API

Disease Heatmap Backend (Node.js + Express)

------------------------------------------------------------------------

## 📌 Overview

The Fluence Demo API is a lightweight backend service that:

-   Proxies public disease data from disease.sh
-   Normalizes case data into heatmap intensity values
-   Supports advanced user filters
-   Caches upstream requests
-   Returns frontend-ready geographic heatmap points

Designed for integration with: - Leaflet heatmaps - Mapbox heat layers -
Google Maps heatmap overlays - Custom ML risk visualizations

------------------------------------------------------------------------

# 🏗 Architecture

Client (Frontend) ↓ Fluence API (Express Server) ↓ disease.sh Public API

------------------------------------------------------------------------

# 🚀 Setup

## Requirements

-   Node.js 18+
-   npm

Verify installation:

    node -v

------------------------------------------------------------------------

## Installation

    npm init -y
    npm install express cors

------------------------------------------------------------------------

## Running the Server

    node fluence_demo_api.js

Server runs at:

    http://localhost:3000

------------------------------------------------------------------------

# 🔎 Endpoints

## GET /health

Health check endpoint.

Response:

{ "ok": true, "service": "fluence-demo-api", "time": "ISO timestamp" }

------------------------------------------------------------------------

## GET /api/v1/heatmap/covid/countries

Returns country-level COVID heatmap points.

### Example

    http://localhost:3000/api/v1/heatmap/covid/countries

------------------------------------------------------------------------

# 🎛 Query Parameters

## Upstream Filters (Change disease.sh Request)

  Parameter                       Description
  ------------------------------- ---------------------------------
  countries=US,CA                 Only request specific countries
  yesterday=true                  Get yesterday's snapshot
  twoDaysAgo=true                 Get two days ago snapshot
  sort=cases\|deaths\|recovered   Sort upstream results

------------------------------------------------------------------------

## Response Filters (Processed in Fluence API)

  Parameter           Description
  ------------------- -----------------------------
  minCases=100000     Minimum case threshold
  minDeaths=1000      Minimum death threshold
  minRecovered=5000   Minimum recovered threshold
  top=50              Return top N results

------------------------------------------------------------------------

## Heatmap Intensity Controls

  Parameter                              Description
  -------------------------------------- --------------------------------------
  intensityBy=cases\|deaths\|recovered   Field used for heat intensity
  intensityScale=linear\|log             Scaling before normalization
  normalize=global\|local                Normalize across all or filtered set

------------------------------------------------------------------------

# 📦 Response Structure

{ "disease": "covid-19", "scope": "countries", "filters": { ... },
"points": \[ { "id": "840", "lat": 37.09, "lng": -95.71, "intensity":
0.82, "cases": 1000000, "deaths": 15000, "recovered": 800000,
"location": { "country": "USA", "iso2": "US", "iso3": "USA" },
"updated": "ISO timestamp" } \], "meta": { "source": "disease.sh",
"generatedAt": "ISO timestamp", "cachedForMs": 120000 } }

------------------------------------------------------------------------

# 🧠 Caching

-   Cache duration: 2 minutes
-   Cache key: Upstream URL (based on filters)

------------------------------------------------------------------------

# 🛡 Error Handling

On failure:

{ "error": "Failed to build heatmap data", "detail": "error message" }

------------------------------------------------------------------------

# 📈 Example Requests

Only US and Canada:

    /api/v1/heatmap/covid/countries?countries=US,CA

Top 20 by deaths:

    /api/v1/heatmap/covid/countries?sort=deaths&top=20

Log intensity scaling:

    /api/v1/heatmap/covid/countries?intensityScale=log

------------------------------------------------------------------------

# 🏁 Production Notes

-   Add rate limiting for public deployment
-   Add environment-based configuration
-   Consider Redis for distributed caching
-   Add authentication for secured deployments

------------------------------------------------------------------------

© Fluence Project
