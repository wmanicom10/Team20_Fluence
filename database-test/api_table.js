import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = "https://rogzdnrmmsdlpxjbgtvj.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_yinNcPmYmUIaIGSpkNJCjQ_vPxrnSbZ";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const DEFAULT_TTL_HOURS = 1;

// ── Cache operations ───────────────────────────────────────────

async function getCache(endpoint, params) {
  const { data, error } = await supabase
    .from("health_api_cache")
    .select("response_body")
    .eq("endpoint", endpoint)
    .eq("params", JSON.stringify(params))
    .gt("expires_at", new Date().toISOString())
    .limit(1)
    .single();

  if (error) { console.error("getCache error:", error.message); return null; }
  if (!data) { console.log("getCache: no rows found"); return null; }
  return data.response_body;
}

async function setCache(endpoint, params, responseBody, ttlHours = DEFAULT_TTL_HOURS) {
  const expiresAt = new Date();
  expiresAt.setHours(expiresAt.getHours() + ttlHours);

  const { error } = await supabase
    .from("health_api_cache")
    .insert({
      endpoint,
      params,
      response_body: responseBody,
      expires_at: expiresAt.toISOString(),
    });

  if (error) console.error("Cache write failed:", error.message);
}

async function purgeExpiredCache() {
  const { error } = await supabase
    .from("health_api_cache")
    .delete()
    .lt("expires_at", new Date().toISOString());

  if (error) console.error("Cache purge failed:", error.message);
  else console.log("Expired cache entries purged.");
}

async function fetchWithCache(endpoint, params, apiFn, ttlHours = DEFAULT_TTL_HOURS) {
  const cached = await getCache(endpoint, params);
  if (cached) {
    console.log("Cache hit:", endpoint);
    return cached;
  }

  console.log("Cache miss:", endpoint);
  const freshData = await apiFn();
  await setCache(endpoint, params, freshData, ttlHours);
  return freshData;
}

// ── Run demo ───────────────────────────────────────────────────

async function main() {
  const endpoint = "/fhir/r4/Observation";
  const params = { patient: "123" };
  const mockResponse = { resourceType: "Observation", status: "final", value: 98.6 };

  // 1. Write to cache
  console.log("Writing to cache...");
  await setCache(endpoint, params, mockResponse, 1);
  console.log("Cache entry written.");

  // 2. Read from cache
  console.log("\nReading from cache...");
  const cached = await getCache(endpoint, params);
  console.log("Cached result:", cached);

  // 3. fetchWithCache (should hit cache this time)
  console.log("\nfetchWithCache (should be a cache hit)...");
  const result = await fetchWithCache(endpoint, params, async () => mockResponse);
  console.log("Result:", result);

  // 4. Purge expired entries
  console.log("\nPurging expired cache entries...");
  await purgeExpiredCache();
}

main();