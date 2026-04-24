# skills/phase3/ — Sustained operations

Phase 3 skills apply after go-live and run continuously. They are the "keep the lights on and improve over time" layer. These skills are deliberately lighter than phase 1–2 — they should feel like maintenance and improvement cadences, not major project events.

**The value of phase 3 is in the cadence, not the ceremonies.** The rhythm matters: monthly debt review, monthly DORA check, dependency audit every month, post-incident review within 5 days. Missing the cadence once is fine. Missing it three times in a row means the system is silently degrading.

---

## The 9 skills

| Skill | What it does |
|-------|-------------|
| **technical-debt-tracker** | Maintains a visible debt register: 7 debt types, 2 intentionality dimensions, prioritisation scoring. Prevents delivery velocity from quietly degrading. |
| **delivery-metrics-dora** | Measures the four DORA metrics (Deployment Frequency, Lead Time, Change Failure Rate, MTTR). Monthly report, quarterly review. Data, not anecdote. |
| **dependency-health-management** | CVE triage, EOL planning, SBOM generation, monthly dependency audit. Keeps third-party dependencies secure and current. |
| **incident-postmortem** | Blameless post-incident review: timeline, 5 Whys RCA, action items. Mandatory for P1 and P2 incidents, completed within 5 days. |
| **team-coaching-engineering-culture** | Culture assessment, failure pattern diagnosis, retrospectives, capability development. Applied when the same quality problems keep recurring despite technical fixes. |
| **chaos-engineering** | Hypothesis-driven chaos experiments, fault injection in CI, game days, steady-state discipline. Run after go-live to verify resilience under real failure conditions. |
| **project-closeout** | Documentation audit, deliverables sign-off, knowledge transfer, operational handover, DORA final report, lessons learned. The formal end of a project or engagement. |
| **cloud-cost-governance** | Cost attribution via tagging, per-feature cost estimation in PRDs, monthly optimization audit, budget alerts, anomaly response playbook. |
| **developer-onboarding** | Day-1/week-1/month-1 checklists, local dev setup, engineering norms codification, onboarding retros. |

---

## Cadence guide

| Skill | Cadence |
|-------|---------|
| technical-debt-tracker | Monthly review and reprioritisation |
| delivery-metrics-dora | Monthly calculation, quarterly joint review |
| dependency-health-management | Monthly audit, immediate response to new CVEs |
| incident-postmortem | Within 5 days of every P1 or P2 incident |
| team-coaching-engineering-culture | As needed; milestone retrospectives after each major delivery |
| chaos-engineering | Quarterly game days; fault injection in CI continuously |
| project-closeout | Once, at the end of a project or engagement |
| cloud-cost-governance | Monthly optimization audit; immediate response to budget alerts; tag policy enforced at all times |
| developer-onboarding | Per new hire (day 1, week 1, month 1); onboarding retro after each cohort; norms doc reviewed quarterly |

---

## The incident-postmortem is blameless

This is not a preference or a style choice. The post-mortem process must be blameless and this must never change. Blameless means:
- The timeline is reconstructed from facts and system state, not from memory or testimony about individuals
- The 5 Whys analysis identifies system and process causes, not people causes
- Action items are systemic: improve monitoring, improve runbooks, improve processes — not "engineer X should be more careful"
- Facilitation keeps the conversation on systems, not individuals

If you find the post-mortem template drifting toward blame (language like "the engineer failed to...", "negligence", "should have known"), revert it. That language will cause people to hide incidents instead of reporting them, which is the worst possible outcome.

---

## What phase 3 is not

Phase 3 skills are not a second chance to do phase 1–2 work. If you find yourself using `technical-debt-tracker` to catch things that `code-review-quality-gates` should have caught, or using `dependency-health-management` to fix what `security-audit-secure-sdlc` should have gated, the upstream skills need attention.

Phase 3 handles what gets through and what accumulates over time. It is not a substitute for upstream quality gates.

---

## Editing phase 3 skills

When editing:
- Keep these skills lighter than phase 1–2 equivalents. A monthly debt review does not need 12 steps.
- The cadence callouts (monthly, within 5 days, quarterly) are load-bearing. Do not make them vague ("periodically", "as appropriate").
- The blameless principle in `incident-postmortem` is absolute. Never soften or qualify it.
- `delivery-metrics-dora` should produce numbers, not narratives. Preserve the SQL queries and metric definitions.
