# Rate limiting and abuse prevention for web products

## What to rate limit and at what thresholds

| Endpoint type | Scope | Recommended limit | Burst |
|--------------|-------|------------------|-------|
| Auth: login / signup | Per IP | 5 req / min | 10 total per 15 min |
| Auth: password reset | Per IP | 3 req / 15 min | — |
| Auth: token refresh | Per user | 10 req / min | — |
| Standard API (GET) | Per user | 100 req / min | 200 per 5 min |
| Standard API (write) | Per user | 30 req / min | 60 per 5 min |
| Expensive operations (export, bulk, report) | Per workspace | 10 req / hour | — |
| Webhooks and integrations | Per API key | 1000 req / min | — |
| Public endpoints (no auth) | Per IP | 20 req / min | — |

Adjust based on your product's real usage patterns. Measure before enforcing.

---

## Algorithms

### Sliding window (recommended for most cases)

Most accurate, smooth enforcement, no burst at window edges.

```typescript
// Redis-based sliding window
async function isRateLimited(key: string, limit: number, windowSeconds: number): Promise<boolean> {
  const now = Date.now();
  const windowStart = now - windowSeconds * 1000;

  const pipeline = redis.pipeline();
  pipeline.zremrangebyscore(key, 0, windowStart);  // remove old entries
  pipeline.zadd(key, { score: now, member: now.toString() });  // add current
  pipeline.zcard(key);  // count in window
  pipeline.expire(key, windowSeconds);

  const results = await pipeline.exec();
  const count = results[2][1] as number;

  return count > limit;
}

// Usage
const key = `ratelimit:login:${ip}`;
if (await isRateLimited(key, 5, 60)) {
  return res.status(429).json({ error: { code: 'RATE_LIMITED', message: 'Too many attempts' } });
}
```

### Token bucket (allows bursts, easier to reason about)

Maintains a "bucket" of tokens. Each request consumes one token. Tokens refill at a steady rate. Allows short bursts.

```typescript
async function consumeToken(userId: string, capacity: number, refillPerSecond: number): Promise<boolean> {
  const key = `ratelimit:tokens:${userId}`;
  const now = Date.now() / 1000;

  const data = await redis.hgetall(key);
  const lastRefill = parseFloat(data?.lastRefill ?? now.toString());
  const tokens = parseFloat(data?.tokens ?? capacity.toString());

  // Refill
  const elapsed = now - lastRefill;
  const refilled = Math.min(capacity, tokens + elapsed * refillPerSecond);

  if (refilled < 1) return false;  // rate limited

  await redis.hset(key, {
    tokens: refilled - 1,
    lastRefill: now.toString(),
  });
  await redis.expire(key, Math.ceil(capacity / refillPerSecond) + 1);

  return true;
}
```

---

## Response headers

Always return rate limit information in headers so clients can back off gracefully:

```typescript
res.setHeader('X-RateLimit-Limit', limit);
res.setHeader('X-RateLimit-Remaining', Math.max(0, limit - count));
res.setHeader('X-RateLimit-Reset', Math.ceil(windowResetAt / 1000));  // Unix timestamp

// On 429
res.setHeader('Retry-After', retryAfterSeconds);
return res.status(429).json({ error: { code: 'RATE_LIMITED', ... } });
```

---

## Middleware integration

```typescript
// Express / Fastify middleware
function rateLimiter(options: RateLimitOptions) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const key = options.keyFn(req);  // e.g., req.user?.id ?? req.ip

    const { limited, remaining, reset } = await checkRateLimit(key, options);

    res.setHeader('X-RateLimit-Limit', options.limit);
    res.setHeader('X-RateLimit-Remaining', remaining);
    res.setHeader('X-RateLimit-Reset', reset);

    if (limited) {
      res.setHeader('Retry-After', Math.ceil((reset * 1000 - Date.now()) / 1000));
      return res.status(429).json({ error: { code: 'RATE_LIMITED', message: 'Rate limit exceeded' } });
    }

    next();
  };
}

// Apply per route category
app.use('/auth', rateLimiter({ keyFn: (req) => req.ip, limit: 5, windowSeconds: 60 }));
app.use('/api', rateLimiter({ keyFn: (req) => req.user?.id, limit: 100, windowSeconds: 60 }));
```

