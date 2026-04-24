# Skills index

41 production-ready skill packages plus 10 domain tracks for a small, high-velocity engineering team (3–5 senior engineers). Each skill is a structured knowledge package with a `SKILL.md` (loaded on trigger), `references/` (loaded on demand), and `scripts/` where tooling exists. Each track is a curated overlay: TRACK.md plus domain `references/`. Philosophy: move fast, leave a trail.

---

## Workflow — End-to-end SDLC pipeline (1 skill)

| Skill | Directory | What it covers |
|-------|-----------|---------------|
| SDLC orchestrator | `workflow/sdlc-orchestrator/` | Master pipeline orchestrator: PRD → requirements → specs → design → implementation → testing → PR/merge → docs |

---

## Phase 1 — Foundation and governance (10 skills)

| Skill | Directory | What it covers |
|-------|-----------|---------------|
| PRD creator | `phase1/prd-creator/` | Interactive PRD creation, raw-input structuring, PRD validation, quality gate, pipeline entry point |
| Requirements tracer | `phase1/requirements-tracer/` | BDD decomposition, traceability matrix, orphan detection, scope impact |
| Design document generator | `phase1/design-doc-generator/` | Synthesises PRD + requirements + specs + ADRs into an implementation-ready DESIGN.md |
| Specification-driven development | `phase1/specification-driven-development/` | OpenAPI, Protobuf, AsyncAPI (incl. event-driven/Kafka schemas), GraphQL (schema-first, deprecation, DataLoader, federation), contract review, freeze process |
| Architecture review governance | `phase1/architecture-review-governance/` | Review process, checklists, anti-patterns, NFR templates, trade-off frameworks |
| Architecture decision records | `phase1/architecture-decision-records/` | ADR creation, indexing, good/bad examples, numbering |
| Technical risk management | `phase1/technical-risk-management/` | P×I matrix, risk register, categories, kill criteria |
| Security audit and secure SDLC | `phase1/security-audit-secure-sdlc/` | STRIDE, secure coding, supply chain (SBOM/Sigstore), CI/CD security, AI-specific threats, NIST SSDF |
| Stakeholder sync | `phase1/stakeholder-sync/` | Async-first stakeholder comms, decision logging, scope change handling, lean escalation |
| Data governance and privacy | `phase1/data-governance-privacy/` | Data classification, PIAs, GDPR/CCPA workflows, retention policy, EU AI Act data transparency |

---

## Phase 2 — Delivery quality (20 skills)

| Skill | Directory | What it covers |
|-------|-----------|---------------|
| Code implementer | `phase2/code-implementer/` | Phase-by-phase implementation from DESIGN.md, inline security gates, test-alongside approach |
| Code review and quality gates | `phase2/code-review-quality-gates/` | PR checklists, comment labels, CI gates, review SLA table |
| Comprehensive test strategy | `phase2/comprehensive-test-strategy/` | Test pyramid, unit/integration/contract/acceptance/performance/LLM feature testing |
| PR and merge orchestrator | `phase2/pr-merge-orchestrator/` | Pre-merge gate, PR description generation, review coordination, merge process, release tagging |
| DevOps pipeline governance | `phase2/devops-pipeline-governance/` | Pipeline design, deployment strategies, IaC, rollback, pipeline security |
| Release readiness | `phase2/release-readiness/` | Release checklist, go/no-go process, deployment plan, post-release verification |
| Database migration | `phase2/database-migration/` | Migration classification, expand-contract pattern, lock-free DDL, CI validation, production deployment sequence |
| Documentation system design | `phase2/documentation-system-design/` | C4 diagrams, runbooks, API guides, operational handover, quality checklist |
| Observability and SRE practice | `phase2/observability-sre-practice/` | Metrics, logs, traces, SLOs, error budgets, alerting |
| API contract enforcer | `phase2/api-contract-enforcer/` | Pact contract tests, schema registry, runtime validation, drift detection |
| Executable acceptance verification | `phase2/executable-acceptance-verification/` | BDD scenarios, feature files, step definitions, sign-off process |
| Performance and reliability engineering | `phase2/performance-reliability-engineering/` | NFR definition, load tests, k6, circuit breakers, retries, capacity planning |
| AI-assisted engineering | `phase2/ai-assisted-engineering/` | Trust tiers, AI code security review, prompt engineering, MCP integrations, Claude across the SDLC |
| LLM application development | `phase2/llm-app-development/` | Eval-driven development, prompt versioning, pipeline pattern selection (single-shot/chain/router/orchestrator-worker), RAG design, agent tool design, production LLM monitoring |
| Feature flag lifecycle | `phase2/feature-flag-lifecycle/` | Flag types, create/roll out/remove lifecycle, debt detection, flag registry |
| Accessibility | `phase2/accessibility/` | WCAG 2.2 AA compliance, dev checklist, axe-core CI integration, EU Accessibility Act and ADA coverage |
| Architecture fitness functions | `phase2/architecture-fitness/` | Automated CI enforcement of import boundaries, dependency budgets, dead code detection, coverage floors |
| Distributed systems patterns | `phase2/distributed-systems-patterns/` | Sagas (orchestration/choreography), event sourcing, CQRS, transactional outbox, idempotency keys, consistency models |
| Disaster recovery | `phase2/disaster-recovery/` | RTO/RPO tiers, 3-2-1 backup, multi-region failover patterns, DR drill runbooks, restore verification |
| Caching strategy | `phase2/caching-strategy/` | Cache layer design, cache-aside/read-through patterns, invalidation, CDN config, stampede prevention |

---

## Phase 3 — Sustained operations (9 skills)

| Skill | Directory | What it covers |
|-------|-----------|---------------|
| Technical debt tracker | `phase3/technical-debt-tracker/` | Debt taxonomy, item format, prioritisation, budget allocation |
| Delivery metrics and DORA | `phase3/delivery-metrics-dora/` | DF, LT, CFR, MTTR measurement, cold-start guidance (month 0–3), reporting |
| Dependency health management | `phase3/dependency-health-management/` | CVE triage, EOL planning, SBOM, update policy, framework upgrades |
| Incident post-mortem | `phase3/incident-postmortem/` | Blameless RCA, 5 Whys, timeline, action items |
| Team coaching and engineering culture | `phase3/team-coaching-engineering-culture/` | Team health snapshot, growth plans, engineering norms, quarterly retro |
| Chaos engineering | `phase3/chaos-engineering/` | Hypothesis-driven chaos experiments, fault injection in CI, game days, steady-state discipline |
| Project closeout | `phase3/project-closeout/` | Documentation audit, deliverables sign-off, knowledge transfer, operational handover, DORA final report, lessons learned |
| Cloud cost governance | `phase3/cloud-cost-governance/` | Cost attribution (tagging), per-feature estimation, monthly optimization audit, anomaly detection and response |
| Developer onboarding | `phase3/developer-onboarding/` | Day-1/week-1/month-1 checklists, local dev setup, engineering norms codification, onboarding retros |

---

## Phase 4 — Advanced assurance (1 skill)

| Skill | Directory | What it covers |
|-------|-----------|---------------|
| Formal verification | `phase4/formal-verification/` | TLA+ protocol specification, TLC model checking, distributed protocol correctness proofs |

---

## Tracks — domain overlays (10 tracks)

Tracks are not skills. They are curated overlays that elevate mandatory skills, tighten gate criteria, and inject domain reference material. Zero tracks is a valid state. Full guide: `docs/tracks.md`. Template: `skills/tracks/TRACK-TEMPLATE.md`.

| Track | Directory | What it covers |
|-------|-----------|---------------|
| Fintech / Payments | `tracks/fintech-payments/` | PCI scope, idempotency patterns for payments, reconciliation, regulatory reporting, fraud signals |
| SaaS B2B | `tracks/saas-b2b/` | Multi-tenancy patterns, SSO/SAML/SCIM, RBAC, SLAs and metering, enterprise onboarding |
| Web product | `tracks/web-product/` | Auth (JWT/OAuth2/MFA), lightweight tenant isolation, simple RBAC, API + frontend contract, DB concurrency, subscription billing, rate limiting, accessibility gate |
| Data platform / ML ops | `tracks/data-platform-mlops/` | Data contracts, schema registry, data quality, model versioning, feature stores |
| Healthcare / HIPAA | `tracks/healthcare-hipaa/` | PHI classification, HIPAA audit logs, de-identification, BAA workflow |
| Regulated / government | `tracks/regulated-government/` | FedRAMP evidence, SOC 2 mapping, change management, VDP |
| Real-time / streaming | `tracks/real-time-streaming/` | Platform selection, exactly-once semantics, backpressure, windowing and watermarks |
| Consumer product | `tracks/consumer-product/` | A/B design, experiment statistics, event taxonomy, analytics setup |
| Open source | `tracks/open-source/` | Semver discipline, deprecation policy, security disclosure, contributor experience, license compliance |
| Mobile | `tracks/mobile/` | App store cycles, version management, offline-first, push notifications, performance |

---

## Reference scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `generate_charter.py` | `phase1/stakeholder-sync/scripts/` | Generate project charter from CLI args |
| `generate_raci.py` | `phase1/stakeholder-sync/scripts/` | Generate and validate RACI matrix from JSON input |
| `review_report.py` | `phase1/architecture-review-governance/scripts/` | Produce architecture review report from JSON findings |
| `check_orphans.py` | `phase1/requirements-tracer/scripts/` | Detect orphaned requirements, modules, and tests |
| `risk_report.py` | `phase1/technical-risk-management/scripts/` | Generate risk register report from JSON or CSV |
| `validate_openapi.py` | `phase1/specification-driven-development/scripts/` | Validate OpenAPI spec for completeness and correctness |
| `diff_contracts.py` | `phase1/specification-driven-development/scripts/` | Compare two OpenAPI versions; classify breaking/non-breaking changes |
| `check_imports.py` | `phase2/architecture-fitness/scripts/` | Enforce import boundary rules and detect circular imports |
| `dep_budget.py` | `phase2/architecture-fitness/scripts/` | Check third-party dependency count against configured budget |
| `dead_code.py` | `phase2/architecture-fitness/scripts/` | Cross-reference coverage + git log to find abandoned modules |
| `migration_risk.py` | `phase2/database-migration/scripts/` | Assess migration safety (lock risk, idempotency, index CONCURRENTLY) |
| `chaos_schedule.py` | `phase3/chaos-engineering/scripts/` | Generate quarterly chaos experiment schedule from service list |
| `mode_advisor.py` | `scripts/` | Interactive 3-question mode derivation CLI |
| `skill_health.py` | `scripts/` | Validate all SKILL.md files have the 8 required sections |
| `skill_usage.py` | `scripts/` | Parse skill-log.md and report usage frequency and BLOCKED rates |
| `health_report.py` | `scripts/` | Generate unified project health report (delivery, quality, security, docs) |
| `track_advisor.py` | `scripts/` | Suggest domain tracks from PRD or description keywords |
| `track_validator.py` | `scripts/` | Validate all TRACK.md files have the 8 required sections |
| `check_track_elevations.py` | `scripts/` | Verify every skill elevation in a TRACK.md maps to a real skill |
