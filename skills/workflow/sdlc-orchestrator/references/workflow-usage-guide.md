# SDLC orchestrator: complete usage guide

This guide explains how to use the SDLC orchestrator skill in every scenario you will encounter. Read the relevant section for your situation.

---

## Overview

The SDLC orchestrator manages the following pipeline:

```
Stage 0: Initialise
Stage 1: PRD creation          → PRD.md
Stage 2: Requirements          → traceability-matrix.md, feature files
Stage 3: Specification         → specs/*.yaml / *.proto / *.asyncapi.yaml
Stage 4: Design document       → DESIGN.md
Stage 5: Implementation        → code + tests + implementation-status.md
Stage 6: Acceptance testing    → acceptance sign-off
Stage 7: Security gate         → security gate sign-off
Stage 8: PR and merge          → merged PR + release tag
Stage 9: Documentation         → updated runbooks, diagrams, API guides
```

The orchestrator does not replace the individual skills — it tells you which skill to use, when, what to pass into it, and what to verify before moving on.

---

## Invocation patterns

### Pattern 1: Start a new feature from scratch

**When:** You have an idea, a feature request, or a problem statement and no other artifacts.

**How to invoke:**
```
User: start a new feature — [description of what you want to build]
```

**What happens:**
1. The orchestrator records the feature description
2. Initialises `docs/sdlc-status.md`
3. Invokes `prd-creator` Mode A (interactive discovery)
4. Guides you through each stage gate

**Tip:** The more context you provide in the initial description, the faster Stage 1 (PRD creation) goes. Include: who the users are, what problem it solves, and any hard constraints you already know.

---

### Pattern 2: Start with an existing PRD

**When:** You have an approved PRD and want to enter the pipeline at Stage 2.

**How to invoke:**
```
User: we have an approved PRD at docs/PRD.md — start the pipeline from requirements tracing
```

**What happens:**
1. The orchestrator reads `docs/PRD.md`
2. Runs it through the `prd-creator` quality checklist (Mode C validation)
3. If it passes: initialises the pipeline at Stage 2
4. If it fails: returns the gap report and asks you to address it before proceeding

**Important:** The orchestrator will validate the PRD even if you say it's approved. The gate exists because informally approved PRDs often have quality problems that cause downstream rework.

---

### Pattern 3: Start with specs already frozen

**When:** Specs have been agreed with a partner company and you need to design and implement against them.

**How to invoke:**
```
User: specs are frozen in specs/ — we need the design doc and implementation, we have a PRD at docs/PRD.md
```

**What happens:**
1. Validates `docs/PRD.md` (Stage 1 gate)
2. Validates that user stories exist (or invokes `requirements-tracer` to create them)
3. Validates the spec files using `validate_openapi.py`
4. Skips Stage 3 (specification) — marks it as "Skipped — pre-existing frozen specs"
5. Proceeds to Stage 4 (design document)

---

### Pattern 4: Resume a paused pipeline

**When:** Work was started and stopped, and you need to pick it up where it left off.

**How to invoke:**
```
User: resume the sdlc pipeline for the [feature name] feature
```

**What happens:**
1. Reads `docs/sdlc-status.md`
2. Reports the current stage and its status
3. Reports what was last completed and what the current blocker is (if any)
4. Resumes from the current stage

**If `docs/sdlc-status.md` does not exist:** The orchestrator asks you to describe where you are in the pipeline so it can reconstruct the status and create the file.

---

### Pattern 5: Check pipeline status

**When:** You want to know where the pipeline is without resuming it.

**How to invoke:**
```
User: what stage are we on?
User: sdlc status
User: where are we in the pipeline?
```

**What happens:**
The orchestrator reads `docs/sdlc-status.md` and produces a status report:

```
Pipeline: [Feature name]
Current stage: Stage 5 — Implementation
Status: In progress

Stage history:
  Stage 0: Complete
  Stage 1: Complete — PRD.md approved 2026-03-15
  Stage 2: Complete — 12 stories, matrix complete
  Stage 3: Complete — contracts frozen 2026-03-20
  Stage 4: Complete — DESIGN.md approved 2026-03-25
  Stage 5: In progress — Phase 1 complete, Phase 2 in progress
  Stage 6–9: Not started

Current phase: Phase 2 of 3
Current blocker: None
Next action: Complete Task 2.3 (event consumer), then run Phase 2 gate
```

