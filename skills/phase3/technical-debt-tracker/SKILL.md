---
name: technical-debt-tracker
description: >
  Activate when inventorying technical debt, prioritising debt repayment, making the case for
  debt remediation work to stakeholders, categorising architectural versus code-level debt,
  estimating the cost of carrying debt versus paying it down, or tracking debt items over time.
  Use when delivery velocity is degrading due to accumulated debt, when a new team is taking
  over a codebase and needs to understand its liabilities, or when reviewing a codebase to
  produce a debt report.
---

# Technical debt tracker

## Purpose

Technical debt is the cost of carrying suboptimal technical decisions. Like financial debt, it accrues interest: the longer it is carried, the more it costs. Making debt visible and quantified is the first step to managing it deliberately rather than accidentally.

---

## When to use

- Delivery velocity is degrading and the team suspects accumulated technical debt is the cause
- Taking over a new or inherited codebase — run an initial debt assessment to understand the liabilities before adding features
- The debt register needs a monthly review and re-prioritisation
- A stakeholder needs a structured case for why debt remediation work belongs in the sprint
- Code review has surfaced a systemic problem that belongs in the debt register rather than just a PR comment
- A specific debt item needs to be formally evaluated for severity, velocity impact, and remediation cost

## When NOT to use

- **Active security risks or threat exposure** — use `technical-risk-management` for proactive risk identification and mitigation, not the debt register.
- **Outdated or vulnerable third-party dependencies (CVEs, EOL runtimes)** — use `dependency-health-management`. Debt register links to it but does not duplicate CVE triage.
- **Design problems in new work being built right now** — use `architecture-review-governance` at design time, not the debt tracker after the fact.
- **Code quality defects caught at PR time** — use `code-review-quality-gates`. Phase 3 debt tracking is for what accumulated, not what a review should have caught.
- **Infrastructure cost or waste** — use `cloud-cost-governance`. Cost inefficiency is not debt unless it reflects a known-suboptimal architectural choice.

---

## Process

### Initial debt assessment (new codebase or brownfield)

1. Walk through all 7 debt types (Architecture, Design, Code, Test, Dependency, Infrastructure, Documentation). For each type, identify specific instances.
2. For each debt item found: record it using the debt item format — type, severity, location, description, impact, estimated remediation effort.
3. Classify each item by intentionality (deliberate/prudent, deliberate/reckless, inadvertent/prudent, inadvertent/reckless). This informs the priority and the conversation with the team.
4. Score each item across the three prioritisation factors (Reliability impact, Velocity impact, Remediation cost). Calculate the priority score.
5. Produce the debt register summary.

### Monthly review

6. Review the register for items whose priority score has changed (the codebase grew; a previously low-risk item is now on a critical path).
7. Retire resolved items. Re-rank open items.
8. Recommend a debt budget allocation for the next sprint based on current debt levels.
9. Produce the updated debt register summary showing new, resolved, and net-change.

### Individual debt item

10. Use the debt item format for every new item added. Never add a debt item without an estimated remediation effort and acceptance criteria for resolution — otherwise the item will sit in the register indefinitely.
11. For security debt: any item with a known exploitable vulnerability jumps to the top of the queue regardless of priority score.
12. Append the execution log entry.

## Debt taxonomy

Not all debt is equal. Categorise debt before prioritising it.

### By intentionality

| Category | Description | Action |
|----------|-------------|--------|
| Deliberate / prudent | A conscious trade-off made to meet a deadline, with a plan to address later | Track; pay down on schedule |
| Deliberate / reckless | A shortcut taken knowing it would cause problems, with no plan | High priority; address before it grows |
| Inadvertent / prudent | Code that was correct at the time but is now known to be suboptimal | Track; address as part of normal refactoring |
| Inadvertent / reckless | Bad practices introduced through lack of awareness | Training opportunity; fix urgently |

### By type

| Type | Examples | Impact |
|------|---------|--------|
| Architecture debt | Distributed monolith, missing service boundaries, wrong data ownership | High — limits scalability and independent deployment |
| Design debt | God objects, missing abstractions, over-abstraction | Medium — slows feature development |
| Code debt | Duplication, complex conditionals, magic numbers, undocumented workarounds | Low-Medium — reduces readability and increases bug risk |
| Test debt | Missing test coverage, brittle tests, no integration tests | High — regression risk increases with every change |
| Dependency debt | Outdated libraries, known CVEs not yet patched, unsupported frameworks | Variable — security and compatibility risk |
| Infrastructure debt | Manual provisioning, no IaC, no automated backups, single points of failure | High — operational risk |
| Documentation debt | No runbooks, outdated API docs, no architecture records | Medium — increases operational cost and onboarding time |

---

## Debt item format

Each debt item should be logged with enough context to act on it:

```markdown
## TDB-{number}: {Short title}

**Type:** Architecture | Design | Code | Test | Dependency | Infrastructure | Documentation
**Severity:** Critical | High | Medium | Low
**Location:** {file path, module, or system area}
**Identified by:** {name}
**Date identified:** {date}
**Status:** Open | In progress | Resolved | Accepted (with rationale)

### Description
{What is the problem? Be specific.}

### Why it is debt
{Why is this suboptimal? What design principle or best practice does it violate?}

### Impact if not addressed
{What happens as this debt accumulates? Rate change velocity? Reliability risk? Security risk? New engineer onboarding cost?}

### Estimated remediation effort
{Story points or rough time estimate for the fix}

### Recommended fix
{What should replace or fix this?}

### Acceptance criteria for resolution
{How do we know this is fixed? What tests or evidence confirm resolution?}
```

