/**
 * fluence_demo_api.js (refactor + user filters)
 * ---------------------------------------------
 * Run:
 *   npm i express cors
 *   node fluence_demo_api.js
 *
 * Endpoints:
 *   GET /health
 *   GET /api/v1/heatmap/covid/countries
 *
 * Filters (query params):
 *   allowNull=true|false          -> forwarded to disease.sh
 *   yesterday=true|false          -> forwarded
 *   twoDaysAgo=true|false         -> forwarded
 *   sort=cases|deaths|recovered   -> forwarded (also used for local sorting if needed)
 *
 *   countries=US,CA,FR            -> request ONLY these countries (changes request path)
 *   minCases=10000                -> filters response
 *   minDeaths=100                 -> filters response
 *   minRecovered=500              -> filters response
 *   top=50                        -> keeps top N after filters (by sortBy)
 *
 *   intensityBy=cases|deaths|recovered   -> what drives heat intensity (default: cases)
 *   intensityScale=linear|log            -> scale before normalization (default: linear)
 *   normalize=global|local               -> global normalizes using max of full response set
 *                                          local normalizes after filters (default: global)
 */

const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = Number(process.env.PORT || 3000);
const DISEASE_SH = "https://disease.sh/v3/covid-19";

// Cache: per unique upstream URL (so filters create distinct cache keys)
const CACHE_TTL_MS = 2 * 60 * 1000; // 2 min
const cache = new Map(); // key -> { expiresAt, value }

// Node 18+ has global fetch. Provide a fallback for older Node.
async function getFetch() {
  if (typeof fetch === "function") return fetch;
  const mod = await import("node-fetch");
  return mod.default;
}

function nowIso() {
  return new Date().toISOString();
}

function toBool(v, defaultVal = false) {
  if (v === undefined || v === null) return defaultVal;
  const s = String(v).trim().toLowerCase();
  if (["1", "true", "t", "yes", "y", "on"].includes(s)) return true;
  if (["0", "false", "f", "no", "n", "off"].includes(s)) return false;
  return defaultVal;
}

function toNum(v, defaultVal = null) {
  if (v === undefined || v === null || v === "") return defaultVal;
  const n = Number(v);
  return Number.isFinite(n) ? n : defaultVal;
}

function clamp01(x) {
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}

function pickSortField(sort) {
  const s = String(sort || "").toLowerCase();
  if (s === "deaths") return "deaths";
  if (s === "recovered") return "recovered";
  return "cases";
}

function scaleValue(v, scale) {
  if (!Number.isFinite(v) || v <= 0) return 0;
  if (scale === "log") return Math.log10(v + 1);
  return v; // linear
}

function parseCountriesParam(countries) {
  if (!countries) return null;
  const list = String(countries)
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
  return list.length ? list : null;
}

function makeUpstreamUrl({ allowNull, yesterday, twoDaysAgo, sortBy, countriesList }) {
  const params = new URLSearchParams();
  params.set("allowNull", allowNull ? "true" : "false");
  if (yesterday) params.set("yesterday", "true");
  if (twoDaysAgo) params.set("twoDaysAgo", "true");
  // disease.sh supports sort on /countries endpoints
  if (sortBy) params.set("sort", sortBy);

  // If user specified countries, change request path to /countries/{countries}
  // (This is the “filters that change the request” part.)
  const path = countriesList ? `/countries/${encodeURIComponent(countriesList.join(","))}` : "/countries";
  return `${DISEASE_SH}${path}?${params.toString()}`;
}

function cacheGet(key) {
  const hit = cache.get(key);
  if (!hit) return null;
  if (Date.now() >= hit.expiresAt) {
    cache.delete(key);
    return null;
  }
  return hit.value;
}

function cacheSet(key, value) {
  cache.set(key, { value, expiresAt: Date.now() + CACHE_TTL_MS });
}

