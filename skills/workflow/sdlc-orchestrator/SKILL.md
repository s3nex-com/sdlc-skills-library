---
name: sdlc-orchestrator
description: >
  The master workflow skill for the full software development lifecycle. Activate when
  the user wants to start a new feature, task, or project and drive the complete
  pipeline end-to-end: from idea through design, implementation, testing, PR, and docs.
  Also activate when the user wants to know where they are in the pipeline, resume a
  paused pipeline, skip or re-run a stage, or check overall workflow status. This is
  the single entry point for "build something properly". Trigger for: "start a new
  feature", "begin the pipeline", "run the sdlc", "what stage are we on", "resume the
  workflow", "orchestrate the build", "full pipeline", "start from scratch",
  "end to end build", "build this from requirements to production", "new task",
  "new project".
---

# SDLC orchestrator

## Purpose

This skill is the conductor of the full software development lifecycle for a small,
high-velocity team. It manages the order stages run in, the outputs each stage
produces, the inputs each stage requires, and the minimum gates that must pass before
moving forward.

Use this as your single entry point when starting any non-trivial feature or project.
The goal is to move fast and leave a trail — not ceremony for its own sake.

---

## When to use

- Starting any non-trivial feature or project from scratch — this is the single entry point for the full SDLC pipeline
- Resuming a paused pipeline — use "resume the pipeline for [feature]" and the orchestrator will read the status files
- Checking where you are in the pipeline — "what stage are we on?" reads `docs/sdlc-status.md`
- Starting with an existing PRD and jumping to a specific stage — "we have an approved PRD, start at the design stage"
- Running a spike to evaluate a technology or approach before committing to a pipeline run
- Taking over a brownfield codebase and needing a baseline assessment before new feature work
- Handling a production hotfix that bypasses stages 1–2 and goes directly to build and verify

## When NOT to use

- **Trivial one-line fixes.** Just make the change. Typos, comment edits, bumping a constant — these do not need a pipeline. A single focused commit with a clear message is enough.
- **Pure exploration with no commitment to ship.** Use the Spike workflow path directly (see below). The orchestrator assumes you are building toward a deployed outcome; a spike is disposable investigation.
- **You already have an approved PRD and just need implementation.** Start at `design-doc-generator` directly, or jump to Stage 2 via the "jumping to a stage" flow. The orchestrator will otherwise re-validate Stage 1 artifacts you already have.
- **Pure operations work with no code change** (e.g. rotating a secret, bouncing a pod). Use the relevant runbook; the pipeline is for code changes.

If your situation does not match any of the above, use the orchestrator.

---

## Skill execution log

At the start of every session where this skill fires, append one line to
`docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] sdlc-orchestrator | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: brief description
```

If `docs/skill-log.md` does not exist, create it with this header first, then append the entry:

```markdown
# Skill execution log

<!-- Created on first run. Append one line per skill firing. Never delete entries. -->
```

Every supporting skill invoked during the pipeline must also append to this log using
the same format when it fires. The log is the audit trail — lightweight, structured,
and machine-readable enough for the orchestrator to reconstruct pipeline state.

**outcome values:**
- `OK` — skill completed, output produced, ready to proceed
- `PARTIAL` — skill ran but output is incomplete (e.g. 5/7 stories done); skill should be re-run
- `BLOCKED` — skill could not complete; pipeline is stalled; review root cause before resuming

**next field:** the skill that should run next, or `"none"` if the pipeline is complete or paused.

---

## Process

1. At the start of every session, create or update `docs/sdlc-status.md` and append to `docs/skill-log.md`.
2. If mode is not declared, ask the 3-question mode derivation (who uses this, does it have external API contracts, is it reversible). Derive and confirm the mode before proceeding.
3. If no track is declared and the PRD or request contains domain keywords, suggest the appropriate track and ask the user to confirm. Never auto-activate a track without confirmation.
4. At Stage 1: invoke `prd-creator` then `requirements-tracer`. Verify the gate before moving to Stage 2.
5. At Stage 2: invoke `specification-driven-development`, `design-doc-generator`, `architecture-decision-records`. Freeze contracts. Verify the gate.
6. At Stage 3: invoke `code-implementer`, `comprehensive-test-strategy`, `architecture-fitness`. Apply inline security gates. Verify the gate.
7. At Stage 4: invoke `executable-acceptance-verification` and `security-audit-secure-sdlc`. Run accessibility check for user-facing UI features. Verify the gate.
8. At Stage 5: invoke `pr-merge-orchestrator`, `release-readiness`, `documentation-system-design`. Update `docs/sdlc-status.md` to complete.
9. If a gate fails at any stage: record the blocker in `docs/sdlc-status.md`, do not proceed, and direct the user to the blocking issue.
10. Log every skill invocation and every gate result to `docs/skill-log.md` in the `outcome | next | note` format.

## The pipeline

Five stages. Stages 1 and 2 can overlap. Stages 3 and 4 can overlap. Stage 5 is always last.

```
Stage 1: Define      PRD + requirements        [prd-creator, requirements-tracer]
    ↓ (problem is clear, stories are testable)
Stage 2: Design      Spec + design doc         [specification-driven-development,
    ↓ (design is approved, contracts frozen)    design-doc-generator, adr,
                                                llm-app-development*]
Stage 3: Build       Implementation + tests    [code-implementer,
    ↓ (all phases done, tests pass)             comprehensive-test-strategy,
                                                architecture-fitness,
                                                llm-app-development*]
Stage 4: Verify      Acceptance + security     [executable-acceptance-verification,
    ↓ (BDD passes, security clean, UI a11y)     security-audit-secure-sdlc,
                                                accessibility*]
Stage 5: Ship        PR + merge + docs + cost  [pr-merge-orchestrator,
    ↓                                           release-readiness,
  Done                                          documentation-system-design,
                                                cloud-cost-governance]

* conditional: llm-app-development fires when the feature uses an LLM;
  accessibility fires for user-facing UI features.
```

