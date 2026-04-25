# Tracks — domain specialization

A **track** is a curated overlay on the 41-skill library for a specific domain. Modes answer *how much rigor*. Tracks answer *what domain am I in*. The two compose: `Standard mode + Fintech track` means Standard-level rigor applied with fintech-specific mandatory skills, tightened gates, and domain reference material.

A track is not a new skill. It is a lens. It pulls three levers:

1. **Skill elevation** — optional skills become mandatory in that domain.
2. **Gate modification** — stage gate criteria tighten or add new required evidence.
3. **Reference injection** — when a skill fires during a tracked session, track-specific reference files load alongside the skill's own references.

Tracks are additive, not subtractive. They never disable skills — they add constraints.

---

## The 14 tracks

| Track | Covers | Typical mode | Min mode |
|-------|--------|--------------|----------|
| [Fintech / Payments](../skills/tracks/fintech-payments/TRACK.md) | Card data, money movement, PCI scope, regulated financial services | Standard or Rigorous | Lean (Rigorous for PCI-scope changes) |
| [SaaS B2B](../skills/tracks/saas-b2b/TRACK.md) | Multi-tenant B2B products with SSO, RBAC, SLA obligations | Standard | Lean |
| [Web product](../skills/tracks/web-product/TRACK.md) | Multi-user web apps: auth, RBAC, API + frontend, DB concurrency, subscription billing | Lean or Standard | Lean |
| [Data platform / ML ops](../skills/tracks/data-platform-mlops/TRACK.md) | Pipelines, schema registries, ML/LLM in production | Standard | Lean |
| [Healthcare / HIPAA](../skills/tracks/healthcare-hipaa/TRACK.md) | PHI handling, HIPAA, HL7/FHIR, clinical data | Rigorous | Lean |
| [Regulated / government](../skills/tracks/regulated-government/TRACK.md) | FedRAMP, SOC 2, ISO 27001, CMMC, formal compliance frameworks | Rigorous | Standard |
| [Real-time / streaming](../skills/tracks/real-time-streaming/TRACK.md) | Kafka/Kinesis/Pulsar, low-latency, stream processing | Standard or Rigorous | Lean |
| [Consumer product](../skills/tracks/consumer-product/TRACK.md) | B2C products: experimentation, growth, analytics, notifications, feeds, viral mechanics | Lean or Standard | Nano |
| [Open source](../skills/tracks/open-source/TRACK.md) | Public libraries with semver, contributor pipeline, CVE disclosure | Standard | Lean |
| [Mobile](../skills/tracks/mobile/TRACK.md) | iOS, Android, React Native, Flutter — native mobile apps | Standard | Lean |
| [Blockchain / Web3](../skills/tracks/blockchain-web3/TRACK.md) | Smart contracts, DeFi, NFTs, crypto custody, key management, upgrade patterns | Standard or Rigorous | Standard |
| [IoT / Embedded](../skills/tracks/iot-embedded/TRACK.md) | Firmware, connected devices, OTA updates, fleet management, edge computing | Lean or Standard | Lean |
| [Gaming](../skills/tracks/gaming/TRACK.md) | Real-time multiplayer, live ops, IAP, latency SLOs, anti-cheat | Lean or Standard | Lean |
| [Defense / Classified](../skills/tracks/defense-classified/TRACK.md) | Classified systems, ITAR/EAR, RMF/ATO, air-gapped deployment | Rigorous | Rigorous |

Zero tracks is a valid state — most projects run without a track. One to N tracks may be active simultaneously.

---

## How to pick a track

### Option A: declare it

```
"Standard mode, Fintech track — implement the payment intent endpoint"
"Lean mode, SaaS B2B track — build the tenant invitation flow"
"Rigorous mode, Healthcare + Regulated tracks — clinical notes service with FedRAMP Moderate"
"Nano mode, Consumer track — add the referral link feature"
```

Multiple tracks compose — say them all.

### Option B: let the orchestrator suggest

The orchestrator reads the PRD and proposes a track based on keywords ("payment", "clinical", "multi-tenant", "FedRAMP"). You confirm before the track activates. Mis-tracking a project wastes more effort than under-tracking — confirmation is required, never auto-activation.

### Activation keywords (high-level)

| Phrase | Suggested track |
|--------|----------------|
| "PCI", "cardholder", "payment intent", "payout", "reconciliation", "KYC/AML" | Fintech |
| "multi-tenant", "tenant isolation", "SSO", "SAML", "RBAC", "SLA credits", "per-seat" | SaaS B2B |
| "multi-user web app", "user accounts", "subscription billing", "Stripe Checkout", "JWT", "OAuth2", "REST API and frontend", "full-stack web app" | Web product |
| "data pipeline", "schema registry", "data contract", "model versioning", "RAG", "feature store" | Data platform / ML ops |
| "HIPAA", "PHI", "clinical notes", "HL7", "FHIR", "BAA" | Healthcare |
| "FedRAMP", "ATO", "SOC 2", "ISO 27001", "CMMC", "StateRAMP" | Regulated / government |
| "Kafka", "Kinesis", "Pulsar", "exactly-once", "watermarks", "backpressure" | Real-time / streaming |
| "A/B test", "experiment", "Amplitude", "Mixpanel", "referral loop", "content feed", "push campaign", "notification inbox", "viral coefficient" | Consumer |
| "open source", "semver", "CONTRIBUTING.md", "CVE disclosure", "SPDX" | Open source |
| "iOS", "Android", "React Native", "Flutter", "TestFlight", "APNS", "FCM" | Mobile |