### Example debt item

```markdown
## TDB-017: Device registry client has no circuit breaker

**Type:** Architecture
**Severity:** High
**Location:** services/ingestion/clients/device_registry.go
**Identified by:** Alice Chen
**Date identified:** 2024-03-15
**Status:** Open

### Description
The device registry HTTP client makes synchronous calls on every ingest request with no
circuit breaker or fallback. If the device registry becomes slow or unavailable, all
ingestion requests queue behind the timeout (currently 30 seconds).

### Why it is debt
Violates the "design for failure" architecture principle. Lack of a circuit breaker
allows a dependency outage to cascade into a full ingestion service outage.

### Impact if not addressed
A device registry outage of > 5 minutes will exhaust the ingestion service's
goroutine pool, causing a full service outage. Historical device registry p99 latency
has spiked to 2–3s on three occasions in the last 6 months.

### Estimated remediation effort
3 story points (implement circuit breaker using existing circuitbreaker library + tests)

### Recommended fix
Add circuit breaker with: failure threshold 5, recovery timeout 30s.
On open circuit, reject new events with 503 (better than queuing behind a 30s timeout).
Cache the last known registration status per device for 5 minutes as a fallback.

### Acceptance criteria for resolution
- Circuit breaker unit tests pass
- Integration test: device registry down → ingestion fails fast with 503, not after 30s timeout
- Load test: device registry at 3s latency → ingestion p99 < 600ms (not 30s)
```

---

## Debt prioritisation

Score each item across three factors (1–5 each):

| Factor | 1 | 5 |
|--------|---|---|
| Reliability impact | No impact | Service outage risk |
| Velocity impact | No slowdown | Blocks new features |
| Remediation cost | Months of work | A day's work (inverse — cheap = high score) |

**Priority score = average of three factors**

- Score ≥ 4: address within 30 days
- Score ≥ 3: in next sprint backlog
- Score < 3: track in register, defer

Security debt is a special case: any item with a known exploitable vulnerability jumps to the top of the queue regardless of score.

---

## Debt budget allocation

The sustainable approach: allocate a fixed percentage of every sprint to debt remediation.

| Team state | Debt allocation | Rationale |
|------------|----------------|-----------|
| Delivering new features rapidly | 20% of sprint | Prevent accumulation |
| Codebase health degrading | 30–40% of sprint | Active remediation |
| Velocity severely impacted by debt | 50%+ of sprint | Emergency remediation |
| Post-delivery stabilisation | 60%+ of sprint | Structured paydown |

Communicate this allocation explicitly in sprint planning. "We are spending 20% of this sprint on debt" is not wasted time — it is investment in delivery capacity.

---

## Debt register summary format

```
## Technical debt register: {System name}

**Last updated:** {date}
**Next review:** {date}

### Summary
| Severity | Open | In progress | Resolved this quarter |
|----------|------|-------------|----------------------|
| Critical | 1 | 0 | 0 |
| High | 5 | 2 | 3 |
| Medium | 12 | 4 | 8 |
| Low | 23 | 6 | 15 |

### Critical and High items
| ID | Title | Type | Score | Owner | Target sprint |
|----|-------|------|-------|-------|--------------|
| TDB-017 | Device registry has no circuit breaker | Architecture | 4.3 | Alice | Sprint 14 |
| TDB-008 | Ingestion service has no integration tests | Test | 4.1 | Bob | Sprint 13 |
| TDB-023 | Event store uses deprecated ORM version | Dependency | 3.8 | Carol | Sprint 15 |

### Debt trend
| Quarter | New items | Resolved | Net change |
|---------|-----------|----------|------------|
| Q1 2024 | 18 | 12 | +6 |
| Q2 2024 | 14 | 19 | -5 |
| Q3 2024 | 11 | 16 | -5 |

Trend: debt reducing at -5 items/quarter. On track to reach target of < 10 Critical+High by Q4.
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] technical-debt-tracker — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] technical-debt-tracker — Debt assessment: new service onboarded, 7 debt items identified
[2026-04-20] technical-debt-tracker — Monthly review: TDB-012 prioritised for Sprint 15
```

---

## Output format

### Debt assessment report

```
## Technical debt assessment: {Service name}

**Date:** {date}
**Assessor:** {name}
**Version reviewed:** {git SHA or version}

### Executive summary
{2-3 sentences on overall debt health and key concerns}

### Debt by type
| Type | Items | Critical/High | Trend |
|------|-------|--------------|-------|
| Architecture | 3 | 2 | Stable |
| Test | 6 | 3 | Increasing |
| Dependency | 4 | 1 | Improving |

### Priority items requiring immediate action
{Top 3–5 items with IDs, descriptions, owners, and target dates}

### Recommended debt allocation
Based on the current debt level, recommend allocating {n}% of sprint capacity to
debt remediation for the next {n} sprints to stabilise velocity.

### Delivered with this assessment
- Full debt register: {link}
- Prioritised backlog items: {link}
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for debt register templates, prioritisation scoring worksheets, and debt triage facilitation guides as they are developed.