Supporting skills that run alongside:
- `technical-risk-management` — seeded at Stage 1, updated at each gate
- `architecture-decision-records` — records decisions made at Stages 2 and 3
- `stakeholder-sync` — invoked when a stakeholder-facing deliverable is produced
- `architecture-fitness` — CI-enforced import boundaries, dep budgets, dead code (Stage 3 gate + monthly in Phase 3)
- `llm-app-development` — eval-driven development, prompt versioning, RAG/agent design (Stage 2 + Stage 3 when feature uses an LLM)
- `accessibility` — WCAG 2.2 AA compliance (Stage 4 gate for user-facing UI; required in Standard/Rigorous)
- `cloud-cost-governance` — per-feature cost attribution and estimates (Stage 5 pre-release review + monthly in Phase 3)

**Overlap rules:**
- Stages 1 + 2 can run together if stories are stable enough to start spec design
- Stages 3 + 4 can run together — acceptance tests can be written and run while
  implementation is finishing, as long as the component under test is complete
- Never start Stage 3 before Stage 2 is fully approved — implementing against an
  unapproved design creates rework

---

## How to invoke

### Starting fresh

```
User: start a new feature — device telemetry ingestion
```

The orchestrator will:
1. Create `docs/sdlc-status.md` and `docs/skill-log.md` if they do not exist
2. Log this session to `docs/skill-log.md`
3. If mode is not declared, ask the 3-question mode derivation
4. If no track is active on this project and the request contains domain keywords (see "Track discovery" below), suggest a track and ask to confirm
5. Invoke `prd-creator` to define the problem
6. Guide you through each stage from there

### Resuming

```
User: resume the pipeline for device telemetry
```

The orchestrator will:
1. Read `docs/sdlc-status.md` to find the current stage and status
2. Read `docs/skill-log.md` to understand what was last done
3. Resume from where work stopped, or explain what is blocking progress

### Jumping to a stage

```
User: we already have an approved PRD — start at the design stage
```

The orchestrator will:
1. Verify prerequisite inputs exist (PRD, stories)
2. Flag anything missing
3. Begin Stage 2 if prerequisites are satisfied

### Checking status

```
User: what stage are we on?
User: sdlc status
```

Reads `docs/sdlc-status.md` and reports: current stage, status, blockers, next action.

### Hotfix workflow path

Bypasses Stages 1–2. Start at Stage 3 with a clear problem statement:
1. Write a test that reproduces the bug
2. Fix the bug, verify the test passes
3. Go directly to Stage 4 (security) and Stage 5 (PR + merge)
4. Create an ADR if the fix has architectural implications
5. Log everything to `docs/skill-log.md`

### Spike / exploration workflow path

A spike is time-boxed exploratory work that produces a **decision or learning**, not a deployment. Use this workflow path when the goal is to evaluate a technology, validate an architectural approach, investigate a performance issue, or prototype a solution before committing to building it.

Spikes do NOT go through stages 1–5. They have their own lightweight path.

**When to use the spike workflow path:**
- Technology evaluation: "should we use Kafka or NATS for this?"
- Architectural proof-of-concept: "can we achieve < 100ms p99 with this approach?"
- Performance investigation: "why is this query slow at scale?"
- Feasibility check: "can we integrate with this third-party API in time?"

**Spike process:**

1. **Define the question** (5 minutes — do this before writing a line of code)
   - What specific question are you answering?
   - What outcome would cause you to adopt vs reject vs defer the approach?
   - What is the timebox? (2–4 hours is typical; 1 day maximum before declaring a spike too large)

2. **Explore** — write throwaway code, run experiments, read docs, benchmark
   - This code is not production code. It does not need tests, docs, or reviews.
   - But: take notes as you go. The spike's value is the learning, not the code.

3. **Decide** (do not extend the timebox — decide with the information you have)
   - **Adopt**: the approach works; proceed to a proper pipeline run (Stage 1)
   - **Reject**: the approach does not work; document why so you do not repeat the investigation
   - **Defer**: inconclusive; record what you learned and what would need to be true to revisit

4. **Record the decision as an ADR**
   - Every spike that produces a decision must produce an ADR (even a one-paragraph one)
   - The ADR is the artifact. The code is disposable.
   - Use `architecture-decision-records` skill to write it.

5. **Log to `docs/skill-log.md`**:
   ```
   [YYYY-MM-DD] sdlc-orchestrator (spike) | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: [question] → [adopt/reject/defer]
   ```

**What a spike does NOT produce:**
- PRD.md (the spike informs the PRD; it does not replace it)
- DESIGN.md (same)
- Merged production code
- Unit/integration tests

**If the spike produces "adopt":** start the full pipeline at Stage 1 with the learning from the spike as input. The spike code is reference material, not starting point.

**If the timebox is exceeded without a decision:** the spike is too large. Break it into smaller spikes with smaller questions, or timebox more aggressively. Do not let a spike become an undocumented prototype that someone deploys.

---

### Brownfield / codebase-assessment workflow path

Use this workflow path when you are inheriting an existing codebase rather than starting fresh. The goal is to establish a baseline before adding any new work — not to retrofit Phase 1 artifacts onto code that already exists.

**When to use the brownfield workflow path:**
- Taking over an existing codebase from another team or company
- Inheriting a project mid-flight with no documentation
- Joining a running project and needing to establish a baseline before adding new features
- Post-acquisition technical due diligence

**Brownfield process:**