Full activation lists live in each track's `TRACK.md` and in `docs/skill-triggers.md`.

---

## Mode-track conflict resolution

Tracks and modes are orthogonal but can create apparent conflicts — a track mandates a skill at Nano that the Nano mode excludes, for example.

**The resolution rule:**

1. **Track elevation wins over mode default.** If a track mandates `security-audit-secure-sdlc` at Nano, that skill is mandatory regardless of what Nano mode says by default. Tracks add constraints; they never remove them.
2. **Minimum mode is a floor.** The track's minimum mode (see table above) is the lowest mode permissible when that track is active. Declaring `Nano mode + Healthcare track` should prompt the orchestrator to flag the conflict and ask whether to promote the mode to Lean or to scope the track to a non-PHI surface.
3. **When in doubt, promote.** If a team genuinely cannot complete a track's gate requirements inside the declared mode's time budget, the right answer is mode promotion — not skipping the gate. Log the promotion with a reason.
4. **Multi-track: strictest wins.** When two active tracks conflict on a gate criterion, the harder criterion applies. When two active tracks conflict on a minimum mode, the higher minimum applies.

**Example:** `Nano mode + Fintech track` on a non-PCI internal tool. The Fintech track mandates `security-audit-secure-sdlc` at Nano. That check runs. The PCI checklist applies only if PAN is in scope. The team declares in the PR that no cardholder data flows through this code path — that declaration is the evidence. Nano's 2–4 hour envelope is preserved; the security gate is not skipped.

---

## Session mechanics

### Persistence

Tracks persist in `docs/sdlc-status.md`:

```markdown
## Current state
- Mode: Standard
- Track(s): Fintech, Healthcare
- Pipeline stage: 3 (Build)
- Active feature: payment-intent-v2
```

Once set on a project, every new feature inherits the track(s) without re-declaring. Change or remove tracks explicitly:

```
"This feature is out of scope for Fintech track — declare no-track for just this one"
"Add the Regulated track to this project"
"Drop the Healthcare track — no PHI after the scope change"
```

### Composition rules — multiple tracks together

| Dimension | Rule |
|-----------|------|
| Skill elevation | Union — every elevation from every active track applies |
| Gate modification | Strictest wins — if two tracks modify the same gate, the harder criterion applies |
| Reference injection | Additive — all applicable references load for every triggered skill |

**Worked examples — multi-track composition:**

**Example 1: IoT + Fintech (payment terminal)**
A payment terminal firmware project activates IoT / Embedded + Fintech / Payments.
- Minimum mode: Fintech requires Standard for PCI-scope changes; IoT requires Lean → **Standard wins**
- Skill elevations: union of both tracks — `security-audit-secure-sdlc` is mandatory with *both* device threat model (IoT) and PCI-scope review (Fintech); `disaster-recovery` is mandatory with OTA rollback (IoT) and reconciliation runbook (Fintech)
- Gate modifications: Stage 2 requires OTA rollback design (IoT) AND idempotency + PCI scope identification (Fintech) — both apply
- Reference injection: when `security-audit-secure-sdlc` fires, load both `device-security-guide.md` (IoT) and `pci-dss-checklist.md` (Fintech)

**Example 2: Gaming + Data platform (analytics pipeline)**
A live-service game adds a real-time analytics pipeline. Gaming + Data platform / ML ops.
- Minimum mode: both are Lean → **Lean** (or higher if the team declares it)
- Skill elevations: `observability-sre-practice` is mandatory with session analytics + DAU metrics (Gaming) AND freshness SLOs + quality SLOs (Data platform) — both sets of requirements apply
- Gate modifications: Stage 4 requires load test at target concurrent player count (Gaming) AND data quality tests + backfill parity test (Data platform)
- Reference injection: when `comprehensive-test-strategy` fires, load both `real-time-multiplayer-patterns.md` (Gaming) and `data-quality-framework.md` (Data platform)

**Example 3: Blockchain + Regulated / Government (cleared crypto custody)**
A cleared facility builds a blockchain-based evidence chain for law enforcement. Blockchain / Web3 + Defense / Classified.
- Minimum mode: Blockchain requires Standard; Defense requires Rigorous → **Rigorous wins**
- Skill elevations: `formal-verification` is mandatory (Blockchain requires it for money-movement logic; Defense requires it for cryptographic protocols) — applied once with both domains' requirements
- Gate modifications: Stage 4 requires external smart contract audit (Blockchain) AND DISA STIG scan + government penetration test (Defense) — both apply; neither replaces the other
- The strictest gate criterion applies at every stage: if Blockchain requires testnet deployment and Defense requires air-gapped testing, the team must satisfy both

Example: a B2B healthcare SaaS product runs SaaS B2B + Healthcare. Both tenant isolation tests and HIPAA audit-log evidence are mandatory. `documentation-system-design` at the release gate must produce both SLA documentation (B2B) and audit trail evidence (Healthcare).

### Logging

Track activations go to `docs/skill-log.md`:

```
[2026-05-01] track-activated: fintech-payments | mode: Standard | duration: project
[2026-05-01] track-activated: healthcare-hipaa | mode: Standard | duration: project
[2026-05-05] track-deactivated: healthcare-hipaa | reason: scope change, no PHI involved
```

Skill firings under a track append the track context on the same line:

```
[2026-05-05] security-audit-secure-sdlc | outcome: OK | next: code-implementer | note: PCI-scope review complete | track: fintech-payments
```

---

## Track vs new skill — when each is right

Some domain patterns deserve a full skill (formal distinct process). Most deserve a track (lens over existing skills).

**Decision rule:**
- **Distinct, repeatable process that is not already a skill** → build a skill, or extend an existing skill with a new reference file.
- **Curation of existing skills with different defaults, mandatory gates, and checklists** → build a track.

PCI DSS audit, HIPAA compliance workflow, FedRAMP evidence collection all look like skill candidates initially. They are not. They are compositions of `security-audit-secure-sdlc` + `data-governance-privacy` + `documentation-system-design` + domain-specific checklists. A track is the right shape.

---

## TRACK.md — the contract

Every track package has a `TRACK.md` at its root with 8 sections in order, parallel to the 8-section `SKILL.md` contract:

1. **YAML frontmatter** — `name:` and `description:` (activation phrases and domain fingerprint)
2. **Purpose** — one paragraph; what domain this covers and why it needs specialization
3. **When to activate** — specific signals and phrases
4. **When NOT to activate** — adjacent domains that belong to a different track (hard boundaries)
5. **Skill elevations** — table of skill × mode showing where Advisory becomes Mandatory
6. **Gate modifications** — table of stage × new criterion / required evidence
7. **Reference injection map** — when skill X fires during this track, also load reference Y
8. **Reference files** — list of `references/*.md` with a one-line description each

Validate with `scripts/track_validator.py`. All 8 sections are required; none are optional.

Template: `skills/tracks/TRACK-TEMPLATE.md`.

---

## Tracks vs workflow paths

The orchestrator also supports three workflow paths: **Hotfix** (bypass Stages 1–2), **Spike** (timeboxed exploration), **Brownfield** (codebase takeover assessment). These were historically called "special tracks" in earlier docs.

**Workflow paths ≠ tracks.** A workflow path modifies *which stages run*. A track modifies *how a stage runs inside a domain*. Workflow paths are orthogonal to both mode and track — you can be in `Lean + Fintech + Hotfix` (a payments hotfix to a PCI-scope endpoint; the hotfix path still runs but fintech gate modifications still apply).

See `skills/workflow/CLAUDE.md` for the three workflow paths in detail.

---

## Adding a new track

When a domain keeps surfacing in work but no existing track covers it:

1. Check the decision rule — is this really a track, or a new skill?
2. Copy `skills/tracks/TRACK-TEMPLATE.md` to `skills/tracks/<domain>/TRACK.md`
3. Fill all 8 sections. Skill elevations must name real skills from the library.
4. Write the reference files under `references/`. Keep `TRACK.md` lean — references do the heavy lifting.
5. Run `scripts/track_validator.py` to verify the contract.
6. Run `scripts/check_track_elevations.py` to verify every skill elevation maps to a real skill.
7. Update this doc's track list, `docs/quickstart.md`, `docs/skill-triggers.md`, `skills/INDEX.md`, `skills/tracks/CLAUDE.md`, and `README.md`.

Candidate future tracks as demand surfaces: AR/VR, Automotive, Desktop apps.

Note: the Web product track was added as track 10. It covers the common shape of multi-user web products (auth, RBAC, API + frontend, DB concurrency, subscription billing) that falls between "no track" and SaaS B2B. SaaS B2B requires enterprise SSO, SAML, and contractual SLAs as preconditions; Web product does not.

---

## Success criteria

A track is successful if:

1. Teams in that domain reach for it and find real value in its elevated skills and references.
2. Gate modifications prevent at least one real class of incident per quarter.
3. Reference material is loaded on average 2+ times per project in that track.
4. Teams in different domains coexist in the same library without skill-set bloat.

A track has failed if:

1. Nobody declares it.
2. Elevations are ignored in practice.
3. Gate modifications cause false friction.
4. Reference material is stale and rarely consulted.

Re-evaluate quarterly. A stale track is worse than no track — retire it or rewrite it.
