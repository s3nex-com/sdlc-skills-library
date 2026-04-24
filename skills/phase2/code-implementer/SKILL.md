---
name: code-implementer
description: >
  Activate when the user wants to implement code from a design document, break a
  technical design into ordered implementation tasks, generate code phase by phase
  following the DESIGN.md, write code that satisfies BDD acceptance criteria,
  implement APIs to their OpenAPI/Protobuf specs, or drive implementation with
  inline security and quality checkpoints. Also trigger for: "implement this",
  "write the code", "build it", "start coding", "implement the design", "code the
  feature", "implement phase 1", "write the service", "generate the implementation",
  "build from the design doc", "implement the spec".
---

# Code implementer

## Purpose

This skill drives code implementation from a completed and approved design document. It does not write code speculatively — it requires `DESIGN.md` as its primary input. Implementation is structured into phases (as defined in the design doc), with quality and security gates between each phase. The output is production-ready code with test stubs, not a prototype.

This skill is the execution engine for the SDLC pipeline. It takes all upstream decisions and translates them into running software.

---

## When to use

- An approved `DESIGN.md` exists and the team is ready to begin implementation (Tier 2)
- A small, well-scoped bug fix or enhancement needs to be implemented with tests alongside (Tier 1)
- The user says "implement this", "write the code", "build from the design doc", or "code the feature"
- A specific implementation phase in `DESIGN.md` is ready to start — all its dependencies are in place
- Implementation has been started and the team needs to pick up from where a previous session left off

## When NOT to use

- Reviewing code that has already been written — use `code-review-quality-gates`.
- Preparing an implemented branch for merge — use `pr-merge-orchestrator`.
- Designing the test strategy or test layers that the implementation must satisfy — use `comprehensive-test-strategy`.
- Writing executable BDD acceptance tests from the traceability matrix — use `executable-acceptance-verification`.
- Producing the `DESIGN.md` this skill consumes — use `design-doc-generator`.
- Building software that calls an LLM at runtime (prompt design, eval harness, RAG) — use `llm-app-development`.

---

## Prerequisites — choose your tier

Not all implementation tasks require the full upstream pipeline. Use the tier that matches the scope of work.

### Tier 1: Minimal (for small features, bug fixes, enhancements < 1 day of work)

| Required | Location | Notes |
|----------|----------|-------|
| Clear problem statement | In the task/issue or conversation | "What to build" and "what done looks like" must be unambiguous |
| Passing test suite (before you start) | CI or local | You must have a green baseline before making changes |
| Branch created | Git | Never implement directly on main |

When Tier 1 applies:
- A bug fix with a clear reproduction case
- Adding a new field to an existing API endpoint (no new service)
- Extending an existing function with a new case
- Refactoring within one component

**For Tier 1 work:** implement, write tests, verify tests pass, create PR. The gate is: tests pass, no regressions, PR description explains what and why.

---

### Tier 2: Full pipeline (for multi-phase features, new services, significant changes)

All of the following must exist and be approved before writing a single line of production code:

| Input | Location | Provided by |
|-------|----------|------------|
| `DESIGN.md` (approved) | `docs/` | design-doc-generator |
| `PRD.md` (approved) | `docs/` | prd-creator |
| Traceability matrix | `docs/` | requirements-tracer |
| API spec files (OpenAPI / Protobuf / AsyncAPI) | `specs/` | specification-driven-development |
| BDD feature files (acceptance criteria) | `tests/acceptance/` | executable-acceptance-verification |
| ADR index | `docs/adr/` | architecture-decision-records |

If any Tier 2 inputs are missing: **stop** and direct the user to the appropriate upstream skill. Implementation without a complete design creates rework that costs more time than producing the design first.

When Tier 2 applies:
- A new service or major new component
- A multi-sprint feature with multiple stories
- Any change that affects a public API, database schema, or integration boundary
- Anything with significant security implications

---

### Which tier?

When in doubt, ask: **"If this change is wrong, how long does it take to undo?"**
- Less than a day: Tier 1 is fine
- More than a day: Tier 2
- Changes a shared API or database schema: Tier 2 regardless of time estimate