1. **Baseline the debt** (use `technical-debt-tracker`)
   - Run a debt assessment across all 7 debt types
   - Identify Critical and High severity items immediately
   - Produce a debt register as the starting point

2. **Baseline the delivery health** (use `delivery-metrics-dora`)
   - Collect available deployment history (git log, CI logs, release tags)
   - Apply cold-start proxy metrics if history is sparse
   - Establish a DORA baseline — even rough numbers are better than none

3. **Audit security and dependencies** (use `security-audit-secure-sdlc` + `dependency-health-management`)
   - Run dependency scan: flag Critical/High CVEs immediately
   - Generate SBOM
   - Check secrets in code (scan the full history, not just HEAD)
   - Run SAST on the full codebase

4. **Map what exists** (use `architecture-review-governance`)
   - Identify actual architecture vs assumed architecture
   - Find the anti-patterns that are already in place
   - Document any existing ADRs or design decisions (create ADRs from tribal knowledge)

5. **Pick a mode and any applicable track(s), then proceed**
   - Brownfield assessment is complete — now pick a mode (Lean/Standard/Rigorous) for any new work
   - If the codebase is in a domain with a track (Fintech, Healthcare, etc.), activate the track now so the mode-level gates also gain track gate modifications for future work
   - New features on a brownfield codebase still go through the full pipeline for the new work
   - Do not retrofit Phase 1 artifacts onto existing code — assess it, don't rewrite its history

**Outputs from brownfield workflow path:**
- `docs/brownfield-assessment.md`: debt register + DORA baseline + security findings summary
- SBOM file
- List of Critical/High debt items to address before new features proceed
- Mode recommendation for ongoing work

**Log format:**
```
[YYYY-MM-DD] sdlc-orchestrator (brownfield) | outcome: OK|BLOCKED|PARTIAL | next: skill-name | note: brief description
```

---

## Operating modes

Every pipeline run operates in one of four modes. The mode determines which skills are required vs optional, how hard the gates are, and how much time to expect.

**Declare the mode at session start.** If you do not declare one, the orchestrator will ask three questions and derive it.

Modes compose with **tracks** (domain overlays). See "Tracks" section below. Tracks never disable skills — they only elevate optional skills to mandatory, tighten gate criteria, and inject domain-specific reference material when a skill fires.

### Mode selection: 3-question derive

If the user does not declare a mode, ask these three questions before starting:

1. **Who uses this if it breaks?**
   - (A) Internal team only → lean toward Nano or Lean
   - (B) Paying customers or external users → lean toward Standard
   - (C) Regulated users, financial transactions, or critical infrastructure → Rigorous

2. **Does this have external API contracts — interfaces another system or team depends on?**
   - (A) No → stays at current level
   - (B) Yes → elevate one level

3. **Is this reversible if something goes wrong?**
   - (A) Yes, easy rollback → stays at current level
   - (B) Hard rollback (migration, data change) → elevate one level
   - (C) Irreversible (data deletion, external system side effects) → Rigorous regardless

**Scoring:** Start at Nano. Apply elevations. Final level is the mode.

**Override:** User can always declare explicitly: "use rigorous mode", "run in lean mode", "nano mode for this one".

---

### Mode: Nano
**Use when:** Solo or pair, internal tool, no external dependencies, hours not days.

**Orchestrator trigger rule:** Skip the orchestrator for a truly isolated change (typo, constant bump, label fix, single additive field on an internal-only model). Use the orchestrator — even at Nano — if the change touches auth, authorisation, a DB schema, or any interface that other code calls. The gate checks take minutes and the blast radius is real. If you are unsure, use the orchestrator.

**Skills active:**
- Phase 1: `prd-creator` (optional — one paragraph if obvious, skip if truly trivial)
- Phase 2: `code-implementer` → `code-review-quality-gates` → `pr-merge-orchestrator`
- `architecture-fitness` if a CI config already exists (runs automatically; no extra effort)

**Security hard stops — not advisory, block unconditionally:**
- Secrets scan: always required; findings block merge
- SAST: required if the change touches auth, session handling, authorisation, or permissions; Critical/High block merge
- SCA (dependency scan): required if any new library is added; Critical CVEs block merge
- Inline security checklist (4 items in `code-implementer`): input validation, auth check, no secrets in code, injection surface — must be answered before each phase gate passes

**Code review rule:** Self-review acceptable for pure internal logic changes. Peer review required if the change touches authentication, authorisation, database schema, or any interface other code calls.

**Migration tripwire:** Any `ALTER TABLE`, `DROP TABLE`, or `CREATE INDEX` on an existing table triggers an automatic promotion to Lean. Stop — do not proceed as Nano. Log the promotion and run the Lean Phase 1 pipeline before touching the schema.

**Gates:** Advisory for quality signals (test coverage, docs completeness). Hard for the security stops above.

**Estimated effort:** 2–4 hours | ~15k Claude tokens

**Skip explicitly:** `requirements-tracer`, `design-doc-generator`, `specification-driven-development`, `architecture-review-governance`, `executable-acceptance-verification`, `llm-app-development`, `accessibility`, `cloud-cost-governance`, all Phase 3/4 skills

**Example triggers:**
- "add a field to the admin dashboard"
- "internal script to bulk-update device records"
- "fix the broken link in the settings page"
- "quick internal tooling change"

---

### Mode: Lean
**Use when:** Small team, standard feature, internal or small user group, no hard external API contracts.

**Skills active:**
- Phase 1: `prd-creator` + `requirements-tracer` + `design-doc-generator` (with security checkpoint — Section 4, 5 questions, required before Stage 3)
- Phase 2: `code-implementer` + `comprehensive-test-strategy` + `code-review-quality-gates` + `release-readiness` + `pr-merge-orchestrator` + `architecture-fitness` (Stage 3 gate)
- Security: SAST + SCA (dependency scan) + secrets scan at Stage 4 — all three are hard gates

