---
name: architecture-decision-records
description: >
  Creates, reviews, updates, and manages Architecture Decision Records (ADRs) — the
  institutional memory of technical decision-making. Use this skill whenever the user
  wants to: create an ADR for a technology or architecture decision, document why a
  specific technology was chosen, record a technical decision before implementing it,
  update or supersede an existing ADR, review a proposed decision for completeness,
  check whether a decision warrants an ADR, maintain the ADR index, or understand
  why a past decision was made. Also trigger when the user asks "why are we using X",
  "who decided this", "was this decision documented", "log a design decision",
  "decision history", "record a technical decision", or "document this choice".
---

# Architecture decision records (ADRs)

## Purpose

ADRs are the institutional memory of technical decision-making. Every major technical decision — technology choices, architectural patterns, interface contracts, security posture decisions, tooling selections — must be captured in a structured, version-controlled record that explains not just what was decided but why, what alternatives were considered, and what the consequences are expected to be.

Without ADRs, knowledge lives in people's heads and Slack threads, architecture drift is invisible, and onboarding becomes painful. ADRs are the answer to "why did we build it this way?" — six months from now when no one remembers.

## When to use

- A technology choice has been made or is under discussion and needs a permanent record
- A new external dependency (library, service, protocol) is being introduced
- The team has debated an architectural approach and reached a conclusion
- An implementation deviated from the agreed design and the deviation needs justification
- Someone asks "why are we using X?" or "who decided this?" and the answer is not documented
- A decision is reversible but expensive to reverse — write it down now before it becomes implicit
- An ADR in Proposed status needs to be reviewed for completeness before being accepted

## When a decision warrants an ADR

Not every choice needs an ADR. Create an ADR when the decision:

- Affects the overall system architecture or the relationship between services
- Introduces a new external dependency (library, service, protocol)
- Defines or changes an API contract or integration pattern
- Has a meaningful security posture implication
- Is a departure from the established architecture principles
- Will be expensive or complex to reverse
- Has been the subject of significant debate between the team

Decisions that do NOT warrant an ADR: naming conventions, minor implementation details, choice between two functionally equivalent libraries, internal code organisation.

## When NOT to use

- Reviewing a full system design or proposal for principle violations and trade-offs → `architecture-review-governance`
- Automating the enforcement of the decision in CI (import boundaries, dependency budgets, drift checks) → `architecture-fitness`
- Capturing product-level goals, user stories, or non-functional requirements → `prd-creator`
- Synthesising multiple decisions and specs into the implementation design → `design-doc-generator`
- Writing the API or event schema the decision governs → `specification-driven-development`
- Tracking a risk surfaced by the decision (kill criteria, early warnings) → `technical-risk-management`

## Process

1. Confirm the decision is in scope for an ADR — use the "When a decision warrants an ADR" section above. If in doubt, write it: the cost of an unnecessary ADR is low; the cost of a missing one is high.
2. Determine the decision status: is it `Proposed` (still under discussion) or `Accepted` (already finalised)? Do not write a Proposed ADR as if it were decided.
3. Open `references/adr-template.md` and populate every field. Do not leave any field blank.
4. Write the context section first — minimum 3 sentences covering the situation, the constraint or pressure forcing the decision, and relevant background. If you cannot write 3 sentences of context, you do not yet understand the decision well enough to record it.
5. Write the decision statement: one or two sentences, active voice, specific. "We will use Apache Kafka on Confluent Cloud" not "use a message queue".
6. Write the alternatives section honestly. If there was only one viable option or the decision was externally forced, say so. Do not invent fake alternatives to fill the table.
7. Write the consequences: what becomes easier, what becomes harder, what new risks exist. If your consequences section has no negatives, it is incomplete.
8. Assign an ADR number (sequential from the last in `docs/adr/`) and set the review date.
9. Save the ADR as `docs/adr/ADR-NNN-kebab-title.md`.
10. Append the execution log entry.

## Required ADR fields

Every ADR must contain all of the following. Incomplete ADRs are not accepted.

1. **Number and title** — Sequential number (ADR-NNN) and a concise title describing the decision made (not the question — write "Use PostgreSQL as the primary data store" not "Database selection")

