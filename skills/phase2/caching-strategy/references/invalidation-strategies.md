# Invalidation strategies

"There are only two hard things in computer science: cache invalidation and naming things." Invalidation is hard because the source of truth changed somewhere, and you need every cache that holds a copy to find out — ideally before a consumer reads the stale copy. Pick the simplest strategy that satisfies your staleness tolerance.

---

## 1. TTL-based invalidation

The default. Every cached value has a time-to-live. When the TTL elapses, the next read misses and repopulates.

**Pros:**
- Trivial to implement — every cache supports it.
- No coupling between writer and cache.
- Self-healing: stale data automatically expires.

**Cons:**
- Staleness window equals the TTL. A 1-hour TTL means consumers may see 1-hour-old data.
- Coarse: a value written 1 second before expiry lives 1 second; same value written 1 second after expiry lives ~TTL.
- Does not react to known-bad data.

**Use when:**
- Data changes on a predictable cadence.
- A bounded staleness window is acceptable.
- You want the simplest thing that works.

**TTL selection (practical):**

| Data type | TTL |
|-----------|-----|
| Public, rarely changes (country list, blog post) | 1h – 24h |
| Public, semi-frequent (product catalog) | 5m – 1h |
| User profile, preferences | 5m – 15m |
| Feed counts, notifications | 10s – 60s |
| Session / auth state | seconds or don't cache |
| Auth decisions, inventory, payments | don't cache, or sub-second |

Always jitter: `ttl * uniform(0.9, 1.1)`.

---

## 2. Event-driven invalidation

On every write to the source of truth, emit an event. A subscriber deletes (or updates) the affected cache keys.