**Conditional skills — signal-based activation (verify before Stage 3 starts; do not rely on memory):**
- Any new route, endpoint, gRPC method, or event topic introduced → add `specification-driven-development`
- Any HTML, JSX, template, or UI component file modified → add `accessibility` (WCAG 2.2 AA spot-check at Stage 4)
- Any LLM API call, prompt template, or RAG component in scope → add `llm-app-development` (Stages 2 and 3)
- Any feature flag variable or toggle introduced → add `feature-flag-lifecycle`
- Any `ALTER TABLE`, `DROP TABLE`, or `CREATE INDEX` required → add `database-migration` (mandatory)

**Gates:** Standard — all Stage gates apply, but gates can pass with team consensus (no external sign-off needed).

**Estimated effort:** 1–2 days | ~40k Claude tokens

**Skip explicitly:** `architecture-review-governance`, `executable-acceptance-verification`, `performance-reliability-engineering` (unless NFRs explicitly defined), `api-contract-enforcer`, `cloud-cost-governance` (unless cost-sensitive), all Phase 4 skills

**Example triggers:**
- "new feature for the device dashboard"
- "implement user notification preferences"
- "add a Kafka consumer for telemetry events"
- "standard feature build"

---

### Mode: Standard
**Use when:** Customer-facing, external API contracts, team of 3+, features that affect billing, auth, or data integrity.

**Skills active:**
- Phase 1: All relevant Phase 1 skills including `security-audit-secure-sdlc` (STRIDE), `specification-driven-development`, `architecture-decision-records`
- Phase 2: All Phase 2 skills, including `architecture-fitness` (Stage 3 hard gate) and `accessibility` (Stage 4 hard gate for any user-facing UI — required in Standard)
- If feature uses an LLM: `llm-app-development` required at Stages 2 and 3 (eval harness, prompt versioning, RAG/agent design)
- Phase 3: `delivery-metrics-dora` + `technical-debt-tracker` post go-live + `cloud-cost-governance` (Stage 5 pre-release cost review)
- Security: Full STRIDE at design + SAST + dependency scan + secrets + SBOM at release

**Gates:** Hard — all gates must pass before proceeding. External sign-off not required but peer review mandatory.

**Estimated effort:** 3–5 days | ~80k Claude tokens

**Skip explicitly:** `formal-verification` (unless distributed protocol), Phase 4 by default (add explicitly if needed)

**Example triggers:**
- "build the device provisioning API"
- "implement customer-facing reporting"
- "new public API endpoint"
- "feature that touches billing or payments"
- "redesign the auth flow"

---

### Mode: Rigorous
**Use when:** Payment processing, authentication/authorization, regulated data (HIPAA, PCI, SOC2), critical infrastructure, features where a bug causes data loss or financial loss.

**Skills active:** All applicable skills across all phases including:
- `architecture-review-governance` with external sign-off
- `architecture-fitness` as a blocking CI gate at Stage 3 (import boundaries, dep budgets, dead code)
- `accessibility` as a blocking Stage 4 gate with documented WCAG 2.2 AA audit evidence for every user-facing surface
- `llm-app-development` required whenever any LLM is in the critical path (eval thresholds must be met before Stage 5)
- `cloud-cost-governance` as a Stage 5 pre-release gate (per-feature cost estimate signed off; unit economics documented)
- `formal-verification` for any distributed protocols
- `chaos-engineering` for critical paths
- Full Phase 3 post go-live
- `executable-acceptance-verification` with formal sign-off document

**Gates:** Hard + external sign-off required on gate checklist. No self-approval.

**Estimated effort:** 1–2 weeks | ~150k+ Claude tokens

**Example triggers:**
- "implement payment processing"
- "redesign authentication"
- "build the data export for GDPR compliance"
- "critical infrastructure change"
- "SOC2 requirement"

---

### Mode promotion

If you discover mid-pipeline that the current mode is insufficient:

1. Stop. Log a BLOCKED entry to `docs/skill-log.md` with note: "mode promotion required: Lean → Standard"
2. Update `docs/sdlc-status.md` with the new mode
3. Run any Phase 1 skills that were skipped in the lower mode
4. Re-run Stage 2 if design artifacts are insufficient for the higher mode
5. Continue from where you stopped

**Common promotion triggers:**
- Discovered the feature has external API consumers → promote Nano→Lean or Lean→Standard
- DB schema change (`ALTER TABLE`, `DROP TABLE`, `CREATE INDEX`) discovered in Nano → auto-promote to Lean immediately; do not proceed with the schema change under Nano
- Discovered a database migration is required → promote one level
- Legal or compliance flag raised → promote to Rigorous regardless of current mode
- Performance NFRs suddenly critical → add `performance-reliability-engineering` at minimum
- Conditional skill signal detected mid-build (new route, UI file, LLM call, flag) → add the appropriate conditional skill before Stage 3 continues; do not defer to post-build

Mode promotion is not failure — it is the system working correctly.

---

## Tracks — domain specialization

Tracks are a second, orthogonal dimension to mode. **Mode** answers *how much rigor*. **Track** answers *what domain am I in*. A session is always in one mode and may be in zero, one, or more tracks.

Full guide: `docs/tracks.md`. All 10 tracks live in `skills/tracks/`.

### The 10 tracks