---

### Pattern 6: Jump to a specific stage

**When:** You know exactly which stage to run and want to go there directly.

**How to invoke:**
```
User: jump to stage 4 — design doc
User: run the design doc stage, we have everything we need
User: start at implementation — design is approved
```

**What happens:**
1. The orchestrator verifies all prerequisite inputs for the target stage exist
2. If all prerequisites are present: begins the target stage
3. If any prerequisites are missing: lists what is missing and what upstream stage produces each item

**Prerequisite map:**

| Target stage | Required inputs |
|---|---|
| Stage 2 (Requirements) | Approved `PRD.md` |
| Stage 3 (Specification) | `PRD.md` + traceability matrix |
| Stage 4 (Design) | `PRD.md` + traceability matrix + frozen specs |
| Stage 5 (Implementation) | Approved `DESIGN.md` + frozen specs + BDD feature files |
| Stage 6 (Acceptance) | Implemented code + BDD feature files |
| Stage 7 (Security) | Implemented code + Stage 4 STRIDE model |
| Stage 8 (PR/merge) | Stages 6 and 7 sign-offs + passing CI |
| Stage 9 (Docs) | Merged PR + `DESIGN.md` |

---

### Pattern 7: Re-run a stage after a change

**When:** Something changed upstream (the PRD was updated, a spec changed, the design was revised) and you need to re-run a downstream stage.

**How to invoke:**
```
User: the PRD changed — re-run from stage 2
User: the design was updated — re-run implementation for the affected components
User: a spec changed — re-run everything from stage 3
```

**What happens:**
1. The orchestrator identifies which stages are invalidated by the change
2. Resets those stages in `docs/sdlc-status.md` to "Not started" with a note explaining why
3. Asks you to confirm before resetting (a reset is not destructive — code is not deleted, but the gate status is cleared)
4. Begins the earliest invalidated stage

**Reset cascade rules:**

| Change | Stages reset |
|--------|-------------|
| PRD goals or NFRs changed | 2, 3, 4, 5, 6 |
| Story added or removed | 3, 4, 5, 6 |
| Spec endpoint added or changed | 4, 5, 6, 7 |
| Data model changed in design | 5, 6, 7 |
| Implementation bug found in acceptance | 5, 6 |
| Security finding requiring design change | 4, 5, 6, 7 |

---

### Pattern 8: Hotfix (bypass stages 1–4)

**When:** A bug in production needs to be fixed and the full pipeline is too slow.

**How to invoke:**
```
User: hotfix — bug in the device registration endpoint, start at stage 5
```

**What happens:**
1. The orchestrator creates a hotfix entry in `docs/sdlc-status.md` (separate from the main pipeline)
2. Skips Stages 1–4
3. Asks for: (a) what is broken, (b) what the expected behaviour is, (c) is there a failing test that reproduces it?
4. Guides you through Stage 5 (fix + test) → Stage 7 (security gate) → Stage 8 (PR/merge)
5. Documents any architectural implications as an ADR for post-fix review
6. Skips Stage 9 unless the hotfix changes operational behaviour

**Hotfix rule:** If the fix requires a design change (component interface change, data model change, new infrastructure), it is not a hotfix — it is an expedited feature. Run the full pipeline with accelerated gates.

---

## Stage gate reference

### How gates work

At each stage, the orchestrator presents the gate checklist and asks you to confirm each item. You must explicitly confirm or flag each item — the orchestrator does not assume items pass.

If an item fails:
1. The orchestrator marks the gate as FAIL with the specific failing item
2. Updates `docs/sdlc-status.md` with the failure and reason
3. Provides the next action to resolve the failure
4. Does NOT proceed to the next stage

If all items pass:
1. The orchestrator marks the gate as PASS with the date
2. Updates `docs/sdlc-status.md`
3. Presents the next stage and what is needed to begin it

### Gate summary reference

