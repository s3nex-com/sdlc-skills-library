# Auth patterns for web products

## JWT vs sessions — decision first

| Signal | Use JWT (stateless) | Use sessions (stateful) |
|--------|--------------------|-----------------------|
| Need to revoke individual tokens instantly | No — requires blocklist, which makes it stateful | Yes — delete session row |
| Horizontally scaled with no shared store | Yes — no shared state needed | No — sessions need shared store (Redis) |
| Mobile + web clients both exist | Yes — easier to pass via header | Less natural |
| You have Redis or equivalent already | Either | Yes — simplest implementation |

**Practical recommendation for most web products:** sessions backed by Redis or your database. JWT's stateless advantage disappears the moment you need logout or token revocation — and you always need logout. Use JWTs for short-lived access tokens (15 min TTL) with a stateful refresh token for rotation; this is the hybrid approach used by Auth0, Clerk, and Supabase Auth.

---

## The hybrid token model (recommended)

```
Access token:  JWT, signed HS256 or RS256, TTL = 15 minutes
Refresh token: opaque random string (UUID v4), stored in DB or Redis, TTL = 7–30 days
```

**Access token** is sent with every API request. Short TTL limits the blast radius of a stolen token.

**Refresh token** is exchanged for a new access token when the access token expires. Stored server-side so it can be revoked.

**Storage:**
- Access token: in-memory (JS variable) or `httpOnly` cookie (preferred)
- Refresh token: `httpOnly`, `Secure`, `SameSite=Strict` cookie — never in `localStorage`

**Why not `localStorage`?** Any XSS on any page in your app can read `localStorage`. `httpOnly` cookies are not readable by JavaScript. An XSS can still forge requests (CSRF), but that's mitigated by `SameSite=Strict` and CSRF tokens.

---

## Refresh token rotation

On every refresh:
1. Client presents the refresh token
2. Server verifies it exists in the store and has not been revoked
3. Server issues new access token + new refresh token
4. Server invalidates the old refresh token
5. Server stores the new refresh token (link to the old one for reuse detection)

**Reuse detection:** if a refresh token is presented after it has already been rotated, assume the old token was stolen. Revoke the entire token family (all refresh tokens for that session). Force re-authentication.

---

## OAuth2 / PKCE for SPAs and public clients

Public clients (SPAs, mobile apps) cannot store a client secret securely. Use PKCE:

1. Client generates `code_verifier` (random 43–128 char string)
2. Client computes `code_challenge = BASE64URL(SHA256(code_verifier))`
3. Client sends `code_challenge` with the authorisation request
4. After redirect, client sends `code_verifier` with the token request
5. Server verifies `SHA256(code_verifier) == code_challenge`

PKCE prevents authorisation code interception attacks. Required for all public OAuth2 clients.

**Social login** (Google, GitHub, etc.) uses OAuth2 authorisation code flow with PKCE. After the OAuth2 callback, create or update the local user record, then issue your own session/JWT pair — do not use the provider's access token as your app's access token.

---

## MFA

**TOTP (Time-based One-Time Passwords):**
- User scans a QR code with an authenticator app (Authy, Google Authenticator, 1Password)
- Server stores the TOTP secret encrypted at rest
- On each login, verify the 6-digit code with a ±1 step window
- Libraries: `speakeasy` (Node.js), `pyotp` (Python), `otpauth` (Go)

**WebAuthn / Passkeys:**
- Hardware key (YubiKey) or platform authenticator (Face ID, Touch ID, Windows Hello)
- Higher security, better UX for supported platforms, immune to phishing
- Libraries: `@simplewebauthn/server`, `py_webauthn`
- Recommended as the upgrade path from TOTP for security-conscious products

**Recovery codes:**
- Generate 8–10 single-use recovery codes at MFA setup time
- Store hashed (bcrypt/Argon2)
- Show to user once — they are responsible for storage

---

## Password hashing

**Use Argon2id.** bcrypt is acceptable if your language ecosystem lacks Argon2 support. SHA-256 and MD5 are not acceptable. Never store plaintext passwords.

Argon2id recommended parameters (2023 baseline, increase as hardware improves):
- `memory = 19456` (19 MiB)
- `iterations = 2`
- `parallelism = 1`
- `hash_length = 32`

---

## Token revocation

Revoke refresh tokens by ID (mark as invalid in DB or delete the Redis key). This is why the refresh token must be stored server-side.

Scenarios requiring revocation:
- User logs out → revoke the specific session's refresh token
- User changes password → revoke all sessions
- User reports device lost/stolen → revoke all sessions or a specific session from the sessions list
- Admin deactivates user → revoke all sessions and reject new token grants

**Revocation check on the access token:** access tokens (JWTs) are not revocable during their TTL unless you add a blocklist. Keep the TTL short (15 min) to limit exposure. For Rigorous mode, maintain a JWT blocklist in Redis keyed by `jti` claim.

---

## Common pitfalls

| Pitfall | Consequence | Fix |
|---------|-------------|-----|
| Refresh token in `localStorage` | XSS reads token → account takeover | `httpOnly` cookie |
| Long-lived access tokens (hours/days) | Stolen token usable until expiry | TTL ≤ 15 min |
| No refresh token rotation | Stolen refresh token valid indefinitely | Rotate on every use |
| JWT `alg: none` accepted | Anyone can forge a valid JWT | Explicitly reject `none`; allowlist algorithms |
| TOTP secret stored plaintext | DB breach → TOTP compromise | Encrypt at rest with KMS/envelope key |
| Missing `SameSite` on session cookie | CSRF attacks | `SameSite=Strict` or `SameSite=Lax` |
| Auth middleware per-handler | One missed handler = open endpoint | Router-level middleware |
| Social login creates duplicate accounts | Same user has two accounts | Merge on verified email match |