**Pros:**
- Near-zero staleness window (as fast as your event bus).
- Works across distributed caches — all listeners receive the event.
- Can invalidate many derived caches from one write (e.g. a user update invalidates `user:42:profile`, `user:42:permissions`, and the user's feed cache).

**Cons:**
- Writer and cache are now coupled via the event bus.
- Missed events = permanent staleness until TTL rescue. Always pair with a TTL backstop.
- Order matters: if invalidate arrives before write commits, the cache can repopulate with old data.

**Correct sequence:**
1. Write to source. Commit.
2. Emit event after commit (transactional outbox pattern avoids lost events).
3. Subscriber deletes cache key.
4. Next read misses and repopulates with fresh data.

**Bad sequence (race):**
1. Emit event.
2. Cache deleted.
3. Concurrent reader misses, loads OLD value from source, populates cache.
4. Write commits. Cache now holds pre-write value indefinitely.

```python
# Using a transactional outbox — event is committed atomically with the write
def update_user(user_id, new_data):
    with db.transaction():
        db.update("users", user_id, new_data)
        db.insert("outbox", {
            "topic": "user.updated",
            "payload": {"user_id": user_id},
        })
    # Separate worker publishes from outbox to event bus

# Cache invalidation subscriber
def on_user_updated(event):
    user_id = event.payload["user_id"]
    redis.delete(f"user:{user_id}:profile:v2")
    redis.delete(f"user:{user_id}:permissions:v2")
```

Always combine with a TTL. If an invalidation event is ever lost, the TTL eventually rescues the cache.

---

## 3. Version keys

Include a version number in the cache key. To invalidate, bump the version. Old keys age out via TTL.

**Pros:**
- "Invalidation" is just a write of a new version number — atomic, no cache delete needed.
- Works trivially across distributed caches.
- Old keys don't have to be found or deleted.

**Cons:**
- Memory waste: old versions linger until TTL.
- Requires a version source (DB column, Redis counter) that every reader consults.

**Two flavours:**

### 3a. Per-entity version

```python
def get_user_profile(user_id):
    version = db.query_scalar(
        "SELECT cache_version FROM users WHERE id = %s", (user_id,)
    )
    key = f"user:{user_id}:profile:v{version}"
    cached = redis.get(key)
    if cached:
        return json.loads(cached)
    profile = db.query_one("SELECT ... FROM users WHERE id = %s", (user_id,))
    redis.setex(key, 3600, json.dumps(profile))
    return profile

def update_user_profile(user_id, new_data):
    db.execute(
        "UPDATE users SET ..., cache_version = cache_version + 1 WHERE id = %s",
        (user_id,),
    )
    # No cache delete — next read generates a new key and the old one ages out
```

Cost: one extra DB read per cache lookup. Usually the version read is cheap or can itself be cached short.

### 3b. Global / schema version

Bump a single version counter to invalidate EVERYTHING. Useful for "we just deployed a breaking schema change to the cached format."

```python
SCHEMA_VERSION = "v3"  # bump on deploy if format changed

def user_key(user_id):
    return f"user:{user_id}:profile:{SCHEMA_VERSION}"
```

---

## 4. Tag-based purging

Cached entries carry tags (e.g. `product:123`, `category:shoes`). Purging a tag evicts every entry carrying it. Supported natively by Fastly, Cloudflare Enterprise, and Varnish; emulate in Redis with secondary sets.

**Pros:**
- One operation purges many related entries (a product update purges every page, API response, and listing that references it).
- Great for CDN content with complex fan-out.

**Cons:**
- Not all CDNs support it (Cloudflare free tier does not — paid tier does).
- Emulating in Redis requires maintaining tag-to-key secondary indexes.

**Fastly example:**

```
# Origin sets Surrogate-Key header on the response
Surrogate-Key: product-123 category-shoes

# Purge by tag via API
curl -X POST -H "Fastly-Key: ..." \
  https://api.fastly.com/service/SERVICE_ID/purge/product-123
```

**Cloudflare (Enterprise Cache Tags):**

```
# Origin sets Cache-Tag header
Cache-Tag: product-123,category-shoes

# Purge by tag via API
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tags":["product-123"]}'
```

**Redis emulation:**

```python
def set_with_tags(key, value, tags, ttl=300):
    pipe = redis.pipeline()
    pipe.setex(key, ttl, value)
    for tag in tags:
        pipe.sadd(f"tag:{tag}", key)
        pipe.expire(f"tag:{tag}", ttl * 2)
    pipe.execute()

def purge_tag(tag):
    members = redis.smembers(f"tag:{tag}")
    if members:
        redis.delete(*members)
    redis.delete(f"tag:{tag}")
```

---

## Distributed cache coherency

Multiple cache nodes holding the same data. How do you keep them in sync?

**Options in order of preference:**

1. **Don't.** Use a single shared cache (Redis cluster) instead of per-node caches. Coherency problem disappears.
2. **Short TTLs on per-node caches.** Accept bounded staleness; no coordination needed. Works well for reference data.
3. **Event-driven invalidation to every node.** Pub/sub broadcasts invalidations; each node deletes its local copy. Tight consistency, ops cost of a pub/sub channel.
4. **Version keys across shared source.** All nodes read the same version counter; they each cache locally under that version. Bumping the counter invalidates everyone.

Avoid: node-to-node direct invalidation calls. N² complexity, fragile.

---

## Anti-patterns

- **Infinite TTL with no event-driven invalidation.** Data becomes stale indefinitely. Every cache should have a TTL, even if event-driven invalidation is the primary mechanism — TTL is the backstop for lost events.
- **Invalidate before commit.** Event emits, cache deletes, concurrent reader reloads OLD data, write commits. Cache now permanently stale. Always commit first, emit second (use transactional outbox).
- **Caching write responses without invalidation.** Write succeeds, response cached, the next read of the mutated resource serves the pre-write response. Don't cache write responses.
- **Caching 5xx errors.** A transient outage becomes a permanent failure for the TTL duration. Only cache successful responses (with rare exceptions like short-TTL 404s).
- **Negative caching without bound.** Caching "not found" is fine for short TTLs (10-60s) but can permanently mask the arrival of new data if unbounded.
- **Global flush as the only invalidation.** "We just flush everything on deploy." Fine occasionally, not as a primary strategy — it stampedes the source.