| Track | Covers |
|-------|--------|
| Fintech / Payments | Card data, money movement, PCI scope, regulated financial services |
| SaaS B2B | Multi-tenant products with SSO, RBAC, contractual SLAs |
| Web product | Multi-user web apps: auth, RBAC, API + frontend, DB concurrency, subscription billing |
| Data platform / ML ops | Pipelines, schema registries, ML/LLM production |
| Healthcare / HIPAA | PHI handling, HIPAA, HL7/FHIR |
| Regulated / government | FedRAMP, SOC 2, ISO 27001, CMMC, StateRAMP |
| Real-time / streaming | Kafka/Kinesis/Pulsar, low-latency, stream processing |
| Consumer product | B2C, experimentation, product analytics |
| Open source | Public libraries with semver, contributor pipeline, CVE disclosure |
| Mobile | iOS, Android, React Native, Flutter |

### Declaring a track

At session start, declare mode and track(s) together:

```
"Standard mode, Fintech track — implement the payment intent endpoint"
"Lean mode, SaaS B2B track — build the tenant invitation flow"
"Rigorous mode, Healthcare + Regulated tracks — clinical notes service with FedRAMP Moderate"
```

### Track discovery

Two ways a track becomes active:

1. **Explicit declaration** (above).
2. **Orchestrator suggestion** — at Stage 1, the orchestrator reads the PRD and proposes a track based on keywords ("PCI", "multi-tenant", "FedRAMP", "HIPAA", "Kafka", "A/B test", "semver", "iOS"). The user must confirm before activation. Never auto-activate without confirmation.

Suggestion keyword table:

| Phrase in PRD | Suggested track |
|---------------|----------------|
| "PCI", "cardholder", "payment intent", "payout", "KYC/AML" | Fintech |
| "multi-tenant", "tenant isolation", "SSO", "SAML", "RBAC", "SLA credits" | SaaS B2B |
| "data pipeline", "schema registry", "data contract", "RAG", "feature store" | Data platform / ML ops |
| "HIPAA", "PHI", "clinical notes", "HL7", "FHIR", "BAA" | Healthcare |
| "FedRAMP", "ATO", "SOC 2", "ISO 27001", "CMMC" | Regulated / government |
| "Kafka", "Kinesis", "Pulsar", "exactly-once", "watermarks" | Real-time / streaming |
| "A/B test", "experiment", "Amplitude", "Mixpanel", "referral" | Consumer |
| "open source", "semver", "CONTRIBUTING.md", "CVE disclosure" | Open source |
| "iOS", "Android", "React Native", "Flutter", "TestFlight", "APNS" | Mobile |

### What a track does at each stage

When any stage runs with track(s) active:

1. **Skill list union.** Take base skills for the mode, add every track elevation. If a track makes a skill Mandatory in Lean mode that would otherwise be Advisory, it is now Mandatory.
2. **Gate criteria merge.** Take base gate criteria for the stage. Merge in every track's Stage N modifications. If two tracks modify the same gate, **strictest wins**.
3. **Reference injection.** When a skill fires, load its normal references plus any track-specific references mapped to that skill in the track's reference injection map.
4. **Evaluate the gate.** Base mode gate first; then track gate modifications. If any track modification is a hard gate and fails, the pipeline is BLOCKED regardless of mode.

### Persistence

Track(s) live in `docs/sdlc-status.md`:

```markdown
## Current state
- Mode: Standard
- Track(s): Fintech, Healthcare
- Pipeline stage: 3 (Build)
- Active feature: payment-intent-v2
```

Once set on a project, every new feature inherits the track(s). Change explicitly:

```
"Add the Regulated track to this project"
"Drop the Healthcare track — no PHI after the scope change"
```

### Log format for tracks

Track activations and deactivations append to `docs/skill-log.md`:

```
[2026-05-01] track-activated: fintech-payments | mode: Standard | duration: project
[2026-05-01] track-activated: healthcare-hipaa | mode: Standard | duration: project
[2026-05-05] track-deactivated: healthcare-hipaa | reason: scope change, no PHI involved
```

Skill firings under an active track append the track to the log line:

```
[2026-05-05] security-audit-secure-sdlc | outcome: OK | next: code-implementer | note: PCI-scope review complete | track: fintech-payments
```

### Multi-track composition rules

- **Skill elevation:** union of every active track's elevations
- **Gate modification:** strictest modification wins
- **Reference injection:** all applicable references load

Example: a B2B healthcare SaaS product → `saas-b2b + healthcare-hipaa`. Both tenant-isolation tests and HIPAA audit-log evidence are mandatory. `documentation-system-design` at Stage 5 must provide both SLA documentation and audit trail evidence.

### Workflow paths vs tracks

The three **workflow paths** below (Hotfix, Spike, Brownfield) are orthogonal to tracks. A workflow path modifies *which stages run*. A track modifies *how a stage runs inside a domain*. `Lean mode + Fintech track + Hotfix path` is a valid combination — the hotfix skips Stages 1–2 but fintech gate modifications still apply to Stages 3, 4, 5.

---

## Stage-by-stage guide

### Stage 1: Define

**Skills:** `prd-creator`, `requirements-tracer`
**Goal:** Understand what to build and why. Stories must be testable before moving forward.

**What happens:**
1. If no PRD exists: run `prd-creator` — produce a lean PRD (5 sections: problem,
   goals, non-goals, constraints, success metrics)
2. Decompose the PRD into user stories with BDD acceptance criteria (Given/When/Then)
3. Every story must be independently testable — if it cannot be automated, it is
   too vague; refine it

**Outputs:**
- `docs/PRD.md`
- `docs/stories.md` (user story list with acceptance criteria)
- `tests/acceptance/*.feature` stubs
- Initial risk register entries

