/**
 * fluence_demo_api.js
 * -------------------
 * Demo Fluence backend that proxies disease.sh and returns heatmap points.
 *
 * Run:
 *   npm i express cors
 *   node fluence_demo_api.js
 *
 * Endpoints:
 *   GET /health
 *   GET /api/v1/heatmap/covid/countries
 */

const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = Number(process.env.PORT || 3000);

// disease.sh base (no auth)
const DISEASE_SH = "https://disease.sh/v3/covid-19";

// tiny cache to avoid hammering the public API
const CACHE_TTL_MS = 2 * 60 * 1000; // 2 min
let cache = { expiresAt: 0, value: null };

function clamp01(x) {
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}

app.get("/health", (req, res) => {
  res.json({ ok: true, service: "fluence-demo-api", time: new Date().toISOString() });
});

/**
 * Heatmap points by country (lat/lng included)
 * Output shape:
 * {
 *   disease: "covid-19",
 *   scope: "countries",
 *   points: [{ id, lat, lng, intensity, cases, deaths, recovered, location:{country, iso2, iso3}, updated }],
 *   meta: { source, generatedAt }
 * }
 */
app.get("/api/v1/heatmap/covid/countries", async (req, res) => {
  try {
    // cache
    if (cache.value && Date.now() < cache.expiresAt) return res.json(cache.value);

    const url = `${DISEASE_SH}/countries?allowNull=true`;
    const r = await fetch(url);
    if (!r.ok) throw new Error(`disease.sh error ${r.status}`);

    const rows = await r.json();
    const maxCases = Math.max(1, ...rows.map((x) => Number(x.cases || 0)));

    const points = rows
      .map((c) => {
        const lat = Number(c?.countryInfo?.lat);
        const lng = Number(c?.countryInfo?.long);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

        const cases = Number(c.cases || 0);
        return {
          id: c?.countryInfo?._id ? String(c.countryInfo._id) : c.country,
          lat,
          lng,
          cases,
          deaths: Number(c.deaths || 0),
          recovered: Number(c.recovered || 0),
          // simple normalization for heatmap
          intensity: clamp01(cases / maxCases),
          location: {
            country: c.country,
            iso2: c?.countryInfo?.iso2 || null,
            iso3: c?.countryInfo?.iso3 || null,
          },
          updated: c.updated ? new Date(c.updated).toISOString() : null,
        };
      })
      .filter(Boolean);

    const out = {
      disease: "covid-19",
      scope: "countries",
      points,
      meta: {
        source: "disease.sh",
        generatedAt: new Date().toISOString(),
      },
    };

    cache = { value: out, expiresAt: Date.now() + CACHE_TTL_MS };
    res.json(out);
  } catch (e) {
    res.status(500).json({ error: "Failed to build heatmap data", detail: String(e?.message || e) });
  }
});

app.listen(PORT, () => {
  console.log(`Fluence demo API: http://localhost:${PORT}`);
  console.log(`Heatmap endpoint: http://localhost:${PORT}/api/v1/heatmap/covid/countries`);
});
