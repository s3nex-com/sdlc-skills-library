---
name: technical-risk-management
description: >
  Identifies, rates, owns, and tracks technical and project risks. Use this skill
  whenever the user wants to: create or update a risk register, identify risks in a
  new design or delivery plan, rate a risk using probability and impact, design a
  mitigation strategy, track risk status, or define early warning indicators for
  specific risks. Also trigger when the user describes risk situations without naming
  them: "what could go wrong", "I'm worried about the timeline", "this dependency is
  outside our control", "technical risks", "delivery risk", "risk assessment",
  "risk mitigation", "risk tracking", "early warning".
---

# Technical risk management

## Purpose

Late surprises kill projects. This skill forces risks to be identified, rated, owned, and mitigated early — and tracked visibly so the team can see the risk landscape at any time. Risk transparency is how a small team stays ahead of problems instead of reacting to them.

## When to use

- Starting a new project or feature — seed the risk register before any design work begins
- A new dependency, technology, or integration is being introduced that is outside the team's direct control
- The user says "what could go wrong?", "I'm worried about the timeline", or "this dependency is risky"
- A scope change has been approved — re-evaluate existing risks and identify new ones
- An incident or near-miss has occurred — update the risk register to reflect what materialised
- Approaching a milestone boundary — review the register and escalate any risks trending toward Critical
- Reviewing a design and spotting areas of uncertainty that could cause delivery or quality problems

## When NOT to use

- Security-specific threats (STRIDE analysis, vulnerability posture, secure SDLC gates) → `security-audit-secure-sdlc`
- Post-incident analysis after a risk has materialised into an outage → `incident-postmortem`
- Code-level debt, shortcuts, and refactor backlog → `technical-debt-tracker`
- Dependency CVEs, EOL tracking, and SBOM operations → `dependency-health-management`
- Reliability experiments that stress-test risks in production-like environments → `chaos-engineering`
- Capturing an architectural decision made to mitigate a risk → `architecture-decision-records`

## Risk categories

Risks fall into three categories. Check all three during every risk identification session.

| Category | Description | Examples |
|----------|-------------|---------|
| **Technical** | Design, architecture, and security risks | Integration complexity, scalability ceiling, technology immaturity, CVEs, secrets management gaps |
| **Delivery** | Execution, schedule, and operational risks | Capacity constraints, underestimated scope, dependency slippage, missing runbooks, no rollback plan |
| **External** | Third-party and organisational risks | Library EOL, vendor API changes, key person dependency, scope disagreement with client |

If a risk does not fit neatly into one category, pick the closest one and note the nuance in the description. Do not create new categories.

## Risk rating

Rate every risk on two dimensions:

**Probability (1–5):**
1. Rare — unlikely to occur in this engagement
2. Unlikely — may occur in less than 20% of similar projects
3. Possible — may occur in ~50% of similar projects
4. Likely — expected to occur in most similar projects
5. Almost certain — expected to occur in this engagement

**Impact (1–5):**
1. Negligible — minor inconvenience, no milestone impact
2. Low — minor quality or schedule impact; resolves within a sprint
3. Medium — noticeable quality or schedule impact; up to 2-week delay
4. High — significant milestone impact; >2-week delay or quality degradation
5. Critical — project failure, major data loss, contractual breach, or security incident

**Composite score = Probability × Impact (range: 1–25)**

| Score | Priority | Action required |
|-------|----------|----------------|
| 20–25 | Critical | Immediate mitigation; surface to the team now |
| 12–19 | High | Active mitigation required; review every week |
| 6–11 | Medium | Mitigation plan in place; review monthly |
| 1–5 | Low | Monitor; no active mitigation required |

See `references/risk-rating-matrix.md` for the full 5×5 matrix.

## Risk status lifecycle

Track every risk through its status:

1. **Identified** — Risk documented; rating and owner assigned; mitigation not yet started
2. **Being mitigated** — Active mitigation actions underway
3. **Resolved** — Risk no longer exists (mitigation successful or trigger condition no longer possible)
4. **Accepted** — Team acknowledges the risk and accepts it without further mitigation; document the rationale
5. **Escalated** — Risk has materialised or mitigation is failing; requires immediate team attention

## How to identify risks

Run a risk identification session at:
- Project kickoff (before any work begins)
- Each milestone boundary
- After any significant scope change
- After any incident or near-miss

For each category, ask: "What could go wrong in this category that would impact our ability to deliver on time, to quality, within budget, and without legal exposure?"

Do not filter at identification time — record everything, even low-probability risks. Rating and prioritisation come next.

## How to design mitigation strategies

For every risk rated Medium or above, define a concrete mitigation. A mitigation must:
- Be specific enough to assign to an owner
- Be completable within a defined timeframe
- Reduce either the probability or the impact (or both)

**Ineffective mitigation:** "Monitor the situation" (not specific, reduces nothing)
**Effective mitigation:** "Schedule a Kafka performance spike in Sprint 3 to validate 50k events/sec throughput with a realistic payload size. If the target is not met, evaluate Confluent Cloud throughput tiers by Sprint 4."

Every risk also needs a **contingency plan** — what to do if the risk materialises despite mitigation.

## Risk reporting

Review the risk register at each milestone boundary. The summary should:
- Highlight any new Critical or High risks since the last review
- Show status changes (risks moved to Resolved or Escalated)
- Summarise mitigation progress for active High risks
- Note the overall trend (risk score going up or down?)

Use `scripts/risk_report.py` to generate a formatted report from a register CSV/JSON.

## Process

### Risk identification session

1. Ask "what could go wrong?" across all three categories: Technical, Delivery, and External. Do not filter at this stage — record everything.
2. For each risk identified, write a concise title and description: what could happen, why, and what the trigger condition is.
3. Assign each risk to a category (Technical / Delivery / External). If a risk spans multiple categories, pick the closest one and note the nuance.

### Rating and prioritisation

4. Rate each risk: Probability (1–5) and Impact (1–5). Calculate the composite score (P×I).
5. Sort by composite score. Risks scoring 12+ are Active — they need mitigation plans now.
6. For every risk scored Medium or above, define a concrete mitigation: specific, time-bounded, with an owner. Vague mitigations ("monitor the situation") do not count.
7. Define a contingency plan for each Active risk: what to do if the risk materialises despite mitigation.
8. Define an early warning indicator: what leading metric or signal would tell you this risk is becoming real?

### Tracking

9. Add all risks to the risk register (`references/risk-register-template.md`). Assign a Risk ID, owner, and review date.
10. At each milestone, review the register: update statuses, escalate risks that have worsened, retire risks that no longer apply.
11. Append the execution log entry.

## Output format

### Risk register entry

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-NNN |
| **Title** | [Short, specific risk title] |
| **Category** | [Technical / Delivery / External] |
| **Description** | [What could happen and why] |
| **Probability** | [1-5 with label] |
| **Impact** | [1-5 with label] |
| **Composite score** | [P×I] |
| **Status** | [Identified / Being mitigated / Resolved / Accepted / Escalated] |
| **Mitigation** | [Specific action to reduce probability or impact] |
| **Contingency** | [What to do if the risk materialises] |
| **Owner** | [Name, role] |
| **Early warning indicator** | [Leading metric or signal that this risk is materialising] |
| **Review date** | [When to re-evaluate this risk] |

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] technical-risk-management — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] technical-risk-management — Risk register seeded for device-registry project
[2026-04-20] technical-risk-management — Monthly risk review; 2 risks escalated to High
[2026-04-20] technical-risk-management — New risk: third-party API EOL identified
```

---

## Reference files

- `references/risk-register-template.md` — Complete register with 6 pre-filled example entries
- `references/risk-rating-matrix.md` — Full 5×5 Probability × Impact matrix

## Scripts

- `scripts/risk_report.py` — Generates a formatted risk summary report from a register CSV/JSON
