---
name: architecture-review-governance
description: >
  Defines architecture principles, catches design problems before code is written, and
  detects drift as delivery proceeds. Use this skill whenever the user wants to: review
  a system design or architecture proposal, evaluate trade-offs between technical approaches
  (microservices vs monolith, sync vs async, edge vs cloud), identify architectural
  anti-patterns or hidden coupling, enforce service and component boundaries, review
  integration design or data flow, validate non-functional requirements, detect architecture
  drift, or self-review a design before presenting it to the team. Also trigger when the
  user asks "is this the right approach", "what are the trade-offs", or "does this
  architecture scale".
---

# Architecture review & governance

## Purpose

Architecture decisions made early are expensive to reverse later. This skill ensures that every significant technical decision is reviewed against defined principles before code is written and that anti-patterns are caught before they are embedded in the codebase.

For a small team, architecture review is primarily a **self-review discipline** — you review your own design before you start building, using a structured checklist that catches the problems most likely to hurt you later. Reserve formal team review for designs that are large, novel, or high-risk.

## When to use

- Self-reviewing a design before starting implementation (always — one gate)
- Evaluating trade-offs between two or more technical approaches
- Detecting or documenting architecture drift
- Reviewing service boundaries or integration design
- Validating non-functional requirements before commitment
- A new service, integration point, or external dependency is being added
- The team is unsure whether an architectural approach has hidden problems
- A quarterly drift check is due on an existing system

## When NOT to use this skill

- Individual PR code review → `code-review-quality-gates`
- Documenting a specific decision already made → `architecture-decision-records`
- Testing that the architecture performs to NFRs → `performance-reliability-engineering`
- **Automated CI enforcement of architectural rules** (import boundaries, dependency budgets, dead code detection, coverage floors) → `architecture-fitness`. This skill handles the human design review; `architecture-fitness` handles the automated enforcement of the rules that come out of it.

---

## Process

1. Confirm what is being reviewed: identify the component or system, its external dependencies, and the stated NFRs. If any of these are unclear, ask before proceeding — a review without a clear scope produces low-value findings.
2. Load the project's architecture principles from `references/architecture-principles-template.md`. If none exist yet, establish them now before reviewing anything against them.
3. Run the 15-item self-review checklist (see below). Mark each item Pass or Fail with a brief note.
4. For any Fail on Critical items (2, 4, 7, 8, 9): stop and record a Critical finding. Do not proceed to implementation until these are resolved.
5. Cross-reference the design against `references/anti-patterns.md`. Focus on: distributed monolith, synchronous call chains, shared databases, missing circuit breakers.
6. For each significant trade-off decision point, use `references/trade-off-frameworks.md` to structure the evaluation. Record the rationale so it can be captured in an ADR.
7. Validate NFRs: verify the design has a named mechanism to meet each one. Vague NFRs must be made measurable before review completes.
8. Produce the architecture review report in the output format below. Assign severity to each finding.
9. For Critical and High findings: identify an owner and a resolution deadline before the review is considered done.
10. Append the execution log entry.

## Architecture principles

Before reviewing any design, establish the project's architecture principles. These are the non-negotiables — patterns and properties that every architectural decision must respect. Principles without rationale are ignored; principles with rationale are followed.

Use `references/architecture-principles-template.md` to define and document the project's principles. Typical principles for a cloud/edge system:

1. **Design for failure** — every component assumes its dependencies will fail
2. **Each service owns its data** — no direct database access across service boundaries
3. **Observability is not optional** — every service must emit logs, metrics, and traces from day one
4. **Contracts are the truth** — implementation must conform to the agreed API contract, not the other way around
5. **Prefer async over sync for non-critical paths** — reduces coupling and improves resilience
6. **Security is structural, not bolted on** — authentication, authorisation, and encryption are designed in, not added later

## How to conduct an architecture self-review

Run this before every design that involves more than a trivial change. It takes 15–30 minutes and catches the problems that are expensive to fix after implementation.

### Step 1 — Understand what is being reviewed

Before evaluating anything, confirm you can answer:
- What problem does this design solve?
- What are its external dependencies and consumers?
- What are the stated NFRs it must satisfy?

If any of these are unclear, clarify before proceeding.

### Step 2 — Run the 15-item self-review checklist