**Gate to Stage 2:**
- [ ] Problem statement is clear and specific
- [ ] Goals are measurable (not "improve performance" — "p95 < 200ms under 1000 RPS")
- [ ] Non-goals are explicit (prevents scope creep)
- [ ] Every story has BDD acceptance criteria
- [ ] No story is untestable

**Lean rule:** A PRD does not need 11 sections. It needs a clear problem, a measurable
goal, and an explicit boundary of what is not in scope. If you have those three things,
you can move.

---

### Stage 2: Design

**Skills:** `specification-driven-development`, `design-doc-generator`,
`architecture-decision-records`
**Conditional skills:** `llm-app-development` (fires when the feature uses an LLM — design the eval harness, prompt versioning strategy, RAG shape, and agent tool surface before coding)
**Goal:** Frozen contracts and an approved design before a single line of production
code is written.

**What happens:**
1. Identify all API surfaces from the stories (REST, events, gRPC)
2. Write specs for each surface (pick one format per interface — OpenAPI for REST,
   Protobuf for gRPC, AsyncAPI for events)
3. Validate specs with `validate_openapi.py` (for REST)
4. Produce `DESIGN.md` — synthesise PRD, stories, and specs into implementation phases
5. Run a self-review against the architecture anti-patterns checklist
6. Record all significant design decisions as ADRs
7. **Freeze contracts** — once Stage 3 starts, specs do not change without an ADR
   and re-evaluation of affected implementation

**Outputs:**
- `specs/` directory (API spec files)
- `docs/DESIGN.md` (approved)
- `docs/adr/` entries for significant decisions
- Risk register updates

**Gate to Stage 3:**
- [ ] All API surfaces from stories have a spec
- [ ] Specs pass validation
- [ ] `DESIGN.md` covers all stories (every story maps to at least one data flow)
- [ ] Every NFR has a named design mechanism (not just aspirations)
- [ ] Every implementation phase names its test approach (unit/integration/acceptance — not generic)
- [ ] Every implementation phase names its documentation deliverable
- [ ] No unresolved design questions (open questions have owners + deadlines)
- [ ] Contracts frozen — team is aligned that specs do not change without an ADR

**Lean rule:** `DESIGN.md` does not need 11 sections. It needs: why we built it this
way, what the components are, how data flows, and what the implementation phases are
(in order, each independently deployable). That's it.

---

### Stage 3: Build

**Skills:** `code-implementer`, `comprehensive-test-strategy`, `architecture-fitness`
**Conditional skills:** `llm-app-development` (run the eval harness against each prompt/agent change; treat eval regression as a build failure)
**Goal:** Implement all design phases with tests written alongside the code.

**What happens:**
1. Break `DESIGN.md` implementation phases into ordered tasks
2. Implement phase by phase — each phase must be independently deployable
3. Write tests alongside each component (unit + integration), not after
4. Follow the 70/20/10 test pyramid: unit / integration / E2E
5. Apply security checklist at each task (STRIDE mitigations from the design)
6. If implementation reveals a design error: stop, create an ADR for the deviation,
   do not implement around a design problem silently
7. Log progress to `docs/skill-log.md` at the end of each phase

**Outputs:**
- Implemented code (all phases)
- Unit, integration, and contract tests
- `docs/implementation-status.md`
- ADRs for any deviations from `DESIGN.md`
- Updated API reference (new/changed endpoints documented)
- Updated README for any new env vars or setup steps
- Runbook stubs for any new operational scenarios

**Gate to Stage 4:**
- [ ] All implementation phases complete
- [ ] Unit and integration tests pass, zero failures
- [ ] All deviations from design have approved ADRs
- [ ] `docs/implementation-status.md` up to date
- [ ] No tasks in "Blocked" state
- [ ] API reference current for all new/changed endpoints
- [ ] Runbook stubs exist for every new P1/P2 operational scenario
- [ ] `architecture-fitness` checks pass in CI (import boundaries clean, dep budgets within limits, no new dead code)
- [ ] If LLM in use: `llm-app-development` eval harness is green against the committed threshold

---

### Stage 4: Verify

**Skills:** `executable-acceptance-verification`, `security-audit-secure-sdlc`
**Conditional skills:** `accessibility` (required for any user-facing UI; mandatory in Standard and Rigorous modes — WCAG 2.2 AA audit against the new/changed surfaces)
**Goal:** All BDD scenarios pass. Security is clean. UI is accessible. No surprises in production.

**What happens:**

**Acceptance (runs first):**
1. Run all BDD scenarios from `tests/acceptance/*.feature`
2. For any failure: determine root cause — implementation bug or wrong criterion
3. Fix and re-run until all scenarios pass
4. Produce acceptance sign-off note (one paragraph, not a ceremony)

**Security (runs in parallel with acceptance or after):**
1. STRIDE verification — confirm all mitigations from Stage 2 are implemented (Standard/Rigorous); in Lean, verify the 5-question design-time security checkpoint answers were implemented as stated
2. SAST scan — all Critical/High findings must be resolved before proceeding (required in Lean and above)
3. SCA dependency scan — no Critical CVEs permitted (required in Lean and above)
4. Secret scan — no secrets in code or config (required in all modes including Nano)

**Outputs:**
- Acceptance test run report (all scenarios pass)
- SAST scan report (clean)
- Dependency scan report (clean)
- Updated traceability matrix (test links populated)

**Gate to Stage 5:**
- [ ] Every BDD scenario passes
- [ ] Every story maps to at least one passing scenario
- [ ] SAST clean (no Critical/High)
- [ ] Dependency scan clean (no Critical CVEs)
- [ ] Secret scan clean
- [ ] API reference reviewed — new endpoints documented, no undocumented breaking changes
- [ ] Runbook stubs from Stage 3 reviewed — sufficient to hand off to on-call
- [ ] If user-facing UI: `accessibility` WCAG 2.2 AA audit passes (required in Standard/Rigorous; spot-check in Lean)

