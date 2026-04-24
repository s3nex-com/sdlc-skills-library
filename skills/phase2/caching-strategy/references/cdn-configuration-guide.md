# CDN configuration guide

Covers Cloudflare, Fastly, CloudFront. Concepts translate; syntax differs.

## Core concepts

### Edge TTL vs browser TTL

Two different TTLs. Do not conflate.

- **Edge TTL** — how long the CDN holds the object. Set via `s-maxage` or CDN-specific headers / rules.
- **Browser TTL** — how long the user's browser holds the object. Set via `max-age` in `Cache-Control`.

Typical pattern: short browser TTL, long edge TTL.

```
Cache-Control: public, max-age=60, s-maxage=3600, stale-while-revalidate=300
```

Meaning: browsers cache for 60s; edge caches for 3600s; browsers may serve stale for 300s while revalidating.

Why short browser + long edge? You can purge the CDN in seconds when something is wrong; you cannot purge users' browsers. Keep the browser copy short so users pick up updates quickly; let the edge do the offload.

### Cache key design

The CDN groups requests into cache entries by cache key. Wrong cache key = two URLs that should share a cached response go to origin twice, OR one URL that should have two responses serves the wrong one.

**Include in the key:**
- Host and path (always).
- Query params that affect the response (`?page=2`, `?sort=price`).
- Relevant headers via `Vary` (e.g. `Accept-Encoding` for gzip/brotli variants).
- For API: `Accept-Language`, `Accept` (content negotiation).

**Exclude from the key:**
- Tracking params: `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `fbclid`, `gclid`, `msclkid`, `mc_cid`, `mc_eid`.
- Session / auth cookies — unless you are intentionally keying on the user, which means you probably shouldn't be on a shared CDN at all.

### Vary headers

`Vary` tells caches that the response differs based on the named request headers. Use sparingly — each distinct combination creates a separate cache entry.

- `Vary: Accept-Encoding` — safe; a few variants (gzip, br, identity).
- `Vary: Accept-Language` — reasonable if you localise.
- `Vary: Cookie` — cache-buster. Every unique cookie string → separate cache entry. Avoid.
- `Vary: User-Agent` — cache-exploder. Thousands of UA strings. Almost always wrong.

### stale-while-revalidate and stale-if-error

Two directives that turn the CDN from a strict cache into a resilient one.

- `stale-while-revalidate=N` — serve stale for up to N seconds past expiry while fetching fresh in background. User never waits for a miss; edge does the work async.
- `stale-if-error=N` — serve stale for up to N seconds if the origin returns 5xx or is unreachable. Hides origin outages from users.

Use both liberally for public read-heavy content. A good default:

```
Cache-Control: public, max-age=60, s-maxage=3600, stale-while-revalidate=300, stale-if-error=86400
```

---

## Cloudflare

### Cache Rules (modern approach, replaces Page Rules)

Define in dashboard or via Terraform. Example JSON for an API path:

```json
{
  "expression": "(http.host eq \"api.example.com\" and starts_with(http.request.uri.path, \"/v1/products/\"))",
  "action": "set_cache_settings",
  "action_parameters": {
    "cache": true,
    "edge_ttl": {"mode": "override_origin", "default": 3600},
    "browser_ttl": {"mode": "override_origin", "default": 300},
    "cache_key": {
      "custom_key": {
        "query_string": {"include": ["page", "sort", "limit", "category"]},
        "header": {"include": ["accept-encoding", "accept-language"]}
      }
    }
  }
}
```

### Purge

```bash
# By URL
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://example.com/products/123"]}'

# By tag (Enterprise only)
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_TOKEN" \
  --data '{"tags":["product-123"]}'

# Purge everything — use sparingly, stampedes origin
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_TOKEN" \
  --data '{"purge_everything":true}'
