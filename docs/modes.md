# Operating modes

The mode you pick controls which skills run, how hard the gates are, and how much time to budget. Pick wrong and you either over-engineer a two-hour fix or under-engineer a payment flow. Get it right upfront; promoting mid-flight is possible but costs time.

---

## Overview

| Mode | Context | Skills active | Gates | Est. time | Claude tokens |
|------|---------|---------------|-------|-----------|---------------|
| **Nano** | Internal tool, solo/pair, hours | 4–5 | Advisory + security hard stops | 2–4 hrs | ~15k |
| **Lean** | Small team, standard feature, days | 8–10 | Standard | 1–2 days | ~40k |
| **Standard** | Customer-facing, API contracts, week | 16–18 | Hard | 3–5 days | ~80k |
| **Rigorous** | Payment/auth/regulated, 1–2 weeks | All relevant | Hard + sign-off | 1–2 weeks | ~150k+ |

Workflow paths: **Hotfix** (skip to Stage 3), **Spike** (time-boxed exploration), **Brownfield** (codebase assessment)

Domain tracks (orthogonal to mode — see `docs/tracks.md`): Fintech, SaaS B2B, Data platform / ML ops, Healthcare / HIPAA, Regulated / government, Real-time / streaming, Consumer, Open source, Mobile. A session is in exactly one mode and zero or more tracks.

---

## How to select a mode

### Option A: Declare it directly

```
"Start a new feature in lean mode"
"Run this in rigorous mode — it touches payments"
"Nano mode — this is a 2-hour internal fix"
```

### Option B: Let the orchestrator derive it

The orchestrator asks three questions:

1. Who uses this if it breaks? `(internal / external users / regulated or financial)`
2. Does another system or team depend on this API contract? `(no / yes)`
3. Is this reversible if something goes wrong? `(easy rollback / hard rollback / irreversible)`

**Decision logic — start at Nano and promote:**

```
Start: Nano
  → External users?              promote to Standard
  → API contract dependency?     promote one level
  → Hard rollback?               promote one level
  → Irreversible?                promote to Rigorous regardless
  → Regulated / financial?       promote to Rigorous regardless
```

**Examples:**

| Scenario | Answers | Mode |
|----------|---------|------|
| Internal dashboard, no API, easy rollback | internal / no / easy | Nano |
| Internal dashboard + new internal API | internal / yes / easy | Lean |
| Customer dashboard + external API | external / yes / easy | Standard |
| Payment feature | financial / any / any | Rigorous |

---

## Mode Nano

### When

- Solo engineer or pair
- Internal team is the only user
- No external API contracts
- Easy to roll back
- Expected total time: hours, not days

### What runs

**Phase 1** — optional if the task is obvious:
- `prd-creator` — one paragraph, not a full PRD. Skip entirely if the task is self-evident ("add export button to admin panel").

**Phase 2** — all three required:
- `code-implementer` — implement with tests; inline security hard stops apply (see below)
- `code-review-quality-gates` — self-review acceptable for pure internal logic; peer review **required** if the change touches auth, authorisation, DB schema, or any interface other code calls
- `pr-merge-orchestrator` — PR with a description, merge

**Security hard stops — these block the PR regardless of mode, no exceptions:**
- Secrets scan must be clean before merge — always
- SAST required if the change touches auth, session handling, authorisation, or permissions — Critical/High findings block merge
- SCA (dependency scan) required if any new library is added — Critical CVEs block merge
- The inline security checklist in `code-implementer` (4 items: input validation, auth check, no secrets in code, injection surface) must be answered for every task before the phase gate passes

**Gates:** Advisory for quality signals (test coverage, docs). The security hard stops above are not advisory — they block unconditionally.

**Migration tripwire:** If the change contains `ALTER TABLE`, `DROP TABLE`, or `CREATE INDEX` on an existing table, Nano auto-promotes to Lean. Database schema changes are not a Nano-mode operation.

### When to use the orchestrator at Nano

Skip the orchestrator for pure isolated changes: typos, constant bumps, label fixes, single-component additive features. Use the orchestrator even at Nano when the change touches auth, authorisation, DB schema, or any interface that other code calls — the blast radius is non-trivial and the orchestrator's gate checks pay for themselves. If you are unsure whether a change is truly isolated, use the orchestrator.