**Lean rule:** Security is not negotiable. Everything else can be trimmed. All three security gates (SAST, SCA dependency scan, secrets scan) take minutes and catch real problems. All three are hard gates in Lean — run them every time.

---

### Stage 5: Ship

**Skills:** `pr-merge-orchestrator`, `release-readiness`, `documentation-system-design`, `cloud-cost-governance`
**Goal:** Merge clean. Production stable. Docs updated. Cost of the new feature is understood and attributed.

**What happens:**
1. Pre-merge check (5 items: all Stage 4 gates passed, CI green, PR description
   complete, reviewers assigned, no unresolved blocking comments)
2. Generate PR description from pipeline artifacts (what changed, why, how to test,
   rollback plan)
3. Assign reviewer(s) — at minimum one engineer who did not write this code
4. Merge with squash (preferred) or merge commit if history matters
5. If production deployment: run release readiness check
   (DB migration safety, rollback plan, canary strategy 10%→50%→100%)
6. Update documentation: runbooks for new operational scenarios, API guide for new
   endpoints, architecture diagrams if components changed
7. Log completion to `docs/skill-log.md`

**Outputs:**
- Merged PR with full description
- Release tag (vMAJOR.MINOR.PATCH)
- Updated `docs/sdlc-status.md` (pipeline complete)
- Updated `docs/skill-log.md` (final entry for this pipeline run)
- Updated runbooks / API guide / diagrams

**Gate (pipeline complete):**
- [ ] PR merged, CI passes on main
- [ ] Release tag created
- [ ] Documentation updated for all new operational scenarios
- [ ] `docs/sdlc-status.md` marked complete
- [ ] Pre-release cost review complete (`cloud-cost-governance`) — per-feature cost estimate recorded; attribution tags in place; required in Standard/Rigorous

**Lean rule:** Documentation is not optional but it does not need to be exhaustive.
Write what the next engineer (or you in 6 months) needs to operate this feature
safely. A runbook is a few bullets about how to deploy, roll back, and debug — not
a textbook.

---

## Pipeline status dashboard

Maintain `docs/sdlc-status.md` throughout the pipeline. Update at every stage gate.

```markdown
# SDLC pipeline: [Feature name]

**Current stage:** Stage N — [stage name]
**Status:** In progress | Blocked | Complete
**Last updated:** YYYY-MM-DD
**Mode:** Nano | Lean | Standard | Rigorous
**Track(s):** none | fintech-payments | saas-b2b | healthcare-hipaa, regulated-government | ...

| Stage | Name    | Status      | Gate passed | Notes |
|-------|---------|-------------|-------------|-------|
| 1     | Define  | Complete    | Yes         | PRD + 8 stories |
| 2     | Design  | Complete    | Yes         | Specs frozen, DESIGN.md approved |
| 3     | Build   | In progress | —           | Phase 2 of 3 |
| 4     | Verify  | Not started | —           | |
| 5     | Ship    | Not started | —           | |

**Blockers:** [None or description]
**Next action:** [Specific next step]
```

**Track(s)** is a required field. Value is the comma-separated list of active track names (from `skills/tracks/<name>/`) or the literal `none`. Zero tracks is valid and common.

---

## Skill execution log format

`docs/skill-log.md` is the session-level audit trail. Every skill appends to it using this format:

```
[YYYY-MM-DD] skill-name | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: brief description
```

Example entries:

```
[2026-04-07] sdlc-orchestrator | outcome: OK | next: prd-creator | note: pipeline started — device telemetry ingestion
[2026-04-07] prd-creator | outcome: OK | next: requirements-tracer | note: PRD created from feature brief
[2026-04-07] requirements-tracer | outcome: PARTIAL | next: requirements-tracer | note: 6/8 stories decomposed; 2 blocked on missing NFRs
[2026-04-08] requirements-tracer | outcome: OK | next: specification-driven-development | note: all 8 stories complete with BDD stubs
[2026-04-08] specification-driven-development | outcome: OK | next: design-doc-generator | note: OpenAPI spec written for ingest API
[2026-04-08] design-doc-generator | outcome: BLOCKED | next: architecture-review-governance | note: design stalled — need arch review before proceeding
[2026-04-09] architecture-review-governance | outcome: OK | next: design-doc-generator | note: arch review complete; proceed with event-driven approach
[2026-04-09] design-doc-generator | outcome: OK | next: code-implementer | note: DESIGN.md produced, Stage 2 gate passed
[2026-04-10] code-implementer | outcome: OK | next: code-implementer | note: Phase 1 of 3 complete
[2026-04-10] architecture-decision-records | outcome: OK | next: none | note: ADR-003 — chose push over pull
```

### State tracking

The orchestrator reads the last 10 log entries at the start of each session to reconstruct pipeline context. It does not re-read the full history.

**How the orchestrator uses outcome values:**
- `BLOCKED` entries: identify the blocker from the `note` field, resolve it, then re-run the blocked skill
- `PARTIAL` entries: the skill needs to be re-run; check the `note` field for what remains
- `OK` entries with a `next` field: the natural next skill to invoke; verify its prerequisites before starting

**`docs/skill-log.md` is created on first pipeline run.** It does not exist until the orchestrator (or any skill) creates it. All skills check for its existence before appending.

---

## Returning to an earlier stage

If a problem is discovered mid-pipeline that requires revisiting an earlier stage:

1. Set current stage to "Blocked" in `docs/sdlc-status.md`, note the reason
2. Return to the appropriate earlier stage and fix the root cause
3. Re-run the gate for that stage
4. Reset all downstream stages that depended on the changed output

