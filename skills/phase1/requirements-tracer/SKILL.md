---
name: requirements-tracer
description: >
  Converts business goals into testable, traceable requirements and keeps them linked
  to everything built from them. Use this skill whenever the user wants to: decompose
  a high-level business ask into user stories with BDD acceptance criteria, write
  Given/When/Then test scenarios, maintain or query the traceability matrix linking
  requirements to code and tests, detect orphaned code with no requirement, detect
  requirements with no implementation, or analyse the impact of a scope change. Also
  trigger for: "what does done mean", "what are we actually building", "scope creep",
  "is this in scope", "traceability", "BDD", "given when then", "user story",
  "feature breakdown", "requirements quality".
---

# Requirements tracer & scope control

## Purpose

Vague requirements are the root cause of most project failures. This skill converts business asks into testable, traceable, deliverable units — and keeps them linked to everything built from them. It also enforces scope discipline: every feature must trace back to an agreed requirement, and every requirement must have a clear acceptance criterion before work begins.

## When to use

- Decomposing a high-level business goal into deliverable user stories
- Writing acceptance criteria for a story or requirement
- Detecting orphaned code (no requirement) or unimplemented requirements
- Analysing the impact of a proposed scope change
- Reviewing requirements for quality problems (ambiguity, missing measurability)
- Planning delivery phases and milestones from a requirements list
- The team asks "what does done mean?" or "is this in scope?"
- Before a milestone review, to verify every requirement has code and tests linked to it

## When NOT to use

- Creating or validating the upstream PRD itself → `prd-creator`
- Writing API or event schemas that the stories will consume → `specification-driven-development`
- Producing the technical `DESIGN.md` that implements the stories → `design-doc-generator`
- Running the executable BDD scenarios against a build → `executable-acceptance-verification`
- Enforcing request/response contracts at runtime → `api-contract-enforcer`
- Tracking code-level debt that surfaces during decomposition → `technical-debt-tracker`

## Process

### Decomposition

1. Read the approved PRD. Extract all functional requirements and NFRs explicitly stated.
2. Group related requirements into epics only if the feature is large enough to benefit from grouping. Skip the epic level for small features.
3. For each requirement, write a user story: "As a [role], I want to [action], so that [benefit]."
4. For each story, write Given/When/Then acceptance criteria. Apply the quality test: "Can I automate a test from this criterion?" If not, rewrite until you can.
5. Assign a Story ID (ST-NNN) to each story.
6. Prioritise stories: which are must-have for the first milestone? Which are deferred?

### Traceability

7. Create or update the traceability matrix linking each story to the code modules and tests that implement it. Start with stub entries; fill in as implementation proceeds.
8. Run `scripts/check_orphans.py` before every milestone review to detect unlinked requirements or code.

### Scope change

9. When a scope change request arrives, perform the impact analysis (steps in the "Scope change impact analysis" section) before any approval.
10. Produce a recommendation: Approve / Reject / Defer. Never let scope change silently widen the backlog.

### All sub-tasks

11. Append the execution log entry.

## How to decompose requirements

Work at two levels: **stories** and **acceptance criteria**. That is all a small team needs.

- **User story** — A specific user-facing behaviour: "As a [role], I want to [action], so that [benefit]"
- **Acceptance criteria** — Specific, testable conditions using Given/When/Then format

If the feature is large enough to need grouping, use an **Epic** label (e.g., "Device management") to cluster related stories — but do not add a Feature level between epics and stories. It creates work without adding value at this team size.

See `references/requirement-decomposition-guide.md` for step-by-step worked examples.

**Quality test for acceptance criteria:** Can you write an automated test from this criterion? If not, it is not specific enough.

### Good acceptance criterion
```
Given a valid API key and a well-formed device registration payload
When I POST to /v1/devices
Then the response status is 201 Created
And the response body includes the assigned device_id
And the device appears in subsequent GET /v1/devices requests
```

### Bad acceptance criterion
```
The device registration API should work correctly.
```

## Acceptance criteria patterns

Use `references/acceptance-criteria-patterns.md` for Given/When/Then patterns across:
- Functional requirements (happy path, error path)
- Performance requirements (latency SLOs, throughput targets)
- Security requirements (authentication, authorisation, input validation)
- Integration requirements (contract compliance, response format)
- Negative/error cases (invalid input, missing resource, unauthorised access)

## Traceability matrix

Every requirement must be linked forward to its implementation and tests. The traceability matrix (`references/traceability-matrix-template.md`) maps:

```
Requirement ID → Feature → User Story → Code Module(s) → Test ID(s)
```

Maintain this matrix throughout development. At each milestone, verify:
- Every requirement in "In scope" has at least one code module and one test
- Every code module listed in the project has at least one linked requirement
- Every test has a linked requirement that it is testing

Use `scripts/check_orphans.py` to detect orphans automatically.

## Orphan detection

Two types of orphans must be detected and resolved:

**Unimplemented requirements** — A requirement with no linked code or tests. Either work has not started (acceptable during development) or the requirement was forgotten (not acceptable at milestone acceptance).

**Orphaned code/tests** — Code or tests with no linked requirement. This is scope creep — work that was done but not agreed. Orphaned code must be either linked to an existing requirement (if it implements something already in scope) or removed (if it implements out-of-scope functionality).

Run `scripts/check_orphans.py` before every milestone review.

## Scope change impact analysis

When a scope change request arrives, perform an impact analysis before approval:

1. Identify which existing requirements the change touches
2. Identify which code modules are affected
3. Identify which tests must be updated or added
4. Estimate effort
5. Assess risk (does this change destabilise existing functionality?)
6. Produce a recommendation

Use `references/scope-impact-template.md` for the analysis format.

## Requirement quality review

Before a requirement is approved for development, check:

- **Unambiguous** — Can it be interpreted only one way? If two people read it and could reach different implementations, it is ambiguous.
- **Measurable** — Does it have specific, testable acceptance criteria? "Fast" is not measurable; "p99 latency < 200ms at 1,000 concurrent users" is.
- **Achievable** — Is it technically feasible within the agreed constraints?
- **Independent** — Can it be delivered and tested independently of other requirements, or does it have unacknowledged dependencies?
- **Team-aligned** — Does everyone who will build and review this requirement interpret it the same way? If there is any ambiguity, resolve it before development begins — not during code review.

## Output format

### Requirements decomposition

**Epic (if applicable):** [Epic title] — EP-NNN

**User stories:**

| Story ID | Story | Acceptance criteria | Priority | Status |
|----------|-------|-------------------|---------|--------|

### Traceability status

| Req ID | Status | Code linked | Tests linked | Notes |
|--------|--------|------------|-------------|-------|

### Scope change impact summary

**Change:** [Description]
**Requirements affected:** [count and IDs]
**Effort estimate:** [days]
**Risk:** [High/Medium/Low]
**Recommendation:** [Approve/Reject/Defer]

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] requirements-tracer — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] requirements-tracer — Decomposed PRD into 8 stories with BDD criteria
[2026-04-20] requirements-tracer — Scope impact analysis for requirement change REQ-004
[2026-04-20] requirements-tracer — Orphan detection run; 2 tests without requirements found
```

---

## Reference files

- `references/requirement-decomposition-guide.md` — Step-by-step decomposition with two fully worked examples
- `references/acceptance-criteria-patterns.md` — Given/When/Then patterns for 5 requirement types
- `references/traceability-matrix-template.md` — Matrix template with example rows
- `references/scope-impact-template.md` — Scope change impact analysis format

## Scripts

- `scripts/check_orphans.py` — Detects unimplemented requirements and orphaned code/tests
