---
name: saas-b2b
description: >
  Activates when the user mentions multi-tenancy, tenant isolation, per-customer data,
  SSO / SAML / OIDC, enterprise login, IdP integration, RBAC, role-based access,
  custom roles, permissions model, SLA, contractual uptime, SLA credits, usage
  metering, consumption-based billing, per-seat pricing, enterprise contract, MSA,
  or DPA. Also triggers on explicit declaration: "SaaS B2B track" or
  "B2B track".
---

# SaaS B2B track

## Purpose

This track covers products sold to businesses where each customer is a logically isolated tenant with its own users, data, configuration, and billing. B2B SaaS has a distinct shape the base library does not encode: a tenant boundary that must be enforced end-to-end, enterprise identity integration that is non-negotiable after a certain deal size, a role model that customers expect to configure themselves, and contractual obligations (SLAs, DPAs, notice periods for breaking changes) that convert engineering decisions into revenue events. Running B2B SaaS in the default library leaves these concerns implicit. The track makes them explicit and blocks the pipeline if they are missed.

Typical mode pairing: Standard. Lean is appropriate for early-stage B2B SaaS still finding shape. Rigorous is for products approaching or inside a SOC 2 audit cycle.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "multi-tenant", "tenant isolation", "per-customer data", "per-tenant"
- "SSO", "SAML", "OIDC", "enterprise login", "IdP integration"
- "SCIM", "user provisioning", "JIT provisioning"
- "RBAC", "role-based access", "custom roles", "permissions model"
- "SLA", "contractual uptime", "credits if we breach", "service credits"
- "usage metering", "consumption-based billing", "metered billing", "per-seat pricing"
- "enterprise contract", "MSA", "DPA", "data processing addendum"
- "SOC 2" in a commercial (non-government) context

Or when the system under discussion has these properties:

- A tenant identifier threaded through every business object and every request
- A customer-facing admin surface for user management, roles, or billing
- A contractual relationship that carries uptime or notice-period obligations
- Separate billing plans per customer tier (free / paid / enterprise)
- Enterprise customers configuring the product via their own IdP and role catalogue

Declaration examples:

```
"Standard mode, SaaS B2B track — build the tenant invitation flow"
"Lean mode, SaaS B2B track — wire up Stripe metered billing for the API tier"
"Standard mode, SaaS B2B + Healthcare tracks — clinical workflow for multi-tenant clinics"
```

---

## When NOT to activate

Do NOT activate this track when:

- The product is consumer-facing (B2C) — use Consumer product track instead
- The product is a purely internal tool used only by employees of one company — no track needed
- Every customer lives in one shared DB with no tenant concept at all — fix that leak before activating this track; multi-tenancy is a precondition, not an output of the track
- The domain is dominated by formal regulatory frameworks (FedRAMP, HIPAA) — use the Regulated / government or Healthcare track as the primary, and add SaaS B2B as a secondary track only if the product is also multi-tenant commercial SaaS
- You are integrating as a vendor into someone else's B2B product — that is a library integration, not a B2B SaaS product

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| api-contract-enforcer | Advisory | Mandatory | Mandatory + versioning discipline | Mandatory + contract tests per tenant tier |
| observability-sre-practice | Standard | Per-tenant SLOs | Per-tenant SLOs + alerting | Per-tenant SLOs + tenant-specific error budgets |
| feature-flag-lifecycle | Advisory | Mandatory | Mandatory + per-tenant rollout | Mandatory + per-tenant rollout + audit log |
| data-governance-privacy | Mandatory | Mandatory | Mandatory + DPA template | Mandatory + DPA per customer |
| release-readiness | Standard | Standard + customer comms | Standard + customer comms + SLA impact review | Standard + customer comms + SLA impact review + customer approval for breaking changes |
| security-audit-secure-sdlc | Standard | Standard | Mandatory + tenant isolation review | Mandatory + SOC 2 mapping |
| architecture-fitness | N/A | N/A | Mandatory (tenant isolation boundary rules enforced in CI — tenant context must not leak across module boundaries) | Mandatory |
| cloud-cost-governance | N/A | N/A | Mandatory (per-tenant cost attribution required to support usage-based billing and cost-per-customer reporting) | Mandatory |
| caching-strategy | N/A | N/A | Mandatory (per-tenant cache key scoping required — cross-tenant cache poisoning is a silent tenant isolation bug) | Mandatory |

Skills not listed keep their default mode behaviour. A cell reading "Mandatory + X" means the skill fires AND X is required for the stage gate to pass.

