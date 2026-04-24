---
name: prd-creator
description: >
  Activate when the user wants to create a Product Requirements Document (PRD) from scratch,
  convert rough ideas or bullet points into a structured PRD, validate or improve an existing
  PRD, facilitate discovery sessions to extract requirements, review a PRD for completeness
  before it enters the development workflow, or prepare a PRD that will feed into the SDLC
  pipeline (requirements-tracer, specification-driven-development, design-doc-generator).
  Also trigger for: "write a PRD", "define the product", "what are we building", "capture
  requirements", "product spec", "feature definition", "we have an idea", "turn this into
  requirements", "requirements document", "product brief".
---

# PRD creator

## Purpose

A Product Requirements Document is the authoritative statement of what is being built, why it is being built, and what success looks like. Without a well-structured PRD, every downstream activity — specifications, design, implementation, testing — is operating on assumptions. This skill creates or validates PRDs that are precise enough to feed directly into the SDLC pipeline without ambiguity.

A PRD created by this skill is the canonical input to:
- `requirements-tracer` — for decomposing into epics, features, and BDD acceptance criteria
- `specification-driven-development` — for designing API contracts
- `design-doc-generator` — for producing the technical design

---

## When to use

- The team is starting a new feature and there is no written statement of what is being built
- Someone says "we have an idea" or "we need to add X" but the problem, goals, and success metrics are not yet written down
- An existing PRD needs to be validated before entering the pipeline (completeness, measurable goals, explicit non-goals)
- Raw material exists (Slack thread, meeting notes, bullet list of requirements) and needs to be structured into a proper PRD
- The scope of an existing PRD needs to change and the impact must be understood before work continues
- Goals or success metrics are vague and the team is about to start design work without a clear target
- The user asks "what are we building?" or "write a PRD"

## When NOT to use

- Decomposing an already-approved PRD into stories and BDD acceptance criteria → `requirements-tracer`
- Producing the technical `DESIGN.md` once the PRD exists → `design-doc-generator`
- Documenting a pure technical decision (technology choice, pattern, trade-off) with no product-facing change → `architecture-decision-records`
- Writing API contracts, schemas, or interface definitions → `specification-driven-development`
- Capturing delivery, technical, or external risks against the PRD → `technical-risk-management`
- Drafting stakeholder updates or status communications about the PRD → `stakeholder-sync`

---

## Two modes of operation

### Mode A: Create from scratch (interactive)

When the user has an idea, a problem statement, or rough notes but no structured PRD. The skill asks discovery questions (see `references/discovery-questions.md`), synthesises the answers, and produces a complete PRD.

Start with:
1. Ask the problem statement questions first — understand the pain before the solution
2. Ask user persona questions — who is affected and how
3. Ask goals and success metrics questions
4. Ask constraint and dependency questions
5. Draft the PRD and present it for review before finalising

Do not accept "we will define that later" for Goals, Non-Goals, or Success Metrics. These three sections are non-negotiable before the PRD is considered complete.

### Mode B: Structure from input

When the user provides raw material (bullet points, a Slack thread, meeting notes, an existing rough doc). Parse the input, map content to PRD sections, identify gaps, fill what can be inferred, flag what requires human input, and produce a structured PRD.

### Mode C: Validate an existing PRD

When the user provides a PRD and wants to verify it is complete and ready to enter the pipeline. Run the quality checklist from `references/prd-quality-checklist.md` and produce a gap report with required actions.

---

## PRD structure

A PRD has five core sections that are always required, and three extended sections that are added when the feature warrants them. Do not skip core sections. Do not add extended sections as filler.

### Core sections (always required)

#### 1. Problem statement
- What is the problem or opportunity?
- Who experiences it and in what context?
- What is the cost of not solving it?

#### 2. Goals
Specific, measurable outcomes this feature will achieve. Written as outcomes, not features.

**Good goal:** "Reduce device onboarding time from 45 minutes to under 5 minutes for 90% of users."
**Bad goal:** "Improve device onboarding."

Goals with no number and no verifiable condition are not goals — they are wishes. Rewrite them until they are testable.

#### 3. Non-goals
What this feature will NOT do. This prevents scope creep and misaligned expectations.

Every non-goal answers: "Is this something a reasonable person might expect this to do?" If yes, it belongs here.

#### 4. Non-functional requirements (NFRs)
Address the NFRs that actually matter for this feature. Do not fabricate NFRs to hit a minimum count — write the ones that will constrain the design.

