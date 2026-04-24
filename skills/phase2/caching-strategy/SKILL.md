---
name: caching-strategy
description: >
  Activate when adding caching to a service, debugging cache-related bugs, configuring a
  CDN (Cloudflare, Fastly, CloudFront), designing cache invalidation, investigating low
  cache hit rate, diagnosing a cache stampede, picking TTLs, introducing Redis or Memcached,
  designing edge caching for static assets or API responses, choosing between cache-aside,
  read-through, write-through, write-behind, or refresh-ahead patterns, reviewing cache
  coherency in a distributed system, or deciding whether caching is the right answer at
  all. Trigger phrases: "add caching", "cache invalidation", "CDN configuration", "cache
  hit rate", "cache stampede", "cache strategy", "Redis caching", "Cloudflare config".
---

# Caching strategy

## Purpose

"There are only two hard things in computer science: cache invalidation and naming things." — Phil Karlton. The joke lands because it is true. A cache is a promise that stale data is acceptable for some bounded window. Every cache decision is really an invalidation decision in disguise: when do we decide the cached value is wrong, and how do we replace it without breaking consumers? This skill gives you the decision framework for picking a cache layer, a pattern, and an invalidation strategy that actually matches the data's volatility, tolerance for staleness, and blast radius of a wrong answer.

---

## When to use

- Designing caching for a new service or endpoint.
- A profile shows repeated identical DB queries or API calls dominating latency.
- Static assets (JS, CSS, images) are being served from origin instead of the edge.
- Introducing a CDN or tuning its cache behaviour.
- A specific read path must drop below a latency budget that the DB cannot meet.
- Debugging stale data, thundering-herd, or memory-growth problems in an existing cache.
- Picking TTLs, cache keys, or eviction policies for Redis / Memcached / in-process caches.

---

## When NOT to use

- Defining latency NFRs, load testing, capacity planning, circuit breakers, or sizing auto-scaling. Caching is one lever, not the whole system — use `performance-reliability-engineering`.
- Changing schemas, adding indexes, migrating tables, rewriting queries at the DB level — use `database-migration`.
- Designing API contracts, versioning, request/response schemas. Cache key design is a derived concern, not the contract itself — use `api-contract-enforcer`.
- Instrumenting metrics, wiring dashboards and alerts for cache hit rate, error budgets, SLOs. Once you have decided what to measure here, ship it through — `observability-sre-practice`.
- Feature-flagging a rollout of a new cache layer — use `feature-flag-lifecycle`.

---

## Process or checklist

Work this in order. Do not skip step 1.

### 1. Decide whether to cache at all

Caching is not free. You buy latency with three costs: staleness risk, invalidation complexity, and a new failure mode (cache down, cache wrong). Skip caching when:

- The data changes on every read (user's shopping cart during checkout).
- The upstream is already fast enough (sub-10ms DB query on an indexed lookup).
- A wrong answer is unsafe (authorisation decisions, payment state, inventory at the moment of purchase).
- The traffic is too low to justify the moving parts (1 RPS does not need Redis).

Sometimes "not caching" is the correct answer. Write it down and move on.

### 2. Pick the layer

Cache at the layer closest to the consumer that is still safe.

| Layer | Use when | Typical TTL |
|-------|----------|-------------|
| Browser (HTTP cache headers) | Static assets, versioned files, per-user profile data | 1 hour – 1 year (with fingerprinting) |
| CDN / edge | Public read-heavy data, static assets, cacheable API GETs | 1 min – 24 hours |
| Reverse proxy (nginx, Varnish) | Per-datacenter cache for origin offload | 1 min – 1 hour |
| Application (Redis, Memcached) | Hot data shared across app instances | 1 min – 1 hour |
| In-process (LRU dict, caffeine) | Per-instance hot data, reference data | 10 sec – 5 min |
| DB query cache | Rarely — MySQL removed it; Postgres has none. Use the app layer instead. | n/a |

Rule of thumb: if the data is public, cache at the edge. If it is user-specific, cache in the application layer with a user-scoped key. Never cache user-specific data in a shared CDN.

### 3. Pick the pattern

See `references/cache-patterns.md` for the full walkthrough. Summary:

- **Cache-aside (lazy loading)** — default choice. App reads cache; on miss, loads from source, populates cache, returns. Cache is a side thing the app manages.
- **Read-through** — cache library owns loading. Cleaner code, tighter coupling.
- **Write-through** — write goes to cache and source synchronously. Strong consistency, slower writes.
- **Write-behind (write-back)** — write goes to cache, flushed to source async. Fast writes, risk of data loss on cache crash.
- **Refresh-ahead** — predictively refresh popular keys before expiry. Use for a few very-hot keys; do not apply library-wide.

Default to cache-aside unless you have a specific reason to pick otherwise.

### 4. Pick the invalidation strategy

See `references/invalidation-strategies.md`. Options, in order of preference for most workloads:

1. **TTL-based** — simplest. Pick a TTL tied to the data's rate of change and the staleness consumers can tolerate. Combine with jitter.
2. **Event-driven invalidation** — source-of-truth emits an event on mutation; cache listens and deletes / updates keys. Tight consistency, more moving parts.
3. **Version keys** — include a version number in the cache key (`user:42:v17`). Bump the version to invalidate — no delete needed. Old keys age out by TTL.
4. **Tag-based purging** — CDN / cache tags group keys; purging a tag evicts all members. Great for CDN content (purge `product:123` across all page variants).
5. **Manual / on-deploy flush** — rare, usually a smell.

Anti-pattern: "no explicit invalidation, just a long TTL, we'll deal with it" — you will not, and your users will see stale data indefinitely.

### 5. Pick TTLs — practical guidance

- Public read-heavy data (product catalog, blog posts): **1 hour – 24 hours**.
- User-specific but slow-changing (profile, preferences): **5 – 15 minutes**.
- Rapidly-changing (feed counts, live scores): **10 – 60 seconds**, or skip the cache.
- Authoritative state (auth tokens, feature flags): very short (< 30 seconds) or event-driven.
- Never: an infinite TTL with no invalidation. Always bound it.

Add **jitter** (± 10%) to every TTL to stagger expiry across keys and prevent herd behaviour.

### 6. Prevent cache stampede

Stampede: a hot key expires, 1000 concurrent requests all miss, all hit the DB simultaneously, DB falls over. See `references/cache-patterns.md` for code. Three mitigations:

- **Distributed lock on miss** — first miss grabs a lock, recomputes, others wait or serve stale.
- **Jittered TTLs** — randomise expiry ± 10% so keys don't expire together.
- **Probabilistic early expiration (XFetch)** — each request has a small, rising probability of refreshing before the TTL hits zero. Smooths the cliff.

For a single very-hot key, use all three.

### 7. Design the cache key

- Deterministic from inputs. Same inputs → same key. Always.
- Namespace by data type (`user:42:profile`, not `42`).
- Include a schema version if the serialised format may change (`user:42:v2`).
- For CDN keys: include only the query params that affect the response. Exclude tracking params (`utm_*`, `fbclid`, `gclid`).
- For user-specific cache: include the user id or session id in the key, never in headers-that-vary alone for shared caches.

### 8. Decide CDN behaviour (if applicable)

See `references/cdn-configuration-guide.md`. Key decisions:

- **Edge TTL** (how long the CDN holds it) vs **browser TTL** (how long the browser holds it). Edge TTL is usually longer.
- **Cache key** — which query params, which headers, which cookies are part of the key.
- **Vary headers** — `Accept-Encoding`, `Accept-Language` often; avoid `Cookie` unless you really mean it (explodes the cache).
- **stale-while-revalidate** — serve stale up to N seconds while fetching fresh in background. Use liberally; it hides origin hiccups.
- **stale-if-error** — serve stale if origin is down. Use liberally.
- **Purge strategy** — tag-based (Fastly, Cloudflare Enterprise) or URL-based.

### 9. Wire observability

Define the metrics you need before you ship. Hand them off to `observability-sre-practice` for dashboards and alerts.

- `cache.hit_rate` — hits / (hits + misses). Below 50% usually means your TTL or key design is wrong.
- `cache.miss_rate` — inverse, but track explicitly for alerting.
- `cache.eviction_rate` — non-zero on memory-bounded caches is normal; spiking evictions mean the working set no longer fits.
- `cache.latency` — P50 / P99 on get and set. If cache latency approaches DB latency, the cache is not earning its keep.
- `cache.stampede_lock_wait` — if you use locks, track time waiting.
- `cdn.origin_hit_rate` — requests that reached your origin. Inverse of CDN offload.

### 10. Anti-patterns to refuse

- **Caching without invalidation.** Any cache without an invalidation plan (even if that plan is "TTL") is a bug waiting.
- **Unbounded cache growth.** Redis with no `maxmemory` + no eviction policy = OOM. Always set `maxmemory` and `maxmemory-policy` (usually `allkeys-lru`).
- **Caching errors.** Do not cache 500s. Usually do not cache 404s either, unless deliberately and with a short TTL.
- **Caching user-specific data on a shared CDN.** Leaks one user's data to another. Use `Cache-Control: private` or a user-scoped edge key.
- **Stale cache never invalidated.** "We'll invalidate later" = never.
- **Cache as a database.** Redis is not your source of truth unless you explicitly designed it to be (with persistence, replication, and backup).
- **Ignoring cache failures.** If Redis is down, your app should degrade to hitting the origin, not 500. Wrap cache calls in try / except.

---

## Output format with real examples

### Cache-aside with TTL + jitter (Python + Redis)

```python
import json
import random
from typing import Optional

CACHE_TTL_SECONDS = 300  # 5 minutes base

def get_user_profile(user_id: str) -> dict:
    key = f"user:{user_id}:profile:v2"

    # 1. Check cache
    cached = redis.get(key)
    if cached is not None:
        return json.loads(cached)

    # 2. Miss — load from source of truth
    profile = db.query_one(
        "SELECT id, name, email, preferences FROM users WHERE id = %s",
        (user_id,),
    )
    if profile is None:
        return None  # do NOT cache the None (avoid poisoning)

    # 3. Populate cache with jittered TTL (±10%) to spread expiry
    ttl = int(CACHE_TTL_SECONDS * random.uniform(0.9, 1.1))
    redis.setex(key, ttl, json.dumps(profile))

    return profile
```

### Cache stampede prevention — distributed lock (Python + Redis)

```python
def get_hot_key_with_lock(key: str, loader, ttl: int = 300) -> dict:
    cached = redis.get(key)
    if cached is not None:
        return json.loads(cached)

    # Miss path — only one caller recomputes
    lock_key = f"{key}:lock"
    got_lock = redis.set(lock_key, "1", nx=True, ex=10)  # 10s lock timeout

    if got_lock:
        try:
            value = loader()
            ttl_with_jitter = int(ttl * random.uniform(0.9, 1.1))
            redis.setex(key, ttl_with_jitter, json.dumps(value))
            return value
        finally:
            redis.delete(lock_key)
    else:
        # Another caller is recomputing; wait briefly and retry or serve stale
        time.sleep(0.05)
        cached = redis.get(key)
        if cached is not None:
            return json.loads(cached)
        # Fall back to loader to avoid unbounded wait
        return loader()
```

### Cloudflare cache config (Page Rule / Cache Rule syntax)

```
# Rule: cache product API responses at edge, exclude tracking params from key
Match: (http.host eq "api.example.com" and starts_with(http.request.uri.path, "/v1/products/"))

Cache settings:
  Cache Level: Cache Everything
  Edge Cache TTL: 1 hour
  Browser Cache TTL: 5 minutes
  Cache Key:
    Include query string:
      - page
      - sort
      - limit
    Exclude query string:
      - utm_source
      - utm_medium
      - utm_campaign
      - fbclid
      - gclid
  Vary on:
    - Accept-Encoding
    - Accept-Language
  Origin Cache Control: respect
  stale-while-revalidate: 60
  stale-if-error: 86400
```

See `references/cdn-configuration-guide.md` for Fastly VCL and CloudFront equivalents.

---

## Skill execution log

Every firing appends one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] caching-strategy | outcome: OK|BLOCKED|PARTIAL | next: <skill> | note: <brief>
```

If `docs/skill-log.md` does not exist, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] caching-strategy | outcome: OK | next: observability-sre-practice | note: cache-aside + Redis added to product API, TTL 1h with jitter, stampede lock on hot keys
[2026-04-20] caching-strategy | outcome: PARTIAL | next: performance-reliability-engineering | note: CDN configured; origin still hot, load test needed to confirm offload
[2026-04-20] caching-strategy | outcome: BLOCKED | next: api-contract-enforcer | note: cannot define cache key — query param contract not frozen
```

---

## Reference files

Heavy material lives under `references/` and loads on demand:

- `references/cache-patterns.md` — cache-aside, read-through, write-through, write-behind, refresh-ahead. Code for each, trade-offs, when to pick.
- `references/invalidation-strategies.md` — TTL, event-driven, version keys, tag-based purging. Distributed coherency notes.
- `references/cdn-configuration-guide.md` — Cloudflare, Fastly, CloudFront config patterns. Cache keys, vary headers, stale-while-revalidate, purge APIs.