Notes on the additional elevations:

- `architecture-fitness` at Standard+ uses CI-enforced import boundary rules to make tenant isolation a detectable, not just documented, property. Without it, tenant context leaks silently as the codebase grows — a code review will miss it; a fitness function will not.
- `cloud-cost-governance` at Standard+ is required because per-tenant cost attribution feeds directly into usage-based billing accuracy, cost-per-customer reporting, and the unit economics that determine whether the product is sustainably priced. An SaaS B2B product that cannot attribute costs per tenant cannot verify its pricing model.
- `caching-strategy` at Standard+ requires per-tenant cache key scoping. Shared cache keys are a tenant isolation failure. A query for tenant A's data should never be served from a cached response for tenant B's query, even if the parameters look similar. This class of bug is silent and typically manifests as data exposure in a customer incident, not a CI failure.

What the elevations actually buy, in plain English:

- `api-contract-enforcer` becomes Mandatory because customers build against your API and a silent breaking change costs trust. Versioning discipline means a documented deprecation window, not "we'll add `/v2/` when it hurts".
- `observability-sre-practice` moves to per-tenant because an aggregate 99.95% that hides one tenant at 80% is a churn event waiting to happen. Per-tenant dashboards let on-call see which customer is unhappy before the CSM does.
- `feature-flag-lifecycle` must target tenants. A per-tenant kill switch is the remediation for every "we rolled out a change and one enterprise customer hated it" incident.
- `data-governance-privacy` at Standard+ requires a DPA template you can ship to customers on request. Enterprise procurement will not proceed without one.
- `release-readiness` in Standard+ extends to customer communication for SLA-relevant and breaking changes. In Rigorous, breaking changes require explicit customer approval, not just notice.
- `security-audit-secure-sdlc` at Standard+ includes a tenant isolation review specifically — it is the failure mode unique to this domain.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 2 (Design) | Tenant isolation boundary must be explicit in the design doc. Data flow must show which data is tenant-scoped and which is global. Shared infrastructure that could leak across tenants (caches, queues, rate limiters) must be called out with its isolation strategy. |
| Stage 4 (Verify) | Cross-tenant data leak test scenario required — a negative test that proves tenant A cannot read or write tenant B's data through any known path (API, background job, admin surface, cache, search index). SSO / SAML flow tested end-to-end against at least one real IdP sandbox (Okta or Azure AD). |
| Stage 5 (Ship) | Breaking API changes require a customer notification period of 30 to 90 days depending on the contract. The release-readiness output must list affected customers, the notice window required per contract, and the notification channel. |
| Phase 3 (Ongoing) | Monthly per-tenant SLA compliance report (uptime and error-rate per tenant, rolled up to tier). Annual SOC 2 control review if the product is SOC 2 audited or in the run-up to an audit. |

Strictest-wins applies if another active track modifies the same gate. Example composition: SaaS B2B + Healthcare at Stage 4 means both a cross-tenant leak test AND a PHI-specific access-control test are required; neither is optional because the other ran.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| api-contract-enforcer | `references/sla-and-metering.md` |
| observability-sre-practice | `references/multi-tenancy-patterns.md`, `references/sla-and-metering.md` |
| feature-flag-lifecycle | `references/multi-tenancy-patterns.md` |
| data-governance-privacy | `references/customer-onboarding-flow.md`, `references/multi-tenancy-patterns.md` |
| security-audit-secure-sdlc | `references/multi-tenancy-patterns.md`, `references/rbac-design.md`, `references/sso-saml-integration.md` |
| release-readiness | `references/sla-and-metering.md`, `references/customer-onboarding-flow.md` |
| code-implementer | `references/multi-tenancy-patterns.md`, `references/rbac-design.md` |
| design-doc-generator | `references/multi-tenancy-patterns.md`, `references/rbac-design.md`, `references/sso-saml-integration.md` |

Specific guidance the injection encodes:

- When `observability-sre-practice` fires, mandate a per-tenant SLO dimension. Default: an aggregate SLO plus a per-tier SLO split into free, paid, and enterprise. In Rigorous mode, name accounts get their own error budget. Tenant_id is a required label on every SLI metric; dashboards must be filterable by tenant.
- When `feature-flag-lifecycle` fires, enforce tenant-granularity rollout capability. A per-tenant kill switch is mandatory — if you cannot turn the flag off for one angry customer at 2am without redeploying, it fails the gate. Rollout order for risky flags is internal → free tier → paid cohort → enterprise cohort → named accounts.
- When `api-contract-enforcer` fires and the change is breaking, enforce the customer notification window from the gate modifications table before the change can merge behind the flag that enables it. Load `sla-and-metering.md` if the breaking change affects billable events or metering shapes.
- When `security-audit-secure-sdlc` fires in Standard+ mode, the threat model must include the cross-tenant leak class (authorization bypass, cache poisoning, shared state leak, log leak). SOC 2 mapping in Rigorous mode outputs control IDs that `documentation-system-design` picks up as evidence targets.
- When `code-implementer` produces code touching a tenant-scoped table, the reviewer checks RLS policies, tenant_id on every insert, and tenant context propagation into any async work spawned from the handler.

---

## Reference files

- `references/multi-tenancy-patterns.md` — pool vs silo vs bridge tenancy models, when to use each, enforcement at application and database layers (Postgres RLS, schema-per-tenant, database-per-tenant), tenant context propagation.
- `references/sso-saml-integration.md` — SAML vs OIDC decision, SP-initiated vs IdP-initiated flows, common enterprise IdPs, JIT provisioning, SCIM, metadata exchange, certificate rotation.
- `references/rbac-design.md` — role hierarchy, permission model, custom roles, RBAC vs ABAC trade-off, enforcement at the API / service layer, audit logging for permission changes, WorkOS / Auth0 / Clerk integration notes.
- `references/sla-and-metering.md` — uptime SLA tiers, credit calculation, per-tier SLOs, usage metering instrumentation, event sourcing for billable events, Stripe Billing integration hooks, defining the billable event cleanly.
- `references/customer-onboarding-flow.md` — standard enterprise onboarding path (MSA → DPA → SSO → SCIM → training → go-live), handover checklist, timing expectations, what to do when a step stalls.

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[2026-04-21] track-activated: saas-b2b | mode: Standard | duration: project
```

Skill firings under this track append the track context:

```
[2026-04-22] api-contract-enforcer | outcome: OK | note: v2 deprecation plan approved | track: saas-b2b
[2026-04-23] observability-sre-practice | outcome: OK | note: per-tier SLOs configured (free/paid/enterprise) | track: saas-b2b
```

---

## Composition with other tracks

- **+ Healthcare / HIPAA.** Common for B2B SaaS selling to clinical customers. HIPAA audit logging is additive to tenant audit logging; the two share the same log pipeline but carry different retention (HIPAA: 6 years). DPA becomes BAA for PHI-handling flows.
- **+ Fintech / Payments.** B2B SaaS handling money movement for customers. PCI scope is usually narrow (a billing / payout subsystem). Tenant isolation review at Stage 2 must cover the payments subsystem specifically; a tenant seeing another tenant's Stripe secrets is a double breach.
- **+ Regulated / government.** Customers require SOC 2 / FedRAMP. Tenant isolation maps to a specific set of SOC 2 controls (CC6.1, CC6.6). SLA commitments may be contractually tighter than the commercial-tier defaults.
- **+ Open source.** Rare but real: B2B SaaS with an open-source core. Track combination means public API versioning discipline (open source) and customer notification discipline (B2B) both apply to the same API surface — strictest-wins typically favours the open-source semver commitment.

---

## Invariants — things this track will not let slide

These are the failure modes that justify the track's existence. Any one of them, unaddressed, is a gate failure in Standard+ mode:

- A query or endpoint that returns rows from another tenant. Not "in theory could"; demonstrably does under some input. Ship-blocker.
- An SLA committed in a contract that engineering cannot actually measure. The measurement must exist and match the contract wording.
- A breaking API change rolled out without customer notice. The notification log is evidence; its absence is a gate failure.
- A per-tenant feature flag that exists but cannot be flipped off for a single named tenant without redeploy.
- A billable event counted twice because an emission retry wrote two records with different idempotency keys.
- A custom role a customer created that grants a permission the product does not intentionally expose to customers.
- SSO configured but tested only against your dev IdP, never against a customer-representative sandbox (Okta, Entra ID).
- A DPA signed but not honoured in the data flow (e.g., data processor list out of date, sub-processor added without notice).
- A release that changes tenant-visible behaviour behind a flag that defaults on, shipped without per-tenant rollout through the free → paid → enterprise ladder.
- A production incident report that cannot answer "which tenants were affected and which were not" because the observability surface was not tenant-aware.

If the team considers any of the above acceptable as a trade-off for velocity, do not activate this track — the track is not for that team. Either the team is building a different shape of product (internal tool, consumer, integration), or the team should mature to the point where these invariants are not controversial.