Common NFRs to consider: performance (latency, throughput), availability, scalability, security, compliance, data retention.

Format each as a measurable statement:
- `NFR-001: The API must respond within 200ms at p99 under 1,000 concurrent requests.`
- `NFR-002: The system must achieve 99.9% uptime, measured monthly.`

#### 5. Success metrics
How will you know this feature succeeded after launch?
- Primary metric (the number that matters most)
- Measurement method (where does the data come from?)
- Evaluation timeline (e.g., "30 days post-launch")

---

### Extended sections (add when needed)

#### 6. Functional requirements
Add when the feature has multiple distinct behaviours that need to be tracked separately through the pipeline. Each requirement must be unambiguous, testable, and independently understandable.

Format: `FR-NNN: [Requirement statement]`

#### 7. User personas and use cases
Add when different user types interact with the feature differently, or when the feature is external-facing. One or two personas with a clear workflow is usually enough.

#### 8. Constraints and dependencies
Add when there are meaningful constraints that will affect the design: existing architecture, technology mandates, third-party dependencies, timeline, or regulatory requirements. Do not list constraints that are obvious from context.

---

### Open questions
If there are genuinely unresolved questions, capture them inline in the relevant section rather than in a separate section. Each must have an owner and a deadline. A PRD with unresolved goals or unresolved NFRs is not ready to proceed.

---

## PRD quality gate

Before a PRD exits this skill and enters the pipeline:

- All 5 core sections are present and complete
- Goals are measurable (contain a number or verifiable condition)
- Non-goals are non-trivial (not just "we won't do everything")
- NFRs reflect real constraints that will affect the design
- Success metrics name a specific data source and timeline
- No unresolved questions in goals, non-goals, or NFRs

---

## Output format

The PRD is produced as a structured markdown document named `PRD.md`. Place it in the project root or the agreed documentation directory.

```markdown
# PRD: [Feature/Product Name]

**Version:** 1.0
**Status:** Draft | Approved
**Author:** [Name]
**Date:** [YYYY-MM-DD]
**Related:** [ADRs, specs, design docs when they exist]

---

## 1. Problem statement
...

## 2. Goals
...

## 3. Non-goals
...

## 4. Non-functional requirements
...

## 5. Success metrics
...

<!-- Add sections 6–8 only when the feature warrants them -->
```

---

## Handoff to next stage

Once the PRD is approved:

1. Pass `PRD.md` to `requirements-tracer` to decompose into epics, features, stories, and BDD acceptance criteria
2. Pass NFRs (section 7) directly to `specification-driven-development` to inform API contract design
3. Pass constraints and dependencies (section 8) to `technical-risk-management` to seed the risk register

---

## Process

### Mode A (create from scratch)

1. Ask the problem statement questions first: what is the pain, who experiences it, what does it cost to leave it unsolved?
2. Ask user persona questions: who uses this, in what context, with what existing tools?
3. Ask goals questions: what does success look like in 30 days? What number will move?
4. Ask NFR questions: what are the latency, availability, security, or compliance constraints?
5. Synthesise answers into the 5-section PRD structure. Draft and present for review before finalising.
6. If the user deflects any core section with "we'll define that later" — push back. Goals, Non-goals, and Success Metrics are non-negotiable before the PRD is done.

### Mode B (structure from input)

1. Parse the raw input and map each piece to a PRD section.
2. Identify gaps: what is not answerable from the input?
3. Fill what can be inferred; flag what requires human input with `> **Open:** [question] — owner: [name]`.
4. Present the structured PRD and ask for confirmation before finalising.

### Mode C (validate existing PRD)

1. Run the quality gate checklist (below) against every section of the provided PRD.
2. For each failure, write a specific required action: what is wrong, what the fix is.
3. Produce a gap report. If there are no blockers, state the PRD is pipeline-ready.

### All modes

1. Run the PRD quality gate before declaring the PRD complete.
2. Confirm the handoff: the approved PRD goes to `requirements-tracer` next.
3. Append the execution log entry.

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] prd-creator — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] prd-creator — Mode A: created PRD for device telemetry ingestion feature
[2026-04-20] prd-creator — Mode B: structured PRD from meeting notes
[2026-04-20] prd-creator — Mode C: validated existing PRD; 3 gaps found
```

---

## Reference files

- `references/prd-template.md` — Full blank PRD template ready to fill in
- `references/discovery-questions.md` — Structured question bank for Mode A (interactive creation)
- `references/prd-quality-checklist.md` — Gate checklist to verify a PRD is pipeline-ready
