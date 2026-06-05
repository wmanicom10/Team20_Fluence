# Health API Cache — Supabase Setup

Cache API responses in a Supabase table. 

---

## 1. Created the Table

```sql
create table health_api_cache (
  id            uuid primary key default gen_random_uuid(),
  endpoint      text not null,
  params        jsonb not null default '{}',
  response_body jsonb not null,
  created_at    timestamptz not null default now(),
  expires_at    timestamptz not null
);

create index on health_api_cache (endpoint);
create index on health_api_cache (expires_at);
```

## 2. Enabled Row Level Security

```sql
alter table health_api_cache enable row level security;

create policy "Allow all operations" on health_api_cache
  for all using (true) with check (true);
```

## 3. Tested Table
```js
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = "https://your-project.supabase.co";
const SUPABASE_ANON_KEY = "your-anon-key";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const DEFAULT_TTL_HOURS = 1;

async function getCache(endpoint, params) {
  const { data, error } = await supabase
    .from("health_api_cache")
    .select("response_body")
    .eq("endpoint", endpoint)
    .eq("params", JSON.stringify(params))
    .gt("expires_at", new Date().toISOString())
    .limit(1)
    .single();

  if (error || !data) return null;
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

export { getCache, setCache, purgeExpiredCache, fetchWithCache };
```