---

## Auth endpoint hardening (credential stuffing)

Credential stuffing is a web product's most common auth threat: an attacker tests a list of leaked passwords against your login endpoint.

**Detectable signals:**
- Many failed logins for different email addresses from the same IP
- Many failed logins for the same email address from different IPs
- Login attempts with identical passwords across many accounts
- Requests with no browser fingerprint characteristics (no Accept-Language, no User-Agent variation)

**Mitigations:**

1. **Per-IP rate limit on auth** — most effective, lowest friction
2. **Account lockout after N failed attempts** — lock the account, not the IP. Send unlock email. Prevents brute-force on a specific account.
3. **Device fingerprinting** — flag logins from new devices; require email verification
4. **CAPTCHA on repeated failures** — show CAPTCHA after 3 failed attempts, not on the first attempt (friction kills conversion)

```typescript
async function handleLogin(email: string, password: string, ip: string) {
  // 1. Check account lockout
  const failedAttempts = await redis.incr(`login:failed:${email}`);
  if (failedAttempts > 10) {
    await lockAccount(email);
    throw new AccountLockedError();
  }
  await redis.expire(`login:failed:${email}`, 900); // 15 min window

  // 2. Verify credentials
  const user = await db.user.findUnique({ where: { email } });
  const valid = user && await verifyPassword(password, user.passwordHash);

  if (!valid) {
    // Track failed attempt (already incremented above)
    await logSecurityEvent('login.failed', { email, ip });
    throw new InvalidCredentialsError(); // same message as "user not found" — no enumeration
  }

  // 3. Success — reset failure counter
  await redis.del(`login:failed:${email}`);
  await logSecurityEvent('login.success', { userId: user.id, ip });

  return user;
}
```

---

## Bot prevention

| Signal | When to apply |
|--------|--------------|
| **Honeypot field** | All public forms (signup, contact). Hidden field — real users never fill it; bots do. |
| **CAPTCHA** (hCaptcha, Cloudflare Turnstile) | After 3+ failed auth attempts; account creation from suspicious IPs; high-value actions |
| **Browser fingerprinting** | Detect headless browsers; flag suspicious user agents |
| **Email verification** | Require on signup — stops bulk fake account creation |

```html
<!-- Honeypot field — hidden from real users, filled by bots -->
<form>
  <input type="text" name="email" />
  <input type="text" name="website" style="display:none" tabindex="-1" autocomplete="off" />
  <!-- If "website" is non-empty on submit, discard silently -->
</form>
```

---

## IP allowlists and trusted clients

Some clients (webhooks from partners, monitoring services, your own CI) should bypass rate limits:

```typescript
const TRUSTED_IPS = new Set(process.env.TRUSTED_IPS?.split(',') ?? []);

function rateLimiter(options: RateLimitOptions) {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (TRUSTED_IPS.has(req.ip)) return next();  // bypass
    // ... normal rate limit check
  };
}
```

Store trusted IPs in environment config, not in code. Rotate them when the partner relationship ends.

---

## Observability for rate limiting

Track these metrics to tune limits over time:

- `ratelimit.checked_total` — labelled by endpoint category
- `ratelimit.limited_total` — how often limits are hit (high rate = limit too low or attack)
- `ratelimit.limited_by_ip` — high from a single IP = attack signal
- `ratelimit.limited_by_user` — high for a specific user = legitimate heavy user or scripted abuse

Alert on: `ratelimit.limited_total` spiking by > 5× the hourly baseline (potential attack).