function normalizeRowsToPoints(rows, opts) {
  const {
    intensityBy = "cases",
    intensityScale = "linear",
    normalize = "global",
    minCases = null,
    minDeaths = null,
    minRecovered = null,
    sortBy = "cases",
    top = null,
  } = opts;

  // 1) map rows -> point candidates (drop missing lat/lng)
  let pts = rows
    .map((c) => {
      const lat = Number(c?.countryInfo?.lat);
      const lng = Number(c?.countryInfo?.long);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

      const cases = Number(c.cases || 0);
      const deaths = Number(c.deaths || 0);
      const recovered = Number(c.recovered || 0);

      return {
        id: c?.countryInfo?._id ? String(c.countryInfo._id) : String(c.country || ""),
        lat,
        lng,
        cases,
        deaths,
        recovered,
        location: {
          country: c.country || null,
          iso2: c?.countryInfo?.iso2 || null,
          iso3: c?.countryInfo?.iso3 || null,
        },
        updated: c.updated ? new Date(c.updated).toISOString() : null,
        _raw: c, // keep around if you later want more fields
      };
    })
    .filter(Boolean);

  // 2) apply min filters (response-only filters)
  if (minCases !== null) pts = pts.filter((p) => p.cases >= minCases);
  if (minDeaths !== null) pts = pts.filter((p) => p.deaths >= minDeaths);
  if (minRecovered !== null) pts = pts.filter((p) => p.recovered >= minRecovered);

  // 3) sort + top
  const sf = pickSortField(sortBy);
  pts.sort((a, b) => (b[sf] || 0) - (a[sf] || 0));
  if (top !== null) pts = pts.slice(0, top);

  // 4) compute intensity with optional scaling + normalization
  const valField = pickSortField(intensityBy);
  const valuesForMax =
    normalize === "local"
      ? pts.map((p) => scaleValue(p[valField], intensityScale))
      : rows
          .map((c) => {
            const v = Number(c?.[valField] || 0);
            return scaleValue(v, intensityScale);
          })
          .filter((v) => Number.isFinite(v));

  const maxVal = Math.max(1, ...valuesForMax);

  pts = pts.map((p) => {
    const v = scaleValue(p[valField], intensityScale);
    return {
      id: p.id,
      lat: p.lat,
      lng: p.lng,
      intensity: clamp01(v / maxVal),
      cases: p.cases,
      deaths: p.deaths,
      recovered: p.recovered,
      location: p.location,
      updated: p.updated,
    };
  });

  return pts;
}

app.get("/health", (req, res) => {
  res.json({ ok: true, service: "fluence-demo-api", time: nowIso() });
});

app.get("/api/v1/heatmap/covid/countries", async (req, res) => {
  try {
    // ---- parse filters ----
    const allowNull = toBool(req.query.allowNull, true);
    const yesterday = toBool(req.query.yesterday, false);
    const twoDaysAgo = toBool(req.query.twoDaysAgo, false);

    const countriesList = parseCountriesParam(req.query.countries);

    const sortBy = pickSortField(req.query.sort);
    const intensityBy = pickSortField(req.query.intensityBy);
    const intensityScale = String(req.query.intensityScale || "linear").toLowerCase() === "log" ? "log" : "linear";
    const normalize = String(req.query.normalize || "global").toLowerCase() === "local" ? "local" : "global";

    const minCases = toNum(req.query.minCases, null);
    const minDeaths = toNum(req.query.minDeaths, null);
    const minRecovered = toNum(req.query.minRecovered, null);

    const top = (() => {
      const n = toNum(req.query.top, null);
      if (n === null) return null;
      const clamped = Math.max(1, Math.min(500, Math.floor(n)));
      return clamped;
    })();

    // ---- build upstream URL (REQUEST CHANGES based on user filters) ----
    const upstreamUrl = makeUpstreamUrl({ allowNull, yesterday, twoDaysAgo, sortBy, countriesList });

    // ---- cache per upstream URL ----
    const cached = cacheGet(upstreamUrl);
    if (cached) return res.json(cached);

    const f = await getFetch();
    const r = await f(upstreamUrl);
    if (!r.ok) throw new Error(`disease.sh error ${r.status}`);

    const data = await r.json();

    // /countries/{list} can return either an array OR a single object if only one country matched
    const rows = Array.isArray(data) ? data : data ? [data] : [];

    const points = normalizeRowsToPoints(rows, {
      intensityBy,
      intensityScale,
      normalize,
      minCases,
      minDeaths,
      minRecovered,
      sortBy,
      top,
    });

    const out = {
      disease: "covid-19",
      scope: "countries",
      filters: {
        allowNull,
        yesterday,
        twoDaysAgo,
        countries: countriesList,
        sort: sortBy,
        intensityBy,
        intensityScale,
        normalize,
        minCases,
        minDeaths,
        minRecovered,
        top,
      },
      points,
      meta: {
        source: "disease.sh",
        upstream: upstreamUrl,
        generatedAt: nowIso(),
        cachedForMs: CACHE_TTL_MS,
      },
    };

    cacheSet(upstreamUrl, out);
    res.json(out);
  } catch (e) {
    res.status(500).json({ error: "Failed to build heatmap data", detail: String(e?.message || e) });
  }
});

app.listen(PORT, () => {
  console.log(`Fluence demo API: http://localhost:${PORT}`);
  console.log(`Heatmap endpoint: http://localhost:${PORT}/api/v1/heatmap/covid/countries`);
});

/*
Examples:
  # Only US + Canada (request path changes to /countries/US,CA), normalize locally, log scale
  curl "http://localhost:3000/api/v1/heatmap/covid/countries?countries=US,CA&normalize=local&intensityScale=log"

  # Filter out small countries, return top 50 by deaths, intensity driven by deaths
  curl "http://localhost:3000/api/v1/heatmap/covid/countries?minCases=100000&top=50&sort=deaths&intensityBy=deaths"

  # Yesterday's snapshot
  curl "http://localhost:3000/api/v1/heatmap/covid/countries?yesterday=true"
*/