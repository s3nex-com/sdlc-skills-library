# skills/phase2/ — Delivery quality

Phase 2 skills govern day-to-day implementation and run continuously throughout development. They apply to every sprint, every PR, every deployment. The goal is to make quality fast — not to add process overhead that slows delivery.

**Key tension to manage:** velocity vs quality. A gate check should take minutes, not hours. If a phase 2 skill is adding significant overhead, it is being applied at the wrong granularity or the wrong moment.

---

## The 20 skills

| Skill | What it does |
|-------|-------------|
| **code-implementer** | Executes implementation phase by phase from `DESIGN.md`. Enforces test-alongside, inline security gates, and phase gates between each implementation phase. |
| **comprehensive-test-strategy** | Defines the test pyramid and standards: unit, integration, contract, acceptance, property-based, and performance tests. Sets ratios and coverage expectations. |
| **code-review-quality-gates** | PR review checklist, comment severity labels (Blocking / Suggestion / Question / Nitpick), review SLA, quality gate process. |
| **pr-merge-orchestrator** | Pre-merge gate verification, PR description generation from pipeline artifacts, review coordination, merge execution, release tagging. |
| **devops-pipeline-governance** | CI/CD design, deployment strategies (blue-green, canary, rolling), IaC pipeline, rollback procedures, pipeline security. |
| **release-readiness** | Go/no-go decision process, full release checklist (8 sections), deployment plan, post-release verification. |
| **database-migration** | Migration classification, expand-contract pattern, lock-free DDL, CI validation, production deployment sequence for schema changes. |
| **documentation-system-design** | Runbooks, API guides, C4 context diagrams, operational handover. Applied before go-live and when handing off to another team. |
| **observability-sre-practice** | Metrics, logs, traces (three pillars), SLO definition and management, error budgets, alerting standards, SLO review cadence. |
| **api-contract-enforcer** | Runtime enforcement of API contracts: Pact consumer-driven tests, schema registry compatibility, contract drift detection in CI. |
| **executable-acceptance-verification** | BDD test execution from the traceability matrix. Converts acceptance criteria into runnable Gherkin scenarios. Produces formal milestone sign-off. |
| **performance-reliability-engineering** | NFR definition, load/stress/soak tests (k6), reliability patterns (circuit breaker, retry, bulkhead, timeout), capacity planning. |
| **ai-assisted-engineering** | Governance for AI tool use: what is permitted, elevated review checklist for AI-generated code, effective prompt patterns, IP policy. |
| **llm-app-development** | Building software that calls an LLM internally: eval-driven development, prompt versioning, pipeline pattern selection, RAG design, agent tool design, production LLM monitoring. |
| **feature-flag-lifecycle** | Flag types, create/roll out/remove lifecycle, debt detection, flag registry. |
| **accessibility** | WCAG 2.2 AA compliance mapped to dev tasks, 15-minute PR checklist, axe-core CI integration, EU Accessibility Act and ADA legal context. |
| **architecture-fitness** | Automated CI enforcement of import boundaries, dependency budgets, dead code detection, coverage floors. |
| **distributed-systems-patterns** | Sagas (orchestration/choreography), event sourcing, CQRS, transactional outbox, idempotency keys, consistency models. |
| **disaster-recovery** | RTO/RPO tiers, 3-2-1 backup, multi-region failover patterns, DR drill runbooks, restore verification. |
| **caching-strategy** | Cache layer design, cache-aside/read-through patterns, invalidation, CDN config, stampede prevention. |

---

## Quality should make delivery faster, not slower

The phase 2 skills are designed so that quality checks are embedded in the development flow rather than bolted on at the end. Key examples:

- `code-implementer` runs security gates inline, not as a separate audit at the end
- `comprehensive-test-strategy` defines tests written alongside code, not after
- `pr-merge-orchestrator` generates the PR description from existing pipeline artifacts, not as a manual write-up
- `api-contract-enforcer` catches drift in CI automatically, not in manual integration testing sessions

When editing these skills, preserve the "quality as you go" pattern. A phase 2 skill that creates a big batch checkpoint at the end has been implemented wrong.

---

## Key dependencies between phase 2 skills

- `code-implementer` requires `DESIGN.md` from phase 1 to be approved before starting
- `executable-acceptance-verification` requires the traceability matrix from `requirements-tracer` (phase 1)
- `api-contract-enforcer` requires frozen specs from `specification-driven-development` (phase 1)
- `pr-merge-orchestrator` requires `executable-acceptance-verification` to have passed
- `pr-merge-orchestrator` requires the security gate from `security-audit-secure-sdlc` to be signed off
- `release-readiness` requires the full phase 2 pipeline to be substantially complete

---

## Reference files — load on demand

Keep heavy content in `references/`. The `SKILL.md` for each skill should contain the process and decision logic. Templates, worked examples, and detailed checklists live in `references/` and are loaded only when needed.

Do not add to `SKILL.md` what belongs in `references/`. A `SKILL.md` over 200 lines is a sign that reference material has leaked into the process document.

---

## Pipeline position

Phase 2 sits between phase 1 (foundation) and phase 3 (operations). The `sdlc-orchestrator` manages the transition. When working standalone, verify:
- Phase 1 outputs are complete before starting phase 2 skills that depend on them
- Phase 2 outputs (merged code, docs, observability) are in place before phase 3 applies
