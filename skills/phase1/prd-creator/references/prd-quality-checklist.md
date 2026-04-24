# PRD quality checklist

Run this checklist before approving a PRD and passing it to Stage 2 (requirements tracing). Every item must pass. Document failures with a specific note about what is missing or wrong.

---

## Section completeness

- [ ] Section 1 (Executive summary) — present and readable by a non-technical stakeholder
- [ ] Section 2 (Problem statement) — includes evidence of the problem, not just a description
- [ ] Section 3 (Goals) — present and contains at least 2 goals
- [ ] Section 4 (Non-goals) — present and contains at least 2 entries
- [ ] Section 5 (User personas) — present with at least 1 persona with a full workflow description
- [ ] Section 6 (Functional requirements) — present with at least 3 requirements
- [ ] Section 7 (NFRs) — present with at minimum performance, availability, and security NFRs
- [ ] Section 8 (Constraints and dependencies) — present (may be brief, but not absent)
- [ ] Section 9 (Success metrics) — present with a primary metric named
- [ ] Section 10 (Out of scope) — present (may be "none identified" if genuinely empty, but must be explicit)
- [ ] Section 11 (Open questions) — present (empty is acceptable only if all questions are resolved)

---

## Goals quality

- [ ] Every goal contains a measurable element (a number, a threshold, a verifiable condition)
- [ ] No goal reads as a feature ("add a button") — goals must be outcomes ("reduce time to X")
- [ ] Goals are achievable within the stated constraints
- [ ] Goals are connected to the problem statement — solving the problem produces these outcomes

**Fail examples:**
- "Improve user experience" — not measurable
- "Add device management" — that is a feature, not a goal
- "Make the system faster" — faster by how much, for whom, by when?

---

## Functional requirements quality

- [ ] Every requirement uses "shall" (mandatory) or "should" (optional) — no ambiguous verbs
- [ ] Every requirement is testable — someone can write a pass/fail test for it
- [ ] No requirement depends on unstated assumptions
- [ ] No requirement duplicates another requirement
- [ ] Every requirement has a priority (Must have / Should have / Nice to have)

**Fail examples:**
- "The system should work reliably" — not testable
- "Users should be able to manage devices" — not specific enough
- "The API should be fast" — not measurable

---

## NFR quality

- [ ] Performance NFR contains: a metric name, a numeric threshold, and a load condition
- [ ] Availability NFR contains: a percentage and a measurement period
- [ ] Security NFR names the mechanism, not just the goal
- [ ] All NFRs have a measurement method (how will you verify this in testing?)

**Fail examples:**
- "The system must be performant" — not measurable
- "Security must be adequate" — not testable
- "The system must be highly available" — what does "high" mean?

---

## Non-goals quality

- [ ] Non-goals are things a reasonable person might expect this product to do
- [ ] Non-goals are not trivially excluded things (e.g., "this API will not fly to the moon")
- [ ] Non-goals do not overlap with "out of scope" (non-goals = never; out of scope = not this phase)

---

## Success metrics quality

- [ ] Primary metric is a single, clear number or rate
- [ ] Data source is named (where does the measurement come from?)
- [ ] Evaluation timeline is stated ("30 days post-launch", not "eventually")
- [ ] The metric actually measures whether the goal was achieved (not a proxy for a proxy)

---

## Open questions

- [ ] No open questions in Section 3 (Goals) — goals must be agreed before work starts
- [ ] No open questions in Section 6 (Functional requirements) — requirements must be defined
- [ ] No open questions in Section 7 (NFRs) — NFRs must be defined before design begins
- [ ] No open questions in Section 9 (Success metrics) — measurement must be agreed
- [ ] All open questions (in any section) have a named owner
- [ ] All open questions have a deadline
- [ ] No open question is older than 5 business days without an update

---

## Approval

- [ ] Product owner has reviewed and signed off
- [ ] Engineering lead has reviewed and signed off (specifically: are the technical constraints accurate? Are the NFRs achievable?)
- [ ] Partner company lead has reviewed and signed off (if cross-company)
- [ ] No reviewer has outstanding "Changes requested" — all reviewers have approved

---

## Scoring

| Result | Criteria |
|--------|----------|
| PASS — ready to proceed | All items checked |
| CONDITIONAL PASS | All mandatory items checked; minor gaps in optional sections with agreed resolution |
| FAIL — return to author | Any item in Goals, FR, NFR, Success Metrics, or Approval not checked |

---

## Gap report format (for FAIL cases)

```
## PRD quality gap report

**PRD:** [title]
**Reviewed by:** [name]
**Date:** [date]
**Result:** FAIL

### Blocking gaps (must be resolved before proceeding)

| Section | Item | Problem | Required action |
|---------|------|---------|-----------------|
| Section 3 | Goal 2 | "Improve performance" is not measurable | Rewrite with a specific latency or throughput target |
| Section 7 | NFR-003 | No measurement method stated | Add how this NFR will be verified in testing |

### Non-blocking gaps (resolve before Stage 3)

| Section | Item | Problem | Recommendation |
|---------|------|---------|----------------|
| Section 11 | OQ-002 | No deadline set | Assign a deadline; this blocks design if unresolved |
```
