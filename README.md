# sdlc-skills-library — SDLC Skill Library for Claude Code

A library of 42 production-ready Claude Code skills plus 14 domain tracks covering every phase of the software development lifecycle. Built for small, high-velocity engineering teams (3–5 senior engineers).

## What this is

sdlc-skills-library augments Claude Code with structured guidance, decision-making frameworks, templates, and automation scripts for every SDLC phase — from stakeholder alignment through architecture, implementation, quality, and sustained operations.

Skills trigger automatically when your request matches their purpose, or can be invoked explicitly. The orchestrator manages the full pipeline, selects an operating mode based on your context, and activates domain **tracks** (Fintech, Healthcare, SaaS B2B, etc.) that overlay mandatory skills and tighter gates where the domain demands them.

## Structure

```
skills/
├── workflow/          # 1 skill  — master SDLC orchestrator (with modes + tracks)
├── phase1/            # 10 skills — foundation & governance
├── phase2/            # 20 skills — delivery quality
├── phase3/            # 9 skills  — sustained operations
├── phase4/            # 1 skill   — advanced assurance
└── tracks/            # 14 tracks — domain overlays (Fintech, SaaS B2B, Web product, Healthcare, Blockchain, IoT, Gaming, Defense, ...)
docs/
├── quickstart.md      — decision tree: where to start
├── modes.md           — full guide to operating modes (Nano/Lean/Standard/Rigorous)
├── tracks.md          — full guide to domain tracks
├── skill-triggers.md  — natural language phrases that activate each skill / track
├── skill-log.md       — append-only execution audit trail (created on first run)
└── sdlc-status.md     — current pipeline stage and status (created on first run)
```

## Operating modes

Every pipeline run operates in one of four modes. Declare it at the start, or let the orchestrator ask three questions and derive it.

| Mode | Context | Active skills | Gates | Est. time |
|------|---------|--------------|-------|-----------|
| **Nano** | Solo/pair, internal tool, hours | 4–5 | Advisory + security hard stops | 2–4 hrs |
| **Lean** | Small team, standard feature | 8–10 | Standard | 1–2 days |
| **Standard** | Customer-facing, API contracts | 16–18 | Hard | 3–5 days |
| **Rigorous** | Payments, auth, regulated, critical | All relevant | Hard + sign-off | 1–2 weeks |

Plus three workflow paths: **Hotfix** (bypass planning, fix and ship), **Spike** (time-boxed exploration, 2–4 hrs), **Brownfield** (codebase takeover assessment).

### Security guardrails — ring-fenced across all modes

Speed is not an excuse for shipping insecure or broken code. Every mode has non-negotiable security controls that the orchestrator enforces unconditionally.

**Nano — hard stops (block even in advisory mode):**
- Secrets scan: always, findings block merge
- SAST: required when the change touches auth, session handling, or permissions — Critical/High block merge
- SCA (dependency scan): required when any new library is added — Critical CVEs block merge
- Inline security checklist (4 items in every implementation task): input validation, auth check, no secrets in code, injection surface — phase gate does not pass until all four are answered
- Peer review required (not self-review) for any change touching auth, authorisation, DB schema, or a shared interface
- **Migration tripwire:** `ALTER TABLE`, `DROP TABLE`, or `CREATE INDEX` in Nano auto-promotes to Lean — no exceptions

**Lean — standard hard gates:**
- All three security scans at Stage 4: SAST + SCA (dependency scan) + secrets scan — all are hard gates, not advisory
- Design-time security checkpoint before Stage 3: 5 required questions in DESIGN.md (data classification, auth model, auth failure behaviour, injection surfaces, replay/idempotency) — "TBD" is not an accepted answer
- Signal-based conditional skill activation — no reliance on team memory:
  - New route / endpoint / gRPC method / event topic → `specification-driven-development`
  - Any HTML / JSX / template / UI component modified → `accessibility` spot-check
  - Any LLM API call / prompt template / RAG component → `llm-app-development`
  - Any feature flag introduced → `feature-flag-lifecycle`
  - Any schema change (`ALTER TABLE`, `DROP`, `CREATE INDEX`) → `database-migration` (mandatory)

Full mode guide: `docs/modes.md`

## Domain tracks

Tracks are a second, orthogonal dimension to mode. Where **mode** answers *how much rigor*, **track** answers *what domain*. A session is always in one mode and may be in zero or more tracks. Tracks elevate mandatory skills, tighten gate criteria, and inject domain-specific reference material when a skill fires.

| Track | Covers | Typical mode | Min mode |
|-------|--------|--------------|----------|
| **Fintech / Payments** | Card data, money movement, PCI scope, regulated financial services | Standard or Rigorous | Lean |
| **SaaS B2B** | Multi-tenant products with SSO, RBAC, contractual SLAs, tenant-scoped caching | Standard | Lean |
| **Web product** | Multi-user web apps: auth, RBAC, API + frontend, DB concurrency, subscription billing | Lean or Standard | Lean |
| **Data platform / ML ops** | Data pipelines, schema registries, ML/LLM production, compute cost governance | Standard | Lean |
| **Healthcare / HIPAA** | PHI handling, HIPAA §164.308(a)(7) DR, HL7/FHIR, clinical data | Rigorous | Lean |
| **Regulated / government** | FedRAMP, SOC 2, ISO 27001, CMMC, StateRAMP, DR testing as a control | Rigorous | Standard |
| **Real-time / streaming** | Kafka/Kinesis/Pulsar, low-latency, exactly-once, caching for state stores | Standard or Rigorous | Lean |
| **Consumer product** | B2C products: experimentation, feed caching, notifications, viral mechanics, consumer-scale performance | Lean or Standard | Nano |
| **Open source** | Public libraries with semver, CVE disclosure, contributor pipeline and onboarding | Standard | Lean |
| **Mobile** | iOS, Android, React Native, Flutter | Standard | Lean |
| **Blockchain / Web3** | Smart contracts, DeFi, NFTs, crypto custody, key management, on-chain/off-chain patterns | Standard or Rigorous | Standard |
| **IoT / Embedded** | Firmware, connected devices, OTA update safety, fleet management, edge computing | Lean or Standard | Lean |
| **Gaming** | Real-time multiplayer, live ops, IAP flows, latency SLOs, anti-cheat, staged player rollout | Lean or Standard | Lean |
| **Defense / Classified** | Classified systems, ITAR/EAR export controls, RMF/ATO authorization, air-gapped deployment | Rigorous | Rigorous |

Zero tracks is a valid state — most projects run with zero. Multi-domain projects run two or more; they compose additively (skill elevation = union, gate modifications = strictest wins, reference injection = all apply).

### Declaring a track

```
"Standard mode, Fintech track — implement the payment intent endpoint"
"Lean mode, SaaS B2B track — build the tenant invitation flow"
"Standard mode, Web product track — build the REST API with multi-user isolation and Stripe billing"
"Lean mode, Web product track — add JWT auth with refresh token rotation and RBAC"
"Rigorous mode, Healthcare + Regulated tracks — clinical notes with FedRAMP Moderate"
"Standard mode, Real-time / Streaming track — build the Kafka-based device telemetry pipeline"
"Lean mode, Consumer product track — run an A/B test on the signup onboarding flow"
"Standard mode, Open source track — release v2.0 with deprecation notices and migration guide"
"Standard mode, Mobile track — ship offline-first sync for iOS and Android"
"Standard mode, Data platform track — design the feature store schema and ingestion pipeline"
```

Or let the orchestrator suggest one from PRD keywords. It scans your PRD for signals and asks for confirmation before activating:

```
User PRD mentions: "multi-tenant", "PHI", "FedRAMP Moderate", "HIPAA audit log"

Orchestrator: I see signals for three tracks:
  1. Healthcare / HIPAA (PHI, HIPAA audit log)
  2. Regulated / Government (FedRAMP Moderate)
  3. SaaS B2B (multi-tenant)

Activate all three? → User confirms → Tracks written to sdlc-status.md
```

Or run `track_advisor.py` offline before starting the session:

```bash
$ python scripts/track_advisor.py --text "multi-tenant SaaS with HIPAA data sharing and FedRAMP Moderate controls"
Suggested tracks:
  healthcare-hipaa      score: 3  — PHI, HIPAA audit log, de-identification, BAA workflow
  regulated-government  score: 2  — FedRAMP evidence, SOC 2 mapping, change management
  saas-b2b              score: 1  — multi-tenancy, SSO/SAML, RBAC, SLAs

Suggested declaration:
  "Rigorous mode, Healthcare + Regulated + SaaS B2B tracks — <describe the feature>"
```

See `docs/tracks.md` for the full guide and `skills/tracks/` for every track's TRACK.md and reference material.

### Declaring a mode

```
"Nano mode — add CSV export to the admin panel"
"Lean mode — build device group management"
"Standard mode — build the provisioning API, the mobile team consumes it"
"Rigorous mode — implement payment intent and charge flow"
"Hotfix — orders are failing in production right now"
"Spike — should we use Kafka or NATS for telemetry?"
"Brownfield — I just inherited this codebase, help me understand what I have"
```

Or let the orchestrator derive the mode:

```
User: "Start a new feature — real-time device alerts"

Orchestrator: Three quick questions:
1. Who uses this if it breaks? → paying customers
2. Does another system depend on this API? → yes, the mobile app
3. Easy to roll back? → yes

→ Mode: Standard (external users + API contract = two elevations from Nano)
→ Running: prd-creator → requirements-tracer → specification-driven-development → ...
```

See `docs/modes.md` for the full mode guide including worked examples and the complete gate specifications.

### Mode promotion mid-pipeline

Start in Lean, discover you need more rigor? The orchestrator handles it:

```
"Promote to Standard — we just found out billing depends on this endpoint"
```

→ Logs a BLOCKED entry, runs the skipped Phase 1 skills, continues from current stage.

## Trigger words

Skills fire automatically when you use their natural language triggers. A few examples:

| Say this... | Fires this skill |
|-------------|-----------------|
| "start a new feature" / "build this from scratch" | `sdlc-orchestrator` |
| "write a PRD" / "define requirements" | `prd-creator` |
| "design the system" / "create DESIGN.md" | `design-doc-generator` |
| "write the OpenAPI spec" / "schema-first" / "GraphQL schema" | `specification-driven-development` |
| "review this code" / "PR is ready for review" | `code-review-quality-gates` |
| "write tests" / "test strategy" / "eval this LLM feature" | `comprehensive-test-strategy` |
| "ready to merge" / "create the PR" | `pr-merge-orchestrator` |
| "production is down" / "hotfix" | `incident-postmortem` → hotfix path |
| "we're going to production tomorrow" / "release checklist" | `release-readiness` |
| "migration failed" / "safe to run this migration?" | `database-migration` |
| "DORA metrics" / "how are we delivering?" | `delivery-metrics-dora` |
| "technical debt" / "velocity is degrading" | `technical-debt-tracker` |
| "this feature flag is stale" / "roll out gradually" | `feature-flag-lifecycle` |
| "project is done" / "hand over to the client" | `project-closeout` |
| "run chaos tests" / "game day" | `chaos-engineering` |
| "TLA+" / "prove this protocol is correct" | `formal-verification` |

Full trigger list: `docs/skill-triggers.md`

## Skills

### Workflow
| Skill | Purpose |
|-------|---------|
| sdlc-orchestrator | Sequences full pipeline with mode selection: PRD → design → implementation → testing → release |

### Phase 1 — Foundation & Governance
| Skill | Purpose |
|-------|---------|
| prd-creator | Interactive PRD creation and validation |
| requirements-tracer | BDD decomposition, traceability matrices, orphan detection |
| design-doc-generator | Synthesizes PRD + requirements + specs into DESIGN.md; includes required 5-question security checkpoint (Lean and above) before Stage 3 |
| specification-driven-development | OpenAPI, Protobuf, AsyncAPI, GraphQL — spec-first before implementation |
| architecture-review-governance | Review process, NFRs, anti-patterns, trade-off frameworks |
| architecture-decision-records | ADR authoring, indexing, versioning |
| technical-risk-management | P×I risk matrix, risk register, kill criteria |
| security-audit-secure-sdlc | STRIDE, supply chain (SBOM/Sigstore), CI/CD security, AI threats |
| stakeholder-sync | Async-first stakeholder comms, decision logging, lean escalation |
| data-governance-privacy | GDPR/CCPA, PIAs, data classification, retention, EU AI Act data transparency |

### Phase 2 — Delivery Quality
| Skill | Purpose |
|-------|---------|
| code-implementer | Phase-by-phase implementation from DESIGN.md; inline security hard stops (input validation, auth, no secrets, injection) block every phase gate |
| code-review-quality-gates | PR checklists, self-review eligibility rules by change type, SCA in CI gates, SLA table |
| pr-merge-orchestrator | Pre-merge gate, PR description generation, release tagging |
| comprehensive-test-strategy | Test pyramid: unit / integration / contract / acceptance / performance / LLM evals |
| executable-acceptance-verification | BDD scenarios, Gherkin feature files, formal sign-off |
| api-contract-enforcer | Pact contract testing, schema registry, drift detection |
| performance-reliability-engineering | NFR definition, load testing with k6, circuit breakers, capacity planning |
| release-readiness | Release checklist, go/no-go process, deployment plan |
| database-migration | Migration classification, expand-contract pattern, lock-free DDL, CI validation |
| devops-pipeline-governance | Pipeline design, deployment strategies, IaC governance |
| observability-sre-practice | SLOs, error budgets, alerting standards |
| documentation-system-design | C4 diagrams, runbooks, operational handover |
| ai-assisted-engineering | Trust tiers, AI code security, prompt patterns, MCP integrations |
| llm-app-development | Eval-driven development, prompt versioning, RAG design, agent tool design, production LLM monitoring |
| feature-flag-lifecycle | Flag types, create/roll out/remove lifecycle, flag debt detection |
| accessibility | WCAG 2.2 AA compliance, dev checklist, axe-core CI integration, EU Accessibility Act and ADA coverage |
| architecture-fitness | Automated CI enforcement of import boundaries, dependency budgets, dead code detection, coverage floors |
| distributed-systems-patterns | Sagas, event sourcing, CQRS, outbox pattern, idempotency keys |
| disaster-recovery | RTO/RPO tiers, 3-2-1 backup, multi-region failover, DR drill runbooks |
| caching-strategy | Cache patterns, invalidation strategies, CDN config, stampede prevention |

### Phase 3 — Sustained Operations
| Skill | Purpose |
|-------|---------|
| technical-debt-tracker | Debt taxonomy, prioritization, budget allocation |
| delivery-metrics-dora | DORA measurement, cold-start guidance (month 0–3), reporting |
| dependency-health-management | CVE triage, EOL planning, SBOM, framework upgrades |
| incident-postmortem | Blameless RCA, 5 Whys, action item tracking |
| team-coaching-engineering-culture | Team health snapshot, growth plans, engineering norms, quarterly retro |
| chaos-engineering | Hypothesis-driven experiments, fault injection, game days |
| project-closeout | Documentation audit, deliverables sign-off, knowledge transfer, DORA final report |
| cloud-cost-governance | Cost attribution tagging, per-feature cost estimates, monthly optimization audit, anomaly detection |
| developer-onboarding | Onboarding checklists, local dev setup, engineering norms codification |
| sustainability-carbon-audit | Carbon baseline measurement, green software patterns, carbon audit report |

### Phase 4 — Advanced Assurance
| Skill | Purpose |
|-------|---------|
| formal-verification | TLA+ protocol specification, TLC model checking, distributed protocol correctness |

### Tracks (domain overlays)
| Track | Directory | Covers |
|-------|-----------|--------|
| fintech-payments | `skills/tracks/fintech-payments/` | PCI scope, money movement, idempotency, reconciliation, fraud signals |
| saas-b2b | `skills/tracks/saas-b2b/` | Multi-tenancy, SSO/SAML, RBAC, SLAs and metering, onboarding |
| web-product | `skills/tracks/web-product/` | Auth (JWT/sessions/MFA), lightweight tenant isolation, simple RBAC, API + frontend contract, DB concurrency, subscription billing, rate limiting, accessibility |
| data-platform-mlops | `skills/tracks/data-platform-mlops/` | Data contracts, schema registry, data quality, model versioning, feature store |
| healthcare-hipaa | `skills/tracks/healthcare-hipaa/` | PHI classification, HIPAA audit log, de-identification, BAA workflow |
| regulated-government | `skills/tracks/regulated-government/` | FedRAMP evidence, SOC 2 mapping, change management, VDP |
| real-time-streaming | `skills/tracks/real-time-streaming/` | Platform selection, exactly-once, backpressure, windowing |
| consumer-product | `skills/tracks/consumer-product/` | A/B design, experiment statistics, event taxonomy, feed caching, notification pipeline, consumer-scale performance |
| open-source | `skills/tracks/open-source/` | Semver, deprecation, security disclosure, contributor experience, license |
| mobile | `skills/tracks/mobile/` | App store cycles, version management, offline-first, push, performance |
| blockchain-web3 | `skills/tracks/blockchain-web3/` | Smart contract audit, key management, upgrade patterns, oracle security, on-chain/off-chain |
| iot-embedded | `skills/tracks/iot-embedded/` | Device security, OTA update patterns, fleet rollout, edge computing, offline-first for devices |
| gaming | `skills/tracks/gaming/` | Real-time multiplayer patterns, IAP flows, live ops, latency SLOs, anti-cheat |
| defense-classified | `skills/tracks/defense-classified/` | ITAR/EAR controls, RMF/ATO authorization, air-gapped deployment, classified CI/CD |

## Installation

```bash
# Global install — all 41 skills available in every Claude Code session
./install-skills.sh

# Project-specific install
./install-skills.sh /path/to/your/project

# Copy mode (standalone snapshot instead of symlinks)
./install-skills.sh --copy
./install-skills.sh /path/to/your/project --copy

# Preview without writing anything
./install-skills.sh --dry-run

# Overwrite existing installations (otherwise, existing directories are skipped)
./install-skills.sh --force

# Show full help and exit
./install-skills.sh --help
```

### Options

| Flag | Effect |
|------|--------|
| `-h`, `--help` | Print usage, examples, and post-install guidance, then exit |
| `--copy` | Copy files instead of symlinking. Standalone snapshot; NOT updated when the repo changes. Best for consumers. |
| `--dry-run` | Show what would be installed without writing anything |
| `--force` | Overwrite existing skill directories. Default is to skip them. |

### Install modes

- **Symlink (default)** — each installed skill is a symlink back into this repo. Edits to the library are reflected everywhere immediately. Symlinks break if the source repo moves. Best when you are actively developing skills.
- **Copy (`--copy`)** — each installed skill is a full copy. No updates unless you re-run the installer. Portable across machines — can be committed into a project.

The installer walks all 41 skill directories dynamically and installs each one into `~/.claude/skills/` (global) or `.claude/skills/` (project-local). New skills added to the library are picked up automatically — no hardcoded list to maintain.

### After installation

- **Global install** — skills are active in every Claude Code session. Verify: `ls ~/.claude/skills/`
- **Project install with `--copy`** — commit `.claude/skills/` (portable snapshot, survives across machines)
- **Project install without `--copy`** — add `.claude/skills/` to `.gitignore` (symlinks are machine-specific)

Unknown options are rejected with a non-zero exit code. Target project paths are validated before installation.

## Usage

### Starting a feature

```
"Start a new feature — device telemetry alerting"
→ sdlc-orchestrator activates, asks 3 questions, sets mode, runs pipeline
```

### Standalone skill invocation

```
"Review this PR for security issues"
→ code-review-quality-gates + security-audit-secure-sdlc activate

"We had a P1 incident last night — run the postmortem"
→ incident-postmortem activates

"Is this database migration safe to run?"
→ database-migration activates
```

### Explicit invocation

```
/skill sdlc-orchestrator
/skill prd-creator
/skill database-migration
```

### Where to start

- **No idea where to begin?** → `docs/quickstart.md` — decision tree
- **Need to pick a mode?** → `docs/modes.md` — full mode guide with worked examples
- **Need to pick a track?** → `docs/tracks.md` — full track guide; or run `python scripts/track_advisor.py`
- **Looking for trigger phrases?** → `docs/skill-triggers.md` — natural language for all 42 skills and 14 tracks
- **Need the full skill reference?** → `skills/MASTER-GUIDE.md`

## Automation Scripts

Several skills include Python utilities for offline/CI use:

| Script | What it does |
|--------|-------------|
| `phase1/stakeholder-sync/scripts/generate_charter.py` | Generate project charter from CLI |
| `phase1/stakeholder-sync/scripts/generate_raci.py` | Generate RACI matrix from JSON |
| `phase1/architecture-review-governance/scripts/review_report.py` | Generate architecture review report |
| `phase1/requirements-tracer/scripts/check_orphans.py` | Detect orphaned requirements, code, or tests |
| `phase1/technical-risk-management/scripts/risk_report.py` | Generate risk register report |
| `phase1/specification-driven-development/scripts/validate_openapi.py` | Validate OpenAPI specs |
| `phase1/specification-driven-development/scripts/diff_contracts.py` | Diff API versions (breaking vs non-breaking) |
| `phase2/architecture-fitness/scripts/check_imports.py` | Enforce import boundary rules and detect circular imports |
| `phase2/architecture-fitness/scripts/dep_budget.py` | Check third-party dependency count against configured budget |
| `phase2/architecture-fitness/scripts/dead_code.py` | Cross-reference coverage + git log to find abandoned modules |
| `phase2/database-migration/scripts/migration_risk.py` | Assess migration safety (lock risk, idempotency, index CONCURRENTLY) |
| `phase3/chaos-engineering/scripts/chaos_schedule.py` | Generate quarterly chaos experiment schedule from service list |
| `scripts/mode_advisor.py` | Interactive 3-question mode derivation CLI |
| `scripts/skill_health.py` | Validate all SKILL.md files have the 8 required sections |
| `scripts/skill_usage.py` | Parse skill-log.md and report usage frequency and BLOCKED rates |
| `scripts/health_report.py` | Generate unified project health report (delivery, quality, security, docs) |
| `scripts/track_advisor.py` | Suggest tracks from PRD or description keywords (`--text`, `--file`, `--json`) |
| `scripts/track_validator.py` | Validate all TRACK.md files have the 8 required sections |
| `scripts/check_track_elevations.py` | Verify every skill elevation in a TRACK.md maps to a real skill |

## Requirements

- [Claude Code](https://claude.ai/code) — Anthropic's official CLI
- Python 3.x — for automation scripts (optional)
- Bash — for the install script

No build tools or package managers required. The library is plain Markdown and lightweight Python scripts.

## Author

**Thanassis Zografos** — S3Nex Ltd

- Email: <tzografos@gmail.com> · <tz@s3nex.com>
- LinkedIn: [linkedin.com/in/sonaht](https://www.linkedin.com/in/sonaht/)

Built for engineering teams who want to move fast without leaving a mess behind. If this library helps your team ship better software, the author would love to hear about it.

## License

MIT — see [LICENSE](LICENSE).

Use it anywhere, for anything. Modify it, redistribute it, build a product around it, charge money for it. The only thing asked is that you keep the copyright notice and license text in any substantial portion you ship. That's it.