| Stage | Key gate items |
|---|---|
| 1 → 2 | All 11 PRD sections complete, goals measurable, NFRs defined, no open questions in goals/requirements/metrics |
| 2 → 3 | Every FR has a story, every story has BDD criteria, partner handshake complete |
| 3 → 4 | All API surfaces specced, validate_openapi passes, contracts frozen and signed |
| 4 → 5 | All 11 design sections complete, every story covered by a data flow, every NFR has a mechanism, architecture review signed, STRIDE complete |
| 5 → 6 | All tasks complete, unit + integration tests pass, coverage met, no open deviations without ADR |
| 6 → 7 | All BDD scenarios pass, acceptance sign-off produced, traceability matrix fully populated |
| 7 → 8 | SAST clean, dependency scan clean, secret scanning clean, all security gates signed off |
| 8 → 9 | PR merged to main, CI green on main, release tag created |
| 9 → Done | Runbooks updated, diagrams updated, API guide updated, quality checklist complete |

---

## File structure maintained by the orchestrator

```
docs/
  sdlc-status.md              ← Pipeline dashboard (maintained throughout)
  PRD.md                      ← Stage 1 output
  traceability-matrix.md      ← Stage 2 output
  DESIGN.md                   ← Stage 4 output
  implementation-status.md    ← Stage 5 output (task tracker)
  adr/
    README.md                 ← ADR index
    ADR-NNN-*.md              ← Individual ADRs

specs/
  *.yaml                      ← OpenAPI specs (Stage 3)
  *.proto                     ← Protobuf specs (Stage 3)
  *.asyncapi.yaml             ← AsyncAPI specs (Stage 3)

tests/
  acceptance/
    *.feature                 ← BDD feature files (Stage 2, executed at Stage 6)
```

The orchestrator creates `docs/sdlc-status.md` at Stage 0 and updates it at every gate. All other files are produced by the individual skills.

---

## Common mistakes and how to avoid them

### Mistake 1: Skipping the gate and moving forward anyway

**Why it happens:** The team is under time pressure and the gate "feels like a formality."
**What it causes:** Stage N+1 work is built on an incomplete foundation. When the gate item that was skipped turns out to matter (it usually does), all the N+1 work must be redone.
**Prevention:** The gate is not a formality. If you genuinely cannot pass a gate item, the answer is to escalate the blocker — not to skip the gate.

### Mistake 2: Treating the pipeline as sequential when work can overlap

**Why it happens:** Over-literal reading of the stage order.
**Reality:** Stages 2 and 3 can overlap. Design thinking (Stage 4) can begin while Stage 3 is finalising, as long as no design decisions are locked until the spec is frozen. The key constraint is that each stage's GATE must pass before the next stage's GATE.

### Mistake 3: Implementing scope that isn't in the design

**Why it happens:** Engineers see a natural extension of what they're implementing and add it.
**What it causes:** Untested code, scope creep, partner expectation mismatches, security surface expansion.
**Prevention:** `code-implementer` has a strict rule: implement only what `DESIGN.md` specifies. Extra scope requires a design doc update, which requires a gate.

### Mistake 4: Running Stage 9 (documentation) as an afterthought

**Why it happens:** The team considers the job done after the merge.
**What it causes:** Operational runbooks are out of date, on-call engineers cannot diagnose incidents with the new code, new engineers cannot onboard.
**Prevention:** The pipeline is not complete until Stage 9 is done. Track it in `docs/sdlc-status.md` and do not call the feature "shipped" until documentation is updated.

---

## Integrating with team processes

### Sprint planning

Map pipeline stages to sprint goals:
- Sprint 1: Stages 1–3 (PRD, requirements, specs)
- Sprint 2: Stage 4 (design)
- Sprint 3–N: Stage 5 (implementation, one phase per sprint ideally)
- Sprint N+1: Stages 6–8 (acceptance, security, PR/merge)
- Sprint N+2: Stage 9 (documentation) — often can run in parallel with the next feature's Stage 1

### Cross-company coordination

At each stage that produces a partner-facing artifact, use `stakeholder-sync` to deliver it:
- Stage 1 → 2: Share the approved PRD for partner sign-off
- Stage 3: Deliver spec for partner review and counter-sign
- Stage 4: Share design doc for partner architecture review
- Stage 8: Deliver release notification with verification instructions

### Multiple features in flight

If multiple features are in the pipeline simultaneously:
- Each feature has its own `docs/sdlc-status.md` (or sections within one file)
- The orchestrator tracks them separately
- When invoking, specify the feature name: "resume the sdlc pipeline for the [feature] feature"