| # | Check | Pass/Fail | Notes |
|---|-------|-----------|-------|
| 1 | Every component has a single, clear responsibility | | |
| 2 | No direct database access across service boundaries | | |
| 3 | All external dependencies can fail — what happens when they do? | | |
| 4 | Synchronous calls in critical paths have timeouts and fallbacks | | |
| 5 | No circular dependencies between services | | |
| 6 | Every NFR is addressable by a named design mechanism | | |
| 7 | Authentication and authorisation are designed in, not deferred | | |
| 8 | Secrets are not in code or config files | | |
| 9 | No shared mutable state between services (no shared DB) | | |
| 10 | Every new external dependency is necessary (not convenience) | | |
| 11 | Data flows are explicit — no implicit side effects | | |
| 12 | The design can be implemented in independently deployable phases | | |
| 13 | Observability (metrics, logs, traces) is planned, not deferred | | |
| 14 | Migration strategy exists for any data model changes | | |
| 15 | The simplest approach that satisfies the requirements was chosen | | |

Any "Fail" on items 2, 4, 7, 8, or 9 is a Critical finding — do not proceed to implementation.

### Step 3 — Check for anti-patterns

Cross-reference the design against `references/anti-patterns.md`. Focus especially on: distributed monolith, synchronous call chains, shared databases across services, and missing circuit breakers.

### Step 4 — Evaluate trade-offs

For any significant decision point, use `references/trade-off-frameworks.md` to structure the evaluation. Record the rationale in an ADR — especially why alternatives were rejected.

### Step 5 — Validate NFRs

Verify the design can plausibly meet each NFR. Vague NFRs ("the system should be fast") must be made measurable before review. Use `references/nfr-template.md`.

## Severity ratings

- **Critical** — Blocks the design from proceeding. Architectural flaw that will cause system failure, data loss, security breach, or inability to meet contractual commitments. Must be resolved before implementation begins.
- **High** — Significant quality, reliability, or maintainability impact. Should be resolved before the next milestone.
- **Medium** — Should be addressed before the milestone after next. Does not block current work.
- **Low** — Good to fix, not urgent. Can be addressed in a future sprint.
- **Informational** — Observation with no required action. Recorded for awareness.

## Architecture drift detection

Architecture drift occurs when implementation deviates from the agreed architecture without a documented decision. Detect drift by:

- Comparing current service boundaries against the agreed architecture diagram at each sprint review
- Checking for new inter-service database access (a common drift pattern)
- Reviewing dependency lists for unapproved new dependencies
- Looking for synchronous calls in paths where async was agreed

When drift is detected: document it in the decision log with status "Deviation", raise it at the next architecture review, and decide whether to correct the code or update the architecture (with a new ADR).

## Architecture gate

One gate: **before any implementation begins**.

The self-review checklist must pass, all Critical findings must be resolved, and significant trade-off decisions must be recorded as ADRs. This gate is not a committee — it is a discipline. Run it on every non-trivial design.

If the design is large, novel, or high-risk, share the `DESIGN.md` with a second engineer for review before implementation starts. Two sets of eyes catch what one misses.

## Output format

### Architecture review report

**Review subject:** [Component or system name]
**Review date:** [date]
**Reviewer:** [name, role]
**Overall status:** Pass / Conditional pass / Fail

### Findings

| # | Finding | Domain | Severity | Recommendation | Owner | Status |
|---|---------|--------|----------|----------------|-------|--------|

### Trade-off decisions

[For each significant trade-off, summarise what was decided and link to the ADR]

### NFR validation status

| NFR | Target | Validated? | Evidence |
|-----|--------|-----------|---------|

### Action items

| Action | Owner | Due | Priority |
|--------|-------|-----|---------|

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] architecture-review-governance — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] architecture-review-governance — Review of device-registry service design
[2026-04-20] architecture-review-governance — Quarterly architecture health review
[2026-04-20] architecture-review-governance — Anti-pattern check: distributed monolith suspected
```

---

## Reference files

- `references/architecture-principles-template.md` — Template for project architecture principles with 8 pre-filled examples
- `references/anti-patterns.md` — Catalogue of 12 common architecture anti-patterns with detection and mitigation
- `references/trade-off-frameworks.md` — Structured frameworks for common trade-off decisions
- `references/nfr-template.md` — Non-functional requirements template with worked examples

## Scripts

- `scripts/review_report.py` — Generates a formatted architecture review report from a JSON findings file