| Change at stage | Stages to reset |
|----------------|----------------|
| PRD changed (scope, goals, NFRs) | 2, 3, 4 |
| Stories changed (added/removed/changed) | 2, 3, 4 |
| Spec changed (new endpoint, schema change) | 3, 4 |
| Design changed (component, data model) | 3, 4 |
| Implementation bug found in acceptance | 3, 4 |
| Security finding requiring design change | 2, 3, 4 |

---

## Phase 3 / sustained operations cadence

After a feature ships, several skills run on a recurring cadence (not per-pipeline). The orchestrator does not drive these in real time, but it records their schedule here so ops work does not drift.

**Monthly:**
- `architecture-fitness` — review CI trends (rule violations silenced, new boundary drift, dep budget creep); tighten rules or file debt items
- `cloud-cost-governance` — per-service and per-feature cost review; flag anomalies; attribute unowned spend
- `technical-debt-tracker` — groom the debt register; retire closed items; re-rank by impact
- `delivery-metrics-dora` — refresh DORA numbers; note trend direction

**Quarterly:**
- `dependency-health-management` — full SBOM refresh and CVE review
- `architecture-review-governance` — lightweight drift check against recorded ADRs
- Re-evaluate whether any Phase 3 cadence needs to become more frequent

**Triggered (event-based), not scheduled:**
- `incident-postmortem` — after every P1/P2 incident
- `chaos-engineering` — before entering a new tier of scale, or after an incident that exposed a resilience gap
- `project-closeout` — when a feature or initiative reaches its natural end
- `team-coaching-engineering-culture` — when a team signal (retro, attrition, quality regression) warrants it

Log every cadence firing to `docs/skill-log.md` the same way pipeline skills do.

---

## Common questions

**Can two stages run in parallel?**
Yes — Stages 1+2 can overlap if stories are stable. Stages 3+4 can overlap
component-by-component. Never start Stage 3 before Stage 2 is approved.

**What if requirements change during implementation?**
This is a scope change. Stop. Run `requirements-tracer` scope impact analysis.
If approved, update stories, update `DESIGN.md` for affected components, re-run
only the affected implementation. Never silently implement new scope.

**What if a gate fails?**
Do not proceed. Document what failed in `docs/sdlc-status.md`, fix the root cause,
re-run the gate. Gates are not suggestions — they exist because skipping them
creates downstream pain that costs more than fixing the problem now.

**A track gate modification is failing but the base mode gate passes — what do I do?**
Treat it as a gate failure. Tracks compose strictest-wins. A track that modifies a gate
makes that modification a hard requirement for projects in that domain. If the
modification is inappropriate for this specific feature, deactivate the track for this
feature (`"this feature is out of scope for the Fintech track"`) rather than silently
skipping the evidence.

**What about very small tasks?**
For tasks smaller than a few hours, the pipeline compresses naturally:
- Stage 1 = a paragraph describing the change and why
- Stage 2 = a quick design note or ADR (skip if the change is purely additive)
- Stage 3 = implementation with tests
- Stage 4 = tests pass, quick security check
- Stage 5 = PR with a clear description
The log and status file still apply — they take minutes and pay off later.

---

## Skill execution log reference

See the "Skill execution log" and "Skill execution log format" sections above for the full format and state-tracking guidance. The orchestrator is responsible for creating `docs/skill-log.md` if it doesn't exist. All supporting skills append to this file when they fire, using the same `outcome | next | note` format.

Spike entries use the format:
```
[YYYY-MM-DD] sdlc-orchestrator (spike) | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: [question] → [adopt/reject/defer]
```

Example spike entry:
```
[2026-04-10] sdlc-orchestrator (spike) | outcome: OK | next: prd-creator | note: Kafka vs NATS evaluation → adopt NATS; lower ops overhead for our scale
```

Track activation/deactivation entries:
```
[2026-05-01] track-activated: fintech-payments | mode: Standard | duration: project
[2026-05-05] track-deactivated: healthcare-hipaa | reason: scope change, no PHI involved
```

When a skill fires under an active track, append `| track: <name>` (or `| tracks: <a>,<b>`) to the standard log line:
```
[2026-05-05] security-audit-secure-sdlc | outcome: OK | next: code-implementer | note: PCI-scope review complete | track: fintech-payments
```

---

## Output format

### `docs/sdlc-status.md` — maintained throughout the pipeline

```markdown
# SDLC pipeline: [Feature name]

**Current stage:** Stage N — [stage name]
**Status:** In progress | Blocked | Complete
**Last updated:** YYYY-MM-DD
**Mode:** Nano | Lean | Standard | Rigorous
**Track(s):** none | [track names]

| Stage | Name    | Status      | Gate passed | Notes |
|-------|---------|-------------|-------------|-------|
| 1     | Define  | Complete    | Yes         | PRD + N stories |
| 2     | Design  | In progress | —           | Specs in review |
| 3     | Build   | Not started | —           | |
| 4     | Verify  | Not started | —           | |
| 5     | Ship    | Not started | —           | |

**Blockers:** [None or description]
**Next action:** [Specific next step]
```

### `docs/skill-log.md` — one line per skill firing

```
[YYYY-MM-DD] skill-name | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: brief description
```

## Reference files

- `references/workflow-usage-guide.md` — Worked examples for common scenarios
- `references/stage-handoff-templates.md` — Input/output contracts between stages
- `references/sdlc-status-dashboard.md` — Full dashboard template
- `references/troubleshooting.md` — What to do when a stage is stuck

See also:
- `docs/tracks.md` — domain tracks (parallel dimension to mode)
- `skills/tracks/` — the 10 track packages
- `skills/tracks/CLAUDE.md` — track index with one-line descriptions
