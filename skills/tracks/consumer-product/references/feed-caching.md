# Feed and recommendation caching

## The core problem

A personalised feed involves expensive computation: ranking, deduplication, personalisation scoring, collaborative filtering. Running this per-request at scale is cost-prohibitive and latency-bloating. Caching is the standard solution — and the source of two common correctness failures:

1. **Cache poisoning of A/B assignment**: a cached feed response is served to a user in the treatment group that was computed for control, or vice versa.
2. **Cross-user data leak**: a feed computed for user A is served to user B because the cache key was insufficiently scoped.

Preventing these failures is why this reference exists.

---

## Cache key design

Every cache key for feed or recommendation data must include:

- `user_id` — never a shared key across users
- `experiment_assignment` — the variant the user is in for any active experiment touching the feed
- `algorithm_version` — if the ranking model or algorithm version matters for correctness
- `page_cursor` — for paginated feeds

**Bad key:** `feed:trending:v3`
**Good key:** `feed:${user_id}:${experiment_assignment}:${cursor}`

---

## Cache invalidation strategies

| Strategy | When to use | Notes |
|----------|------------|-------|
| TTL expiry | Slowly changing feeds (news, recommendations) | 5–15 min TTL typical; avoid for social feeds with real-time events |
| Event-driven invalidation | Social feeds (follow, like, new post) | Write event triggers cache eviction for affected user feeds |
| Lazy recompute | On miss, recompute synchronously | Only viable if recompute is fast (< 200ms); otherwise prefetch |
| Background prefetch | High-traffic feeds | Compute on schedule; cache pre-warmed before users arrive |

---

## Write-time fanout vs read-time compute

Personalised feeds at scale use pre-computation (write-time fanout):

```
User posts content → fanout service → writes to each follower's cached feed
```

Tradeoffs:
- High-follower accounts generate O(follower_count) writes per post
- Read-heavy products prefer write-time fanout for low-latency reads
- Hybrid: pre-compute for users with < 10k followers; compute-on-read for influencers

---

## A/B experiment integrity

Any experiment that modifies feed ranking, item selection, or content ordering MUST be reflected in the cache key. Failure modes:

1. User A (treatment) triggers cache miss → recompute with treatment algorithm → write to cache with key `feed:recent`
2. User B (control) triggers cache hit → served treatment content

The fix: include experiment assignment in the cache key. This multiplies storage but is non-negotiable for valid experiments.

During an experiment, do not serve cache entries generated before the experiment started. Include a `cache_after: {experiment_start_time}` check on read, or bust the cache at experiment launch for the affected segments.

---

## CDN and edge caching

Static content (images, thumbnails, assets embedded in feed items): aggressive CDN caching is safe.

Personalised content (ranked feed positions, recommendation tiles, engagement-dependent content): CDN caching is almost always wrong. Never cache personalised responses at the CDN layer unless Vary headers are keyed on user identity.

Edge-caching personalised content without proper Vary headers is the industry's most common source of cross-user data leaks in consumer products.

---

## Performance targets

| Metric | Target | Measurement point |
|--------|--------|-----------------|
| Feed API p50 | < 100ms | Server-side, excluding network |
| Feed API p95 | < 300ms | Server-side |
| Time to first item | < 500ms | Client-measured, includes network |
| Feed cache hit rate | > 80% | Cache layer metric |

A hit rate below 80% usually means TTL is too short or cache key cardinality is too high. Tune TTL and key granularity together — they are in tension.

---

## State store caching (streaming feeds)

For feeds built on top of a streaming processor (Kafka Streams, Flink), state stores (RocksDB-backed) are the caching layer. Design for:

- State store size: estimate per-user state size × active users; overshoot fails the broker
- Restore time: on consumer restart, state must restore within the lag SLO
- Cache-aside vs in-stream: for aggregations that do not need to be in the stream topology, a Redis cache-aside is simpler and avoids state-store complexity

---

## Common failures

- Per-type cache keys (`feed:trending`) with no user scoping → cross-user data served
- TTL of 1 hour on a feed where content changes every 5 minutes → user experience is stale, users see old content and report bugs
- No stampede prevention → cache expiry triggers simultaneous recomputes from 10k users, floods DB
- Cache pre-warming skipped → cold start after deploy saturates the database for 60 seconds