---

## Process

### Step 1: Break the design into tasks

Read `DESIGN.md` section 10 (Implementation phases). For each phase, produce a task list:

```
Phase 1: [Phase name]
  Task 1.1: [Component name] — [what specifically to implement]
    Inputs: [data/events/requests this task receives]
    Outputs: [code artifacts produced]
    Story IDs: [ST-NNN from traceability matrix]
    Dependencies: [other tasks that must complete first]
    Test stubs: [list of tests to write alongside]
    Security gate: [which STRIDE threat to address]

  Task 1.2: ...
```

Rule: each task must be completable in a single session without requiring decisions not already captured in the design doc. If a task requires a design decision, raise it as a blocker before coding.

### Step 2: Verify task ordering

Tasks have dependencies. Before executing any task, verify:
- All dependency tasks are complete
- Required infrastructure is available (database, queues, etc.)
- Required external specs are frozen (no pending contract changes)

Do not start a task if its dependencies are not complete. Incomplete dependencies produce integration failures that cost more time to fix than waiting.

### Step 3: Implement task by task

For each task:

1. **Read the relevant spec section** — the exact endpoint, schema, or event definition
2. **Read the relevant story** — the BDD acceptance criteria that define done
3. **Implement to the spec** — not to assumptions; any deviation must create an ADR
4. **Write tests alongside** — not after; test stubs from the task list become real tests
5. **Run the security checklist** — apply `security-audit-secure-sdlc` secure coding standards
6. **Verify the acceptance criterion** — the task is not done until the BDD scenario passes

### Step 4: Phase gate before moving to next phase

At the end of each phase, verify before moving on:

- [ ] All tasks in the phase are complete
- [ ] Unit and integration tests pass for all new code
- [ ] Acceptance criteria for phase stories pass
- [ ] The phase does not break existing functionality
- [ ] All four security hard stops answered and passing for every task in this phase: input validation, auth check, no secrets in code, injection surface
- [ ] Documentation updated: API reference reflects any new/changed endpoints; README updated for new env vars or setup steps; runbook stub created for any new operational scenario introduced by this phase

**For small features (single phase or single task):** the gate is: tests pass, security checklist done, docs updated, one quick self-review. No ceremony required.

**For larger multi-phase features:** run the full gate between phases. Do not start phase N+1 until phase N has passed.

---

## Implementation standards

### Code quality rules (apply to every file written)

- **Naming:** Names must communicate intent. `deviceRegistrationHandler` not `handler1`. `validateDevicePayload` not `validate`.
- **Single responsibility:** Each function does one thing. If a function needs a comment to explain what it does, it is doing too much.
- **Error handling:** Every error path is explicit. No silent failures. No swallowed exceptions. Log the error with context; return a typed error or appropriate HTTP status.
- **No hardcoded values:** Configuration belongs in environment variables or config files. Never in source code.
- **No dead code:** Do not write code for hypothetical future requirements. Implement exactly what the design doc specifies.

### Test requirements (mandatory, not optional)

For every functional requirement implemented, write:

| Test type | Scope | When to write |
|-----------|-------|--------------|
| Unit test | Individual function/method logic | Alongside implementation |
| Integration test | Component interaction (e.g., handler + DB) | At end of each task |
| Contract test | API endpoint vs OpenAPI spec | For every new endpoint |
| Acceptance test | BDD scenario from feature file | Validates story "done" |

Coverage is not a vanity metric here — every BDD scenario in the feature files must have a corresponding passing acceptance test before the phase is complete.

### Spec compliance

Every API endpoint implemented must:
- Match the OpenAPI spec exactly (path, method, request body schema, response schema, status codes)
- Include spec-driven validation (reject requests that do not match the spec schema)
- Return documented error responses for documented error conditions

Use `validate_openapi.py` from `specification-driven-development` to verify spec compliance in CI.

### Security hard stops — answer inline, block the phase gate if any fail

These four checks are mandatory before any phase gate passes, in every mode. They are not cross-references to another skill — answer each item explicitly for every task before marking the task complete. A task is not done until all four are resolved.