### What you skip

`requirements-tracer`, `design-doc-generator`, `specification-driven-development`, `architecture-review-governance`, `executable-acceptance-verification`, all Phase 3/4 skills, `release-readiness` (add it only for production deployments with real rollback risk).

### Example — start to finish

```
User: "Nano mode. Add a CSV export button to the admin device list page."

Orchestrator:
1. [Skip prd-creator — task is clear]
2. code-implementer: CSV export endpoint + frontend button + unit tests
3. code-review-quality-gates: self-review (does it work, does it handle empty list)
4. pr-merge-orchestrator: PR "Add CSV export to admin device list", merge

Skill log:
[2026-04-20] code-implementer | outcome: OK | next: code-review-quality-gates | note: CSV export endpoint + button, 3 unit tests
[2026-04-20] code-review-quality-gates | outcome: OK | next: pr-merge-orchestrator | note: self-review clean
[2026-04-20] pr-merge-orchestrator | outcome: OK | next: none | note: merged — v1.4.2

Total: ~2 hours
```

---

## Mode Lean

### When

- Small team (2–4 engineers)
- Internal or small beta user group
- Feature is non-trivial but scope is clear
- No hard external API contracts (or internal-only APIs)
- Expected time: 1–2 days

### What runs

**Phase 1** — all three:
- `prd-creator` (Mode A, 20 min) — one-page PRD: problem, goals, NFRs, non-goals
- `requirements-tracer` (30 min) — 3–5 stories with BDD acceptance criteria
- `design-doc-generator` (45 min) — component design, data flow, implementation phases

**Phase 2:**
- `code-implementer` — phase-by-phase from DESIGN.md
- `comprehensive-test-strategy` — unit + integration, 70/20 ratio minimum (default — track overrides apply: Real-time/Streaming and Data platform tracks shift this toward integration-heavy coverage; Consumer track adds experiment-path scenarios; track override takes precedence over the default ratio)
- `code-review-quality-gates` — peer review required, 1 reviewer minimum
- `release-readiness` — pre-deployment checklist
- `pr-merge-orchestrator` — PR + merge + tag

**Conditional skills — signal-based activation (check before Stage 3 starts; do not rely on team memory):**
- Any new route, endpoint, gRPC method, or event topic introduced → add `specification-driven-development`
- Any HTML, JSX, template, or UI component file modified → add `accessibility` (WCAG 2.2 AA spot-check at Stage 4)
- Any LLM API call, prompt template, or RAG component in scope → add `llm-app-development` (Stages 2 and 3)
- Any feature flag variable or toggle introduced → add `feature-flag-lifecycle`
- Any `ALTER TABLE`, `DROP TABLE`, or `CREATE INDEX` required → add `database-migration` (mandatory, not optional)

**Security:** SAST + SCA (dependency scan) + secrets scan at Stage 4. No full STRIDE required — but the 5-question design-time security checkpoint in `design-doc-generator` Section 4 is required before Stage 3 starts.

**Gates:** Standard. All gates apply. Peer review required. No external sign-off.

### What you skip

`architecture-review-governance`, all Phase 4 skills. `executable-acceptance-verification` is optional — add it if stories are complex. `performance-reliability-engineering` — add only if explicit latency/throughput NFRs exist. `api-contract-enforcer` — add if external consumers discovered.

### Example — start to finish

```
User: "Lean mode. Build device group management — users can group IoT devices into logical sets."

Stage 1 — Define:
  prd-creator: PRD — device grouping, goals (reduce time-to-find by 50%), NFRs (< 100ms list query)
  requirements-tracer: 4 stories (create group, add device, remove device, list groups with devices)

Stage 2 — Design:
  design-doc-generator: DESIGN.md — REST endpoints, data model (groups + junction table), 2 phases

Stage 3 — Build:
  code-implementer Phase 1: data model + migrations
  code-implementer Phase 2: API endpoints + tests

Stage 4 — Verify:
  comprehensive-test-strategy: 12 unit tests, 4 integration tests
  SAST scan: clean
  SCA scan: clean (no Critical CVEs in new dependencies)
  Secrets scan: clean

Stage 5 — Ship:
  release-readiness: checklist passed (DB migration tested in staging, rollback plan documented)
  pr-merge-orchestrator: PR merged, tagged v1.5.0

Total: ~1.5 days
```