2. **Date** — When the decision was made (not when the ADR was written)

3. **Status** — One of: `Proposed` (under discussion), `Accepted` (decision finalised), `Deprecated` (no longer valid but not superseded), `Superseded by ADR-NNN` (replaced by a newer decision)

4. **Context** — What situation, constraint, or requirement forced this decision? What was the state of the system? What pressures existed? Write enough context that someone reading this 2 years later understands why this decision existed.

5. **Decision** — What was decided, stated precisely. "We will use X" not "We discussed X". Be specific enough that there is no ambiguity.

6. **Alternatives considered** — At least one genuine alternative with honest pros and cons. If the decision was obvious or forced by an external constraint, state that clearly rather than inventing fake alternatives. The goal is honest reasoning, not box-ticking.

7. **Consequences** — What becomes easier? What becomes harder? What new risks are introduced? What new constraints exist? What other decisions does this enable or constrain?

8. **Owner** — Who made or approved this decision (name, role)

9. **Review date** — When should this decision be re-evaluated? (e.g., after 6 months, at Phase 2 planning, when X changes)

## How to create an ADR

Use the template in `references/adr-template.md`. Populate every field. For alternatives, write honestly — if the decision was forced or obvious, say so rather than manufacturing fake options.

**Before writing the decision statement:** make sure the decision has actually been made. ADRs in `Proposed` status document ongoing discussions; ADRs in `Accepted` status document finalised decisions.

**The most common ADR writing mistakes:**
- Context is too brief — a two-sentence context leaves reviewers without enough information to evaluate the decision
- Alternatives are superficial — listing "Option A: use X" with "pros: it works" is not a genuine alternatives analysis
- Consequences focus only on benefits — every decision has costs and risks; if your consequences section has no negatives, it is incomplete
- The decision statement is vague — "use a message queue" instead of "use Apache Kafka on Confluent Cloud"

## How to update an ADR

ADRs are immutable records — do not edit an accepted ADR's decision. Instead:

- If the decision is being **reversed or replaced**: create a new ADR documenting the new decision, and update the old ADR's status to `Superseded by ADR-NNN`
- If the context has **changed materially**: create a new ADR that acknowledges the old one and explains what changed
- If the ADR has **factual errors**: correct the errors and note the correction with a date in a changelog section

## ADR numbering and storage

- Number ADRs sequentially: ADR-001, ADR-002, etc.
- Store ADRs in `docs/adr/` in version control
- File names: `ADR-NNN-short-title-in-kebab-case.md`
- No mandatory index file required — the directory listing is the index for a small team. Create `docs/adr/README.md` only if the ADR count grows beyond 20 and navigation becomes painful.

## Output format

When creating an ADR, produce it in this exact structure:

### ADR-[NNN]: [Title]

**Date:** [YYYY-MM-DD]
**Status:** [Proposed / Accepted / Deprecated / Superseded by ADR-NNN]
**Owner:** [Name, Role]
**Review date:** [date or trigger condition]

### Context
[Minimum 3 sentences. Cover: what the situation is, what is forcing a decision, what constraints exist.]

### Decision
[One or two sentences stating precisely what was decided.]

### Alternatives considered

| Alternative | Pros | Cons |
|-------------|------|------|
| [Option A — the chosen option] | | |
| [Option B] | | |
| [Option C] | | |

### Consequences

**What becomes easier:**
- [consequence 1]

**What becomes harder or more constrained:**
- [consequence 1]

**New risks introduced:**
- [risk 1]

**Dependencies created:**
- [dependency 1]

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] architecture-decision-records — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] architecture-decision-records — ADR-007: chose Kafka over NATS for event bus
[2026-04-20] architecture-decision-records — ADR-008: deviation from DESIGN.md — async instead of sync
```

---

## Reference files

- `references/adr-template.md` — Complete ADR template with field instructions and a full worked example
- `references/adr-index-template.md` — Index format for maintaining a navigable ADR list
- `references/adr-good-vs-bad.md` — Three pairs of good vs bad ADRs with annotations