```

### Cache-Tag header (Enterprise)

Origin sets tags; purge hits all URLs carrying a tag.

```
# Origin response header
Cache-Tag: product-123,category-shoes,featured
```

---

## Fastly (VCL)

Fastly gives you full VCL — arbitrary logic in cache key and TTL.

```vcl
sub vcl_recv {
  # Strip tracking params from the cache key
  set req.url = querystring.regfilter(req.url,
    "^(utm_(source|medium|campaign|term|content)|fbclid|gclid)$");
}

sub vcl_fetch {
  if (req.url.path ~ "^/v1/products/") {
    set beresp.ttl = 1h;
    set beresp.grace = 24h;  # stale-if-error window
    set beresp.stale_while_revalidate = 5m;
  }
  if (beresp.status >= 500) {
    set beresp.ttl = 0s;
    set beresp.uncacheable = true;
  }
}
```

### Fastly surrogate keys (tag-based purge, all tiers)

```
# Origin response header
Surrogate-Key: product-123 category-shoes
```

Purge:
```bash
curl -X POST -H "Fastly-Key: $FASTLY_KEY" \
  https://api.fastly.com/service/$SERVICE_ID/purge/product-123
```

Fastly purges complete globally in sub-200ms. Use surrogate keys aggressively.

---

## CloudFront

Cache key and origin request policies are separate configurable objects.

### Cache policy (what's in the cache key)

```hcl
resource "aws_cloudfront_cache_policy" "product_api" {
  name        = "product-api-cache"
  default_ttl = 3600
  max_ttl     = 86400

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config { cookie_behavior = "none" }
    headers_config {
      header_behavior = "whitelist"
      headers { items = ["Accept-Encoding", "Accept-Language"] }
    }
    query_strings_config {
      query_string_behavior = "whitelist"
      query_strings { items = ["page", "sort", "limit", "category"] }
    }
    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}
```

### Invalidations (purge)

```bash
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/v1/products/123" "/v1/products/123/*"
```

CloudFront invalidations are slower than Fastly/Cloudflare (typically 1-5 min) and the first 1,000 paths/month are free; beyond that, $0.005/path. Design for versioned URLs (`/assets/app.abc123.js`) rather than invalidations where possible.

---

## Static asset strategy

For JS/CSS/images, the right pattern is **immutable URLs with fingerprinted filenames**:

```
app.abc123.js    → Cache-Control: public, max-age=31536000, immutable
styles.def456.css → Cache-Control: public, max-age=31536000, immutable
```

When content changes, filename changes, new URL, cache bypassed naturally. Never purge. Never version by query string (`app.js?v=2` — some caches key on query, some don't; filename fingerprinting is universal).

The HTML referencing these assets should be short-TTL or no-cache, since it embeds the new filenames on deploy:

```
index.html → Cache-Control: public, max-age=60, stale-while-revalidate=300
```

---

## Security: never cache user-specific data in a shared CDN

```
# BAD — sets user-specific response without scoping the cache key
GET /api/me
Cache-Control: public, max-age=300

# Risk: edge caches the first user's response; serves it to everyone.
```

Two safe patterns:

1. **Private cache only:** `Cache-Control: private, max-age=300` — browser caches, CDN does not.
2. **User-scoped key:** include auth/user id in the cache key AND set appropriate headers. Complex; usually overkill. Default to `private`.

Checklist for any endpoint returning user data:
- [ ] Is the response user-specific? If yes, `Cache-Control: private` OR no caching.
- [ ] Is an auth cookie or header required? If yes, the default response is private.
- [ ] Does the CDN ignore `Cache-Control: private`? (CloudFront and Cloudflare respect it; verify your config.)

---

## Quick defaults

| Content type | Cache-Control |
|--------------|---------------|
| Fingerprinted static asset | `public, max-age=31536000, immutable` |
| HTML page | `public, max-age=60, stale-while-revalidate=300` |
| Public API (GET, not user-specific) | `public, max-age=60, s-maxage=3600, stale-while-revalidate=300, stale-if-error=86400` |
| User-specific API response | `private, max-age=0, must-revalidate` |
| Authenticated, never cache | `no-store` |
| Error responses (4xx) | `no-store` or very short TTL (10-60s) |
| Error responses (5xx) | `no-store` |
