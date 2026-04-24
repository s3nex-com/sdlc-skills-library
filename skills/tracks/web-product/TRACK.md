---
name: web-product
description: >
  Activates when the user mentions a multi-user web application, user accounts,
  user registration, REST API and frontend, full-stack web app, API with React /
  Vue / Next.js / Svelte, subscription billing, Stripe Checkout, pricing tiers,
  user roles, RBAC for a web product, tenant isolation without enterprise SSO,
  authentication flows (JWT, OAuth2, sessions), web product, SaaS product without
  enterprise ceremony. Also triggers on explicit declaration: "web product track"
  or "web app track".
---

# Web product track

## Purpose

This track covers multi-user web products: an API backend, a browser frontend, a shared relational database, and a user-facing identity model with roles and permissions. Unlike the SaaS B2B track (which is scoped to enterprise customers with SSO, SAML, DPAs, and contractual SLAs), this track targets the most common shape of product: multiple users, standard auth, simple RBAC, subscription billing, and a need for real tenant isolation and concurrency discipline — without enterprise ceremony.

The base library handles implementation well but does not encode the web-product class of failure: cross-user data leaks from missing tenant scoping, auth regressions from JWT/session mismanagement, duplicate submissions from absent idempotency keys, broken UI from missing error boundaries, and billing state drift from improperly handled Stripe webhooks. This track makes those concerns explicit, elevates the skills that catch them, and injects domain reference material at the moment each skill fires.

Typical mode pairing: **Lean** for internal-team or early-product work. **Standard** for any product with external users. **Rigorous** if auth, billing, or data handling is the primary business risk.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "multi-user", "user accounts", "user registration", "user management"
- "authentication", "login", "signup", "JWT", "OAuth2", "sessions", "refresh tokens"
- "RBAC", "roles", "permissions" (in a web product — not enterprise IdP configuration)
- "REST API and frontend", "API with React", "API with Vue", "API with Next.js", "full-stack web app"
- "subscription billing", "Stripe", "Stripe Checkout", "pricing tiers", "free/pro plan", "feature gating"
- "tenant isolation", "data isolation", "row-level security", "multi-user database"
- "web product", "SaaS product" (without enterprise SSO or contractual SLA signals)
- "optimistic UI", "error boundaries", "loading states", "skeleton screens"
- "idempotency", "duplicate submission", "optimistic locking" (in a web product context)
- "rate limiting", "abuse prevention", "API throttling"

Or when the system under discussion has these properties:

- A user table, an auth layer, and at least one resource type that belongs to a user or workspace
- A browser frontend consuming a REST, GraphQL, or tRPC API backed by a relational database
- Multiple users who should not see each other's data
- A billing integration where subscription state controls feature access
- No enterprise identity provider requirement (no SAML, SCIM, or enterprise SSO)

Declaration examples:

```
"Standard mode, web product track — build the user invitation and RBAC flow"
"Lean mode, web product track — add subscription billing with Stripe Checkout"
"Standard mode, web product track — implement the REST API for the dashboard with multi-user isolation"
"Rigorous mode, web product track — auth service with MFA and session revocation"
```

---

## When NOT to activate

Do NOT activate this track when:

- Enterprise identity integration (SSO, SAML, OIDC against a customer IdP, SCIM provisioning) is a primary requirement — use **SaaS B2B** instead
- The product has contractual SLA obligations, DPAs, MSAs, or per-customer billing contracts — use **SaaS B2B** instead
- The product is purely consumer-facing with no workspace/org concept and the primary engineering concerns are A/B testing and product analytics — use **Consumer product** instead
- It is a mobile app without a meaningful web frontend — use **Mobile** instead
- It is a purely internal tool with a single implicit tenant and no user management complexity — no track needed; Standard or Lean mode is sufficient
- The domain is dominated by formal regulatory requirements (FedRAMP, HIPAA, PCI) — use the relevant regulatory track as primary and optionally add this track if the product also has a web product shape
- It is a public library or CLI with no web frontend — use **Open source** instead

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| `technical-debt-tracker` | N/A | N/A | Mandatory (post go-live debt register for auth, RBAC, and isolation subsystems) | Mandatory |
| `delivery-metrics-dora` | N/A | N/A | Mandatory (track this feature's impact on deployment frequency and change failure rate) | Mandatory |
| `api-contract-enforcer` | Advisory | Mandatory | Mandatory + typed client generation from spec | Mandatory + consumer-driven contract tests |
| `comprehensive-test-strategy` | Advisory | Mandatory (unit + integration) | Mandatory — full pyramid: unit + integration + E2E per user role | Mandatory + mutation testing baseline |
| `security-audit-secure-sdlc` | Advisory | Mandatory (auth flows + OWASP Top 10 basics) | Mandatory + full OWASP review + tenant isolation threat class | Mandatory + pen test checklist |
| `database-migration` | Advisory | Mandatory | Mandatory + concurrency review (locking strategy, idempotency) | Mandatory + HA plan and DR strategy |
| `accessibility` | Advisory | Advisory | Mandatory (WCAG 2.1 AA; axe-core CI gate with zero critical violations) | Mandatory + manual audit on all user flows |
| `performance-reliability-engineering` | N/A | Advisory | Mandatory (p50/p95 targets documented and verified post-deploy) | Mandatory + load test at peak projected load |
| `observability-sre-practice` | Advisory | Mandatory (error tracking + structured logs with user_id) | Mandatory + SLOs defined and measured | Mandatory + SLOs + alerting runbooks |
| `data-governance-privacy` | Advisory | Advisory | Mandatory (GDPR basics: export, deletion, consent surface) | Mandatory + full privacy review and retention audit |
| `distributed-systems-patterns` | N/A | Advisory | Mandatory (concurrency review: optimistic locking + idempotency at every mutation) | Mandatory + outbox pattern for any async side-effects |
| `caching-strategy` | N/A | Advisory | Advisory | Mandatory (cache plan with tenant-scoped keys required) |
| `feature-flag-lifecycle` | N/A | Advisory | Advisory | Mandatory |
| `disaster-recovery` | N/A | N/A | Advisory | Mandatory |
| `documentation-system-design` | Advisory | Advisory | Mandatory (API reference + user guide for auth and RBAC flows) | Mandatory (full doc set including runbooks) |

Skills not listed keep their default mode behaviour.

What the elevations actually buy, in plain English:

- `api-contract-enforcer` becomes Mandatory in Lean+ because the API is the contract between your frontend and backend; drift between them is the #1 cause of silent regressions. In Standard+, typed client generation from the spec (openapi-typescript, graphql-codegen) eliminates an entire class of integration bug.
- `comprehensive-test-strategy` at Lean requires unit and integration coverage because web products have too many data paths to rely on manual testing. At Standard+, E2E scenarios per user role are required — tests that prove a non-admin cannot perform an admin action are not optional.
- `security-audit-secure-sdlc` at Lean requires auth flow review and OWASP Top 10 basics because auth is the highest-impact attack surface in web products and the easiest to misconfigure. At Standard+, the tenant isolation threat class (IDOR, authorization bypass, horizontal privilege escalation) must be explicitly modelled.
- `database-migration` at Lean is Mandatory because web products live or die by schema evolution without downtime. At Standard+, the concurrency review requires explicit documentation of which operations need optimistic locking and which need idempotency keys.
- `accessibility` at Standard is Mandatory because the EU Accessibility Act 2025 applies to commercial web products serving EU users, and retrofitting accessibility is consistently more expensive than building it in.
- `observability-sre-practice` at Lean requires error tracking (Sentry-class) and structured logs with `user_id`. Without `user_id` on logs, you cannot diagnose a production bug reported by a specific user. At Standard+, SLOs give you objective criteria for when something is broken.
- `data-governance-privacy` at Standard is Mandatory because GDPR deletion and export requests arrive before most teams have built the capability. The cost of building it in response to a request is 3–5× the cost of building it at design time.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 2 (Design) | Auth flow must be documented: token type (JWT or sessions), access token TTL, refresh strategy (rotation policy, revocation approach), MFA options (TOTP / WebAuthn / none), logout and token invalidation. Tenant/user isolation strategy required: which DB isolation model (RLS, schema-per-tenant, or app-level scoping) with rationale. RBAC permission matrix documented: roles, what each role can do, where enforcement lives (router middleware vs service layer). API schema (OpenAPI spec or GraphQL SDL) committed as source of truth before implementation starts — no implementation before spec is frozen. Concurrency plan: identify any write operation that could race or produce duplicates; document idempotency strategy per operation. |
| Stage 3 (Build) | No raw SQL without parameterisation (ORM or parameterised queries only). `user_id` or `tenant_id` present on every INSERT and in every WHERE clause touching a user-scoped or tenant-scoped table. Auth middleware applied at router level, not per-handler — missing a handler is a security hole. Idempotency keys required for any state-mutating POST or PUT that could be retried by the client or a background job. RBAC enforcement at the service layer; UI guards alone are not sufficient. Billing state (subscription plan, feature entitlements) read from the source of truth at the API layer, not cached client-side without a TTL. |
| Stage 4 (Verify) | Full testing pyramid required: unit + integration + at least one E2E flow per user role (including a negative E2E: a member-role user cannot perform an admin-role action). Cross-user data leak test required: a negative integration test proving that user A cannot read, modify, or enumerate user B's resources through any API path. Auth edge cases all tested: expired access token → 401; invalid/tampered token → 401; refresh with revoked token → 401; request with insufficient role → 403. Accessibility: automated scan (axe-core or pa11y) runs in CI with zero critical violations on all user-facing pages. At least one concurrency test: concurrent writes to the same record (optimistic lock conflict) and duplicate submission of the same idempotent operation (second call returns same result, no duplicate side-effect). |
| Stage 5 (Ship) | API versioning policy documented before any external consumer exists. Zero-downtime migration strategy documented for any DB schema change in the release. Feature flags for any change to user-visible behaviour that is hard to roll back without a deploy. p50/p95 response time baseline documented pre-deploy; verified against NFRs post-deploy within 24 hours. Stripe webhook endpoint verified: signature validation enabled, idempotency on `event.id` implemented. |
| Phase 3 (Ongoing) | Dependency audit quarterly (all packages, runtimes, and container base images). Accessibility regression check on each UI release (automated; manual audit annually or when UI is substantially redesigned). Performance baseline re-verified on each major release. GDPR deletion and export flows tested after each data schema change to verify correctness. **Standard+ additions:** monthly debt register review (`technical-debt-tracker`) with focus on auth, RBAC, and tenant-isolation subsystems — any debt item in these areas is automatically elevated to High regardless of age; monthly DORA metrics refresh (`delivery-metrics-dora`) recording this feature's impact on deployment frequency and change failure rate. |

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| `security-audit-secure-sdlc` | `references/auth-patterns.md`, `references/tenant-isolation-lightweight.md`, `references/rate-limiting-abuse.md` |
| `database-migration` | `references/db-concurrency.md`, `references/tenant-isolation-lightweight.md` |
| `distributed-systems-patterns` | `references/db-concurrency.md` |
| `api-contract-enforcer` | `references/api-design-patterns.md` |
| `specification-driven-development` | `references/api-design-patterns.md` |
| `code-implementer` | `references/auth-patterns.md`, `references/rbac-simple.md`, `references/tenant-isolation-lightweight.md` |
| `design-doc-generator` | `references/auth-patterns.md`, `references/rbac-simple.md`, `references/api-design-patterns.md`, `references/tenant-isolation-lightweight.md` |
| `accessibility` | `references/frontend-architecture.md` |
| `data-governance-privacy` | `references/subscription-billing.md` |
| `performance-reliability-engineering` | `references/rate-limiting-abuse.md`, `references/frontend-architecture.md` |
| `caching-strategy` | `references/tenant-isolation-lightweight.md` |
| `observability-sre-practice` | `references/tenant-isolation-lightweight.md` |

Specific guidance the injection encodes:

- When `security-audit-secure-sdlc` fires, the threat model must explicitly include the horizontal privilege escalation class (IDOR, missing `user_id` scope on DB queries, JWT manipulation). Load `auth-patterns.md` to check token storage, refresh rotation, and revocation. Load `rate-limiting-abuse.md` for auth endpoint rate limits and credential-stuffing signals.
- When `database-migration` fires on a web product, load `db-concurrency.md` to verify the migration does not introduce a race condition (e.g., adding a counter column without initialising it atomically, removing a unique constraint that was preventing duplicates).
- When `code-implementer` produces code touching user-scoped or tenant-scoped tables, the reviewer checks: `user_id`/`tenant_id` in every query filter, RLS policy active if using Postgres RLS, idempotency key generated and stored for every mutation endpoint.
- When `design-doc-generator` fires, the auth section must reference `auth-patterns.md` to choose token type, TTL, and revocation strategy before any implementation decision is made. The RBAC section must reference `rbac-simple.md` to document the role matrix before the permission middleware is designed.

---

## Reference files

- `references/auth-patterns.md` — JWT vs sessions decision, access/refresh token design, OAuth2/PKCE for SPAs, refresh token rotation, MFA (TOTP and WebAuthn), social login, token revocation, password hashing, common pitfalls
- `references/tenant-isolation-lightweight.md` — shared schema + RLS vs schema-per-tenant vs app-level scoping, decision criteria, Postgres RLS setup, `user_id`/`tenant_id` propagation through request and async job lifecycle, cache key scoping, cross-user leak patterns and how to test for them
- `references/rbac-simple.md` — owner/admin/member role model, invitation flow, permission naming convention (resource:action), enforcement at service layer vs UI, RBAC vs ABAC decision, audit logging for role changes
- `references/api-design-patterns.md` — REST vs GraphQL vs tRPC decision tree, spec-first workflow, error schema consistency, cursor vs offset pagination, typed client generation (openapi-typescript, graphql-codegen), versioning policy, deprecation headers
- `references/db-concurrency.md` — optimistic locking (version column, ORM support), pessimistic locking (SELECT FOR UPDATE, advisory locks), idempotency keys (UUID from client, deduplication at handler, Redis TTL), duplicate form submission prevention, connection pooling (PgBouncer, application pool sizing), deadlock prevention
- `references/frontend-architecture.md` — server state vs client state (TanStack Query/SWR vs Zustand/Jotai), optimistic UI with rollback, error boundaries at component/page/global levels, skeleton screens, typed API client from spec, accessibility in component design, form validation (Zod + react-hook-form), code splitting
- `references/subscription-billing.md` — Stripe Checkout and Customer Portal flow, webhook handling and signature verification, idempotent event processing on `event.id`, entitlements model (subscription → plan → feature flags), feature gating at the API layer, pricing tier design, trial periods, dunning flow, graceful feature downgrade
- `references/rate-limiting-abuse.md` — per-user/per-IP/per-tenant rate limit strategies, token bucket vs sliding window algorithms, Redis-based implementation, rate limit headers (X-RateLimit-*), what to throttle and at what thresholds (auth: strict, API: moderate, expensive ops: low), credential stuffing detection, honeypot fields, CAPTCHA for high-value actions

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[2026-04-21] track-activated: web-product | mode: Standard | duration: project
```

Skill firings under this track append the track context:

```
[2026-04-22] security-audit-secure-sdlc | outcome: OK | note: auth threat model complete, IDOR class addressed | track: web-product
[2026-04-23] database-migration | outcome: OK | note: zero-downtime migration + RLS policy verified | track: web-product
[2026-04-24] comprehensive-test-strategy | outcome: OK | note: full pyramid + cross-user leak tests defined | track: web-product
```

---

## Composition with other tracks

- **+ SaaS B2B.** When the web product also targets enterprise customers who require SSO and SCIM. The web-product track handles standard auth and RBAC; SaaS B2B adds SAML/OIDC, customer IdP, contractual SLAs, and DPA obligations. Skill elevations union; strictest gate wins. The tenant isolation review at Stage 2 covers both the lightweight model (this track) and the enterprise isolation requirements (SaaS B2B).
- **+ Fintech / Payments.** When the web product processes card data or money movement beyond simple Stripe subscriptions. The web-product track handles subscription billing (Stripe Checkout); the Fintech track handles PCI scope, idempotency for payment intents, reconciliation, and fraud signals. If the product only uses Stripe Checkout with redirect (no card data on your servers), PCI scope is minimal and the Fintech track may not be needed.
- **+ Healthcare / HIPAA.** A web product handling health data. The web-product track handles standard auth and RBAC; Healthcare adds PHI classification, HIPAA audit logs, and BAA workflow. Stage 4 verification combines the cross-user leak test (this track) with the PHI access-control test (Healthcare).
- **+ Consumer product.** A web product with a strong B2C experimentation component. Web-product track handles the auth/data/API shape; Consumer product track adds experiment design, event taxonomy, and product analytics. Not common — most web products either have a user base or an experiment pipeline, not both at the same level of rigour simultaneously.

---

## Invariants — things this track will not let slide

These are the failure modes that justify the track's existence. Any one of them, unaddressed, is a gate failure in Standard+ mode:

- An API endpoint that returns another user's data under some input — IDOR or missing user-scope filter. Ship-blocker.
- Auth middleware missing on one route because it was applied per-handler rather than at the router level.
- A JWT stored in `localStorage` instead of an `httpOnly` cookie — XSS readable. If there is a documented reason (native app integration), it must be in an ADR.
- A state-mutating endpoint with no idempotency key that the client or a background job could call twice, producing duplicate records or double charges.
- Stripe webhook endpoint with no signature verification.
- An RBAC check only in the UI (a `disabled` button or hidden route) with no server-side enforcement at the service layer.
- A DB migration that adds a `user_id` column without a NOT NULL constraint and without backfilling existing rows — leaves all legacy rows queryable by any user.
- p95 API response time undefined at ship time — no NFR means no regression signal.
- Accessibility scan never run — first run in production always finds critical violations.
- A GDPR deletion flow that clears the users table but leaves the user's data in three other tables that weren't mapped at design time.
