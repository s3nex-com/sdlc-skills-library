# Cache patterns

Pick one deliberately. Defaulting to cache-aside is fine; copying whichever pattern your neighbour used is not.

---

## 1. Cache-aside (lazy loading)

The default. The application owns the cache; the cache library is dumb. On read: check cache, on miss load from source, populate cache, return. On write: write to source, then invalidate (or update) the cache.

**When to use:** general-purpose read-heavy workloads. This is the right answer ~80% of the time.

**Pros:**
- Cache failure is survivable — fall back to source.
- Only requested data is cached; no wasted memory on cold data.
- Simple, explicit, easy to reason about.

**Cons:**
- First read is always a miss (cold start penalty).
- Race condition on concurrent miss without a lock (see stampede prevention).
- Invalidation logic lives in app code.

```python
def get(key):
    value = cache.get(key)
    if value is not None:
        return value
    value = source.load(key)
    if value is not None:
        cache.set(key, value, ttl=300)
    return value

def update(key, new_value):
    source.write(key, new_value)
    cache.delete(key)  # next read repopulates
```

Note: `cache.delete` after write is usually safer than `cache.set(new_value)` — the write may race with a concurrent read that refilled the cache with the old value.

---

## 2. Read-through

Cache library sits in front of the source; a miss transparently loads from source. App only talks to the cache.

**When to use:** when you want to centralise loading logic (e.g. a shared caching library across many services accessing the same data model). Common in Hibernate L2 cache, Guava LoadingCache.

**Pros:**
- App code is cleaner — just `cache.get(key)`.
- Loading logic encapsulated.

**Cons:**
- Cache library must know how to load — tight coupling.
- Cache outage requires the library to fall through to source cleanly.
- Less flexible than cache-aside for bespoke loading logic.

```python
# Guava-style LoadingCache (Java)
LoadingCache<String, User> cache = Caffeine.newBuilder()
    .expireAfterWrite(Duration.ofMinutes(5))
    .maximumSize(10_000)
    .build(userId -> userRepository.findById(userId));

User u = cache.get("42");  // transparently loads on miss
```

---

## 3. Write-through

Every write goes to the cache AND the source synchronously. Reads hit cache.

**When to use:** when you need strong read-after-write consistency and the write latency cost is acceptable.

**Pros:**
- Cache is always consistent with source (no stale cache after write).
- Reads never miss for recently-written keys.

**Cons:**
- Writes are slower (two hops instead of one).
- If the cache is down, writes fail (unless you degrade to write-only-source).
- Still need TTL / eviction for data that's never re-read.

```python
def update(key, new_value):
    source.write(key, new_value)        # must succeed first
    cache.set(key, new_value, ttl=300)  # then cache

def get(key):
    return cache.get(key) or source.load(key)
```

---

## 4. Write-behind (write-back)

Write goes to the cache; cache flushes to source asynchronously in batches.

**When to use:** very write-heavy workloads where write throughput to the source is the bottleneck and some data loss is acceptable (e.g. metrics, counters, analytics events).

**Pros:**
- Extremely fast writes.
- Coalesces repeated writes to the same key (counter increments).
- Batches reduce source load.

**Cons:**
- Data loss window if the cache crashes before flush.
- Ordering and consistency are hard.
- Operational complexity (queue, retry, dead-letter).

Only use write-behind when the domain tolerates the loss. Never for financial, auth, or inventory state.

```python
# Pseudocode — real impls use a durable queue
def update(key, new_value):
    cache.set(key, new_value)
    write_buffer.enqueue((key, new_value))

# Background worker
def flush_worker():
    while True:
        batch = write_buffer.drain(max_size=100, max_wait_ms=500)
        if batch:
            source.bulk_write(batch)
```

---

## 5. Refresh-ahead

Predictively refresh a cached value shortly before its TTL expires, so consumers never see a miss on the hot path.

**When to use:** a small number of very-hot keys where even a single miss is unacceptable latency (e.g. homepage feed, top-10 products). Do NOT apply library-wide — it wastes compute refreshing cold keys.

**Pros:**
- Zero miss latency on hot keys.
- Smooths source load.

**Cons:**
- Wasted refreshes for keys no one reads anymore.
- More complex — needs a scheduler or probabilistic trigger.
- Can mask real invalidation bugs (data looks fresh because it's constantly re-fetched, even if wrong).

Typically implemented via **probabilistic early expiration (XFetch)** rather than a separate scheduler:

```python
import math, random, time

def get_with_xfetch(key, loader, ttl=300, beta=1.0):
    entry = cache.get_with_metadata(key)  # value, expiry, last_compute_duration
    if entry is None:
        value = loader()
        cache.set_with_metadata(key, value, ttl=ttl)
        return value

    now = time.time()
    # Probability rises as we approach expiry
    # beta > 1 refreshes earlier; beta < 1 refreshes later
    threshold = now - (entry.compute_duration * beta * math.log(random.random()))
    if threshold >= entry.expiry:
        # Proactive refresh
        value = loader()
        cache.set_with_metadata(key, value, ttl=ttl)
        return value
    return entry.value
```

This eliminates stampedes AND eliminates cold-miss latency for hot keys, without maintaining a separate refresh schedule.

---

## Cache stampede — the problem and the fixes

**The problem:** a hot key expires. 1000 concurrent requests all miss simultaneously. All 1000 hit the DB. DB falls over. When it recovers, the cache populates, and everything looks fine — until the next expiry.

### Fix 1: Distributed lock on miss

First miss acquires a lock; others wait briefly or serve stale.

```python
def get_locked(key, loader, ttl=300, lock_ttl=10):
    value = cache.get(key)
    if value is not None:
        return value
    lock_key = f"{key}:lock"
    if cache.set(lock_key, "1", nx=True, ex=lock_ttl):
        try:
            value = loader()
            cache.set(key, value, ex=ttl)
            return value
        finally:
            cache.delete(lock_key)
    else:
        time.sleep(0.05)
        return cache.get(key) or loader()  # bounded fallback
```

### Fix 2: Jittered TTLs

Add ±10% randomness to every TTL. Prevents keys from all expiring in the same millisecond.

```python
ttl_with_jitter = int(base_ttl * random.uniform(0.9, 1.1))
```

Cheap, effective, always use it.

### Fix 3: Probabilistic early expiration

See XFetch above. A small, rising probability of refreshing before the TTL runs out.

**For a single very-hot key, use all three together.** Jitter to stagger, XFetch to prevent the cliff, lock as a last-resort safety net.

---

## Pattern selection cheat-sheet

| Workload | Pattern |
|----------|---------|
| Generic read-heavy | cache-aside |
| Read-heavy with complex loader | read-through |
| Read-after-write must be fresh | write-through |
| Write-heavy, tolerates loss (counters, metrics) | write-behind |
| Very-hot key, miss is unacceptable | refresh-ahead / XFetch |