| Check | When it applies | Pass condition |
|-------|----------------|---------------|
| **Input validation** | Every endpoint, handler, or function that receives external data | All inputs validated at the trust boundary; no raw external input reaches business logic or the database |
| **Auth check** | Every new route or API method | Authentication verified (token/session/key); authorisation applied (role/permission); no endpoint reachable without auth unless explicitly and intentionally public |
| **No secrets in code** | Any config, credential, token, or key reference | Zero hardcoded secrets; all secrets referenced exclusively through env vars or a secrets manager |
| **Injection surface** | Any DB query, shell command, or template render | Parameterised queries only — no string concatenation into SQL; shell commands use argument arrays — no string interpolation; templates use auto-escaping |

**For Nano mode:** these four items are the complete security gate. Answer them per task. The phase gate does not pass until all four are answered for every task in the phase.

**For Lean and above:** these four run inline during implementation. The full `security-audit-secure-sdlc` gate (SAST + SCA + secrets scan) runs additionally at Stage 4 before merge.

**If any item cannot be answered "pass" for a task:** the task is not complete. Do not mark it done. Raise it as a blocker. Do not proceed to the next task with an open security item.

---

## Handling deviations from the design

If implementation reveals that the design doc is incorrect, incomplete, or needs to change:

1. **Stop implementing** the affected component
2. **Document the deviation** — what the design says vs what reality requires
3. **Raise it explicitly** — do not silently implement something different from the design
4. **If the deviation is minor** (naming, implementation detail with no architectural impact): record it in the implementation notes and continue
5. **If the deviation is significant** (changes a component's interface, data model, or integration): create an ADR via `architecture-decision-records` and get it approved before continuing

Do not implement around a design problem. Fix the design.

---

## Output format

### Implementation task tracker

Maintain this file at `docs/implementation-status.md`:

```markdown
# Implementation status

**Phase:** [current phase name]
**Last updated:** [date]

## Phase 1: [name]

| Task | Status | Story IDs | Notes |
|------|--------|-----------|-------|
| 1.1 Component name | In progress / Complete / Blocked | ST-001, ST-002 | |
| 1.2 Component name | Not started | ST-003 | Blocked on Task 1.1 |

**Phase gate:** Not started / In progress / Passed

## Phase 2: [name]
...
```

### Per-task implementation notes

For each completed task, add a brief entry:

```markdown
## Task 1.1: [Component name] — completed [date]

**Implemented:** [What was built — 2-3 sentences]
**Spec compliance:** Verified — all endpoints match `specs/device-api.yaml`
**Tests written:** 12 unit, 3 integration, 2 acceptance (ST-001 ✓, ST-002 ✓)
**Deviations:** None | [description of any deviation and ADR reference]
**Security gate:** Passed — input validation, auth middleware applied
```

---

## Handoff to next stage

Once all implementation phases are complete:

1. Verify the implemented test suite satisfies the pyramid ratios defined in the test strategy (70% unit / 20% integration / 10% E2E)
2. Pass to `executable-acceptance-verification` — run full acceptance test suite and produce sign-off
3. Pass to `security-audit-secure-sdlc` — run final security gate before PR
4. Pass to `pr-merge-orchestrator` — create PR and manage the merge process
5. Implementation status doc becomes part of the PR description

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] code-implementer — [phase and description, e.g., "Phase 1 of 3 complete — event ingestion handler"]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] code-implementer — Tier 1: fixed connection pool exhaustion bug
[2026-04-20] code-implementer — Tier 2 Phase 1 of 3 complete — device registry client
[2026-04-21] code-implementer — Tier 2 Phase 2 of 3 complete — ingestion API handlers
[2026-04-21] code-implementer — Tier 2 Phase 3 complete — all phases done, ready for verification
```

---

## Reference files

- `references/implementation-plan-template.md` — Task breakdown template for each design phase
- `references/implementation-checklist.md` — Per-task quality and security checklist
- `references/task-dependency-guide.md` — How to order tasks correctly across components