---

## Mode Standard

### When

- Customer-facing feature
- External API contracts (another team or system depends on your API)
- Touches auth, billing, or data integrity
- Team of 3+
- Expected time: 3–5 days

### What runs

**Phase 1 — all relevant skills:**
- `prd-creator` + `requirements-tracer` + `design-doc-generator`
- `specification-driven-development` — API specs written and frozen before implementation
- `security-audit-secure-sdlc` — STRIDE threat model at design time
- `architecture-decision-records` — significant design decisions recorded
- `technical-risk-management` — risk register updated

**Phase 2 — all:**
- `code-implementer` + `comprehensive-test-strategy` + `code-review-quality-gates`
- `api-contract-enforcer` — Pact consumer-driven contract tests if external consumers exist
- `executable-acceptance-verification` — BDD scenarios run as formal sign-off
- `release-readiness` + `pr-merge-orchestrator`
- Add `performance-reliability-engineering` if explicit latency/throughput NFRs
- Add `database-migration` if schema changes involved

**Phase 3 — post go-live:**
- `delivery-metrics-dora` — track this feature's impact on DORA
- `technical-debt-tracker` — update register

**Security:** Full STRIDE + SAST + dependency scan + secrets + SBOM at release.

**Gates:** Hard. All gates must pass. Peer review mandatory (1 reviewer minimum). No self-approval.

### Example — trigger and what fires

```
User: "Standard mode. Build the device provisioning API — the mobile app team is consuming it."

→ prd-creator: PRD for provisioning API
→ requirements-tracer: 6 stories with BDD
→ specification-driven-development: OpenAPI spec written and shared with mobile team
→ security-audit-secure-sdlc: STRIDE — provisioning is auth-adjacent, rate limiting required
→ architecture-decision-records: ADR for provisioning token design
→ design-doc-generator: DESIGN.md with 3 implementation phases
→ code-implementer: all phases
→ comprehensive-test-strategy: unit + integration + contract tests (Pact with mobile team)
→ api-contract-enforcer: Pact provider tests passing
→ executable-acceptance-verification: all 6 BDD scenarios pass
→ security-audit-secure-sdlc (Stage 4): SAST clean, deps clean, secrets clean
→ release-readiness: checklist + canary plan (10% → 50% → 100%)
→ pr-merge-orchestrator: PR merged, tagged v2.0.0

Total: ~4 days
```

---

## Mode Rigorous

### When

- Payment processing or financial transactions
- Authentication / authorization systems
- Regulated data (HIPAA, PCI, SOC2, GDPR)
- Critical infrastructure (data pipeline, message broker, core platform service)
- A bug causes data loss, financial loss, or a regulatory violation
- Expected time: 1–2 weeks

### What runs

Everything in Standard, plus:
- `architecture-review-governance` — formal architecture review with at least one reviewer not on the implementation team
- `formal-verification` — if any custom distributed protocol is involved (consensus, ordering, idempotency)
- `chaos-engineering` — chaos experiment set run against all critical paths
- `executable-acceptance-verification` — formal sign-off document produced (not just tests passing)
- Full SBOM + Sigstore image signing at release

**Gates:** Hard + external sign-off. No gate can be self-approved. Formal sign-off document required before merge.

### Example

```
User: "Rigorous mode. Implement payment intent and charge flow."

→ Full Phase 1 including STRIDE (PCI scope, tokenization, idempotency)
→ formal-verification: idempotency protocol for charge-retry logic (TLA+ sketch)
→ Full Phase 2 including contract tests with payment provider
→ chaos-engineering: simulate payment provider outage, DB slow query during charge
→ formal architecture review (peer, not self)
→ executable-acceptance-verification: formal sign-off from tech lead + QA
→ Release: SBOM + cosign image signing + canary 1% → 10% → 50% → 100%
```

---

## Workflow paths

Workflow paths modify *which stages run*. They are orthogonal to both mode and domain track — all three compose (`Lean mode + Fintech track + Hotfix path` is valid).

### Hotfix

**Triggered by:** "hotfix", "production is down", "critical bug in prod"

- Bypasses Stages 1–2
- Jumps to Stage 3 with tight scope definition
- Stage 4 (security) and Stage 5 (merge gate) still required
- Time: 1–4 hours

