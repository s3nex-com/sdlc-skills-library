# skills/ — the 41-skill library plus 10 domain tracks

This directory contains all skill packages and domain tracks. Each **skill** has a `SKILL.md` (loaded when the skill triggers), a `references/` subdirectory (loaded on demand), and some have `scripts/`. Each **track** (under `tracks/`) has a `TRACK.md` plus `references/` — tracks are overlays, not skills. Full tracks guide: `docs/tracks.md`.

---

## All 41 skills by phase

### Workflow (1)
| Skill | Directory |
|-------|-----------|
| sdlc-orchestrator | `workflow/sdlc-orchestrator/` |

### Phase 1 — Foundation (10)
| Skill | Directory |
|-------|-----------|
| prd-creator | `phase1/prd-creator/` |
| requirements-tracer | `phase1/requirements-tracer/` |
| design-doc-generator | `phase1/design-doc-generator/` |
| specification-driven-development | `phase1/specification-driven-development/` |
| architecture-review-governance | `phase1/architecture-review-governance/` |
| architecture-decision-records | `phase1/architecture-decision-records/` |
| technical-risk-management | `phase1/technical-risk-management/` |
| security-audit-secure-sdlc | `phase1/security-audit-secure-sdlc/` |
| stakeholder-sync | `phase1/stakeholder-sync/` |
| data-governance-privacy | `phase1/data-governance-privacy/` |

### Phase 2 — Delivery quality (20)
| Skill | Directory |
|-------|-----------|
| code-implementer | `phase2/code-implementer/` |
| comprehensive-test-strategy | `phase2/comprehensive-test-strategy/` |
| code-review-quality-gates | `phase2/code-review-quality-gates/` |
| pr-merge-orchestrator | `phase2/pr-merge-orchestrator/` |
| devops-pipeline-governance | `phase2/devops-pipeline-governance/` |
| release-readiness | `phase2/release-readiness/` |
| database-migration | `phase2/database-migration/` |
| documentation-system-design | `phase2/documentation-system-design/` |
| observability-sre-practice | `phase2/observability-sre-practice/` |
| api-contract-enforcer | `phase2/api-contract-enforcer/` |
| executable-acceptance-verification | `phase2/executable-acceptance-verification/` |
| performance-reliability-engineering | `phase2/performance-reliability-engineering/` |
| ai-assisted-engineering | `phase2/ai-assisted-engineering/` |
| llm-app-development | `phase2/llm-app-development/` |
| feature-flag-lifecycle | `phase2/feature-flag-lifecycle/` |
| accessibility | `phase2/accessibility/` |
| architecture-fitness | `phase2/architecture-fitness/` |
| distributed-systems-patterns | `phase2/distributed-systems-patterns/` |
| disaster-recovery | `phase2/disaster-recovery/` |
| caching-strategy | `phase2/caching-strategy/` |

### Phase 3 — Sustained operations (9)
| Skill | Directory |
|-------|-----------|
| technical-debt-tracker | `phase3/technical-debt-tracker/` |
| delivery-metrics-dora | `phase3/delivery-metrics-dora/` |
| dependency-health-management | `phase3/dependency-health-management/` |
| incident-postmortem | `phase3/incident-postmortem/` |
| team-coaching-engineering-culture | `phase3/team-coaching-engineering-culture/` |
| chaos-engineering | `phase3/chaos-engineering/` |
| project-closeout | `phase3/project-closeout/` |
| cloud-cost-governance | `phase3/cloud-cost-governance/` |
| developer-onboarding | `phase3/developer-onboarding/` |

### Phase 4 — Advanced assurance (1)
| Skill | Directory |
|-------|-----------|
| formal-verification | `phase4/formal-verification/` |

---

## Tracks — domain overlays (10)

| Track | Directory |
|-------|-----------|
| fintech-payments | `tracks/fintech-payments/` |
| saas-b2b | `tracks/saas-b2b/` |
| web-product | `tracks/web-product/` |
| data-platform-mlops | `tracks/data-platform-mlops/` |
| healthcare-hipaa | `tracks/healthcare-hipaa/` |
| regulated-government | `tracks/regulated-government/` |
| real-time-streaming | `tracks/real-time-streaming/` |
| consumer-product | `tracks/consumer-product/` |
| open-source | `tracks/open-source/` |
| mobile | `tracks/mobile/` |

Template: `tracks/TRACK-TEMPLATE.md`. Track-level invariants: `tracks/CLAUDE.md`.

---

## Key cross-skill pipelines

**Main feature pipeline:**
```
prd-creator → requirements-tracer → design-doc-generator → code-implementer → pr-merge-orchestrator
```

**Contract enforcement pipeline:**
```
specification-driven-development → api-contract-enforcer
```

**Security — runs alongside all phases:**
```
security-audit-secure-sdlc (threat model at design, security gate at each code review, pipeline gate at CI)
```

**Master conductor:**
```
sdlc-orchestrator (orchestrates all of the above; single entry point for non-trivial work)
```

---

## Standalone vs. orchestrated

Use a skill **standalone** when:
- You have a specific, bounded need (e.g. "write an ADR for this decision", "run a postmortem")
- The pipeline has already started and you need one specific piece
- You are in phase 3/4 work that is not feature development

Use **sdlc-orchestrator** when:
- You are starting any non-trivial feature from scratch
- You are unsure which skill applies or in what order
- You need to verify stage gates have been completed before proceeding

---

## The "when NOT to use it" principle

Every skill has an explicit list of adjacent situations that belong to a different skill. Before adding behaviour to a skill, check that list. If the situation already appears in another skill's "when to use it", it belongs there — not here. Skill boundaries must stay clean or the whole library becomes ambiguous.

Example: runtime enforcement of API contracts belongs to `api-contract-enforcer`, not `specification-driven-development`. Spec design belongs to `specification-driven-development`, not `api-contract-enforcer`. These are hard boundaries.

---

## File organisation

```
skill-name/
  SKILL.md          — loaded when skill triggers; contains full process
  references/       — loaded on demand; reference material, templates, examples
  scripts/          — automation scripts (only some skills have these)
```

Keep heavy reference material (templates, worked examples, anti-pattern catalogues) in `references/`. `SKILL.md` should contain the process, not the full library of supporting material.