### Spike

**Triggered by:** "explore", "investigate", "should we use X or Y", "proof of concept", "evaluate"

- Time-boxed: 2–4 hours, 1 day maximum
- Output: a decision + ADR. Not deployable code.
- If the decision is "adopt", exit into the full pipeline (Lean or Standard) for implementation.

### Brownfield

**Triggered by:** "taking over", "inherited codebase", "assess this project", "joining mid-flight", "technical due diligence"

Run in order:
1. `technical-debt-tracker`
2. `delivery-metrics-dora`
3. `security-audit-secure-sdlc`
4. `dependency-health-management`
5. `architecture-review-governance`

Output: `docs/brownfield-assessment.md` — debt register, DORA baseline, security findings.

Then pick a mode (and any domain tracks that apply) for all new work from that point forward.

---

## Mode-track minimum mode guidelines

Some tracks carry domain obligations that cannot be honoured inside Nano's 2–4 hour envelope. The table below defines the minimum mode for each track. You can always run a track at a higher mode than its minimum; you cannot run it at a lower one without explicitly scoping it to a non-regulated surface and documenting why.

| Track | Minimum mode | Rationale |
|-------|-------------|-----------|
| Fintech / Payments | Lean (for any payment-adjacent surface); Rigorous for PCI-scope changes | Idempotency, reconciliation, and PCI checklist cannot complete in 2–4 hours |
| SaaS B2B | Lean | Tenant isolation review requires design-stage discipline |
| Web product | Lean | Auth and RBAC design are minimum Lean concerns |
| Data platform / ML ops | Lean | Data contracts need a design gate before code ships |
| Healthcare / HIPAA | Lean | PHI classification + audit log design are non-negotiable even at smallest scope |
| Regulated / government | Standard | Control mapping, evidence collection, and separation of duties are not Nano concepts |
| Real-time / streaming | Lean | Delivery semantics and backpressure require a design-gate document |
| Consumer product | Nano | Nano is acceptable with a flag and event sanity check; experiment design is not required at Nano |
| Open source | Lean | Semver and CHANGELOG discipline require at least a design review |
| Mobile | Lean | Store submission and phased rollout planning are minimum Lean concerns |

**Conflict resolution:** When a track mandates a skill at a mode level below the declared mode, the declared mode wins (its requirements include everything below it). When a track mandates a skill at a mode level *above* the declared mode, the track elevation wins — that skill becomes mandatory regardless of mode. The net effect: skill elevations union, and the track never removes a mode's existing requirements.

---

## Domain tracks

Tracks overlay the library for specific domains — Fintech, SaaS B2B, Healthcare, and so on. A track never replaces a mode; it adds on top:

- Optional skills become mandatory in that domain.
- Stage gates tighten or gain new required evidence.
- Track-specific reference material loads alongside a skill's normal references.

Multi-track composition: skill elevations union, gate modifications strictest-wins, reference injection additive.

Declare a track together with the mode:
```
"Standard mode, Fintech track — implement the payment intent endpoint"
"Rigorous mode, Healthcare + Regulated tracks — clinical notes service"
```

Or let the orchestrator suggest one based on PRD keywords; you confirm before activation.

Full guide: `docs/tracks.md`. Track packages live under `skills/tracks/`.

---

## Mode promotion

Start in one mode, discover you need more rigor. Do not restart — promote in place.

**Steps:**
1. Log `BLOCKED` to `docs/skill-log.md`: `"mode promotion: Lean → Standard — discovered external API consumers"`
2. Update `docs/sdlc-status.md` with the new mode
3. Run Phase 1 skills that were skipped
4. Re-run Stage 2 if the current design is insufficient
5. Continue from the current stage

**Common promotion triggers:**

| Discovery | Action |
|-----------|--------|
| Discovered external API consumers | Promote one level |
| DB schema change (`ALTER TABLE`, `DROP`, `CREATE INDEX`) in Nano | Auto-promote to Lean — no exception |
| DB migration with no rollback path | Promote one level |
| Legal or compliance flag raised | Promote to Rigorous |
| Performance NFRs suddenly critical | Add `performance-reliability-engineering` at minimum |
| Irreversible data operation identified | Promote to Rigorous |
