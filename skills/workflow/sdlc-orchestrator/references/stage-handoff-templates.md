# Stage handoff templates

These templates define the exact artifacts that pass between each stage. Use them to verify that a stage is complete before starting the next one, and to brief the next skill on what it is receiving.

Each template is a "handoff checklist" — both an output verification for the sending stage and an input verification for the receiving stage.

---

## Stage 1 → Stage 2 handoff (PRD → Requirements tracing)

**Sending skill:** prd-creator
**Receiving skill:** requirements-tracer

### What to hand off

```
Stage 1 → Stage 2 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Artifacts:
  [✓] docs/PRD.md — approved, version [1.0]

PRD summary for requirements-tracer:
  Functional requirements: FR-001 through FR-NNN ([N] total)
  User personas: [Persona 1], [Persona 2]
  Key NFRs for test criteria: [NFR-001: latency], [NFR-002: availability]
  Constraints relevant to stories: [list key constraints]

Instructions for requirements-tracer:
  - Decompose all FR-NNN requirements into epics, features, and user stories
  - Write BDD Given/When/Then for each story
  - NFR-NNN list is provided for later use by design-doc-generator — flag any NFRs
    that will need testable acceptance criteria (e.g., performance NFRs → performance acceptance tests)
  - Open questions from PRD section 11: [OQ-001, OQ-002] — these are unresolved;
    flag any story that depends on them as "blocked on OQ-NNN"
```

### Receiving skill verification

Before starting Stage 2, confirm:
- [ ] `docs/PRD.md` exists and is readable
- [ ] PRD version and approval date noted
- [ ] FR list extracted and counted
- [ ] PRD quality checklist was run (not just "approved by stakeholders")

---

## Stage 2 → Stage 3 handoff (Requirements → Specification)

**Sending skill:** requirements-tracer
**Receiving skill:** specification-driven-development

### What to hand off

```
Stage 2 → Stage 3 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Artifacts:
  [✓] docs/traceability-matrix.md
  [✓] tests/acceptance/*.feature ([N] files, [N] stories total)
  [✓] Story list: ST-001 through ST-NNN

API surfaces implied by stories (input for spec design):
  - ST-001, ST-003, ST-007 require: POST /devices, GET /devices/{id}
  - ST-004 requires: DELETE /devices/{id}
  - ST-009 requires: event publication when device status changes (AsyncAPI)
  - ST-011, ST-012 require: gRPC service for telemetry ingestion

NFRs from PRD that must be reflected in the spec:
  - NFR-001: API response time → add latency SLO note to spec header
  - NFR-004: Security → all endpoints must require [auth mechanism]

Open questions that may affect the spec:
  - OQ-003 (unresolved): Does the partner company consume our API or do we consume theirs?
    → If unresolved before spec design: design both sides and freeze only the agreed side

Instructions for specification-driven-development:
  - Design API contracts for all surfaces listed above
  - Do not implement before the spec is agreed
  - Use contract freeze process before passing to Stage 4
```

### Receiving skill verification

Before starting Stage 3, confirm:
- [ ] Traceability matrix exists and is readable
- [ ] All API surfaces have been identified (map each story to an API surface)
- [ ] NFR constraints for the spec are noted
- [ ] Open questions that could change the spec are flagged

---

## Stage 3 → Stage 4 handoff (Specification → Design)

**Sending skill:** specification-driven-development
**Receiving skill:** design-doc-generator

### What to hand off

```
Stage 3 → Stage 4 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Artifacts:
  [✓] specs/device-api.yaml — OpenAPI 3.0, frozen [date]
  [✓] specs/telemetry.proto — Protobuf, frozen [date]
  [✓] specs/device-events.asyncapi.yaml — AsyncAPI, frozen [date]
  [✓] Contract review checklist — complete
  [✓] Contract freeze sign-off — [names, date]

ADRs created during spec design:
  - ADR-007: REST vs gRPC for device management API
  - ADR-008: Async event schema design

Constraints for design-doc-generator:
  - The spec defines the external API surface — the internal design must satisfy it
  - Security scheme: [Bearer JWT — defined in spec] — design must implement this
  - Error schema: [RFC7807 Problem Details] — all components must return this format

Instructions for design-doc-generator:
  - Reference spec files in DESIGN.md Section 5 — do not duplicate schemas
  - Use spec schemas to derive data model entities for DESIGN.md Section 6
  - ADR-007 and ADR-008 must be referenced in the relevant design sections
  - Architecture review is required before DESIGN.md is approved — schedule it
```

### Receiving skill verification

Before starting Stage 4, confirm:
- [ ] All spec files are present and frozen (not draft)
- [ ] `validate_openapi.py` has been run on all OpenAPI specs
- [ ] ADR index is up to date with spec-related decisions
- [ ] Architecture reviewer is identified and scheduled

---

## Stage 4 → Stage 5 handoff (Design → Implementation)

**Sending skill:** design-doc-generator
**Receiving skill:** code-implementer

### What to hand off

```
Stage 4 → Stage 5 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Artifacts:
  [✓] docs/DESIGN.md — approved [date], version [1.0]
  [✓] Architecture review sign-off — [reviewer, date]
  [✓] STRIDE threat model — [reviewer, date]
  [✓] specs/ — all spec files (frozen)
  [✓] tests/acceptance/*.feature — [N] feature files
  [✓] docs/traceability-matrix.md

DESIGN.md section 10 phase plan:
  Phase 1: [Name] — Stories: ST-001, ST-002, ST-003
  Phase 2: [Name] — Stories: ST-004, ST-005
  Phase 3: [Name] — Stories: ST-006, ST-007

Security requirements for implementer (from STRIDE):
  - All endpoints require JWT auth (Gate 2 — apply at handler level)
  - Tenant isolation required on all DB queries (Gate 2 — parameterise by tenant_id)
  - Device ID must be validated as UUID format (Gate 2 — input validation)

Open design questions (DQ) that must be resolved before affected tasks:
  - DQ-001: [Question] — owner: [name] — deadline: [date] — affects: Phase 2, Task 2.3

Instructions for code-implementer:
  - Implement phases in order — do not start Phase 2 until Phase 1 gate passes
  - Every task must reference its story IDs (for traceability matrix completion)
  - Spec compliance is mandatory — do not implement beyond or different from the spec
  - Security checklist must be applied per task, not per phase
```

### Receiving skill verification

Before starting Stage 5, confirm:
- [ ] `docs/DESIGN.md` exists, is approved, and has an architecture review sign-off
- [ ] STRIDE threat model reference exists
- [ ] All spec files are present
- [ ] All BDD feature files are present
- [ ] Phase plan (Section 10) is understood and tasks can be derived from it
- [ ] DQ items that block Phase 1 are resolved (DQ items for later phases may be open)

---

## Stage 5 → Stage 6 handoff (Implementation → Acceptance testing)

**Sending skill:** code-implementer
**Receiving skill:** executable-acceptance-verification

### What to hand off

```
Stage 5 → Stage 6 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Artifacts:
  [✓] Implemented code (all phases complete)
  [✓] docs/implementation-status.md — all tasks Complete
  [✓] Unit tests: [N] passing
  [✓] Integration tests: [N] passing
  [✓] Coverage: [N]% (threshold: [N]%)

Stories implemented:
  ST-001 ✓ — acceptance scenario: tests/acceptance/device_registration.feature:line 5
  ST-002 ✓ — acceptance scenario: tests/acceptance/device_retrieval.feature:line 3
  [...]

How to run the acceptance test suite:
  [command — e.g., "pytest tests/acceptance/ -v --tags=@device-management"]

Deviations from design doc:
  - Task 1.3: [deviation] — ADR-015 created
  - None for other tasks

Security gate status:
  - Gate 1 (STRIDE): ✓ — ADR-NNN reference
  - Gate 2 (secure coding): ✓ — implementation-status.md per-task sign-offs
  - Gate 3 (SAST): not yet run — will run at Stage 7

Instructions for executable-acceptance-verification:
  - Run all feature files in tests/acceptance/
  - For each failing scenario: determine if it is an implementation bug or an acceptance
    criterion error before escalating
  - Produce the formal acceptance sign-off document on completion
  - Update the traceability matrix with test links
```

### Receiving skill verification

Before starting Stage 6, confirm:
- [ ] Implementation status document shows all tasks Complete
- [ ] Unit and integration tests pass (run them to verify — do not rely on the status doc alone)
- [ ] BDD feature files are present for all stories
- [ ] Test run command is documented and works

---

## Stage 6 → Stage 7 handoff (Acceptance → Security gate)

**Sending skill:** executable-acceptance-verification
**Receiving skill:** security-audit-secure-sdlc

### What to hand off

```
Stage 6 → Stage 7 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Artifacts:
  [✓] Acceptance test report — [N] scenarios, 0 failures
  [✓] Formal acceptance sign-off — signed by [name, date]
  [✓] docs/traceability-matrix.md — complete (all links populated)

Stories verified:
  ST-001: [N] scenarios, all pass ✓
  ST-002: [N] scenarios, all pass ✓
  [...]

For security gate (Stage 7):
  Gate 1 reference: STRIDE threat model at [docs/security/stride-analysis.md]
  Gate 2 reference: implementation-status.md (per-task security gate sign-offs)
  Gate 3: SAST to be run now — tool: [Semgrep / Snyk Code / etc.]
  Gate 4: Dependency scan to be run now — tool: [Snyk / OWASP DC / etc.]
```

### Receiving skill verification

Before starting Stage 7, confirm:
- [ ] Acceptance sign-off document exists and is signed
- [ ] Gate 1 and Gate 2 references are present (not re-doing them — verifying they were done)
- [ ] Tooling for Gate 3 (SAST) and Gate 4 (dependency scan) is available

---

## Stage 7 → Stage 8 handoff (Security → PR/merge)

**Sending skill:** security-audit-secure-sdlc
**Receiving skill:** pr-merge-orchestrator

### What to hand off

```
Stage 7 → Stage 8 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Security gate results:
  Gate 1 (STRIDE): ✓ — [doc reference]
  Gate 2 (secure coding): ✓ — [implementation-status reference]
  Gate 3 (SAST): ✓ — [scan date], [N] findings, all addressed — [findings report if any]
  Gate 4 (dependency scan): ✓ — [scan date], no Critical CVEs
  Secret scanning: ✓ — clean

For PR creation:
  Security sign-off text for PR description:
  "STRIDE: ADR-NNN | Secure coding: implementation-status.md Phase N | SAST: [date] clean | Deps: [date] clean"

Stories in scope for this PR:
  [ST-NNN list]

Release tag target:
  v[M].[N].[P] (reason: [minor — new functionality])

Required reviewers:
  - [Name] (Senior engineer — code review)
  - [Name] (Security reviewer — new auth surface)
```

### Receiving skill verification

Before starting Stage 8, confirm:
- [ ] All four security gates have sign-offs
- [ ] CI is green on the implementation branch
- [ ] Pre-merge checklist has been run (from pr-merge-orchestrator)

---

## Stage 8 → Stage 9 handoff (PR/merge → Documentation)

**Sending skill:** pr-merge-orchestrator
**Receiving skill:** documentation-system-design

### What to hand off

```
Stage 8 → Stage 9 handoff

Feature: [Name]
Handoff date: [YYYY-MM-DD]

Merge details:
  PR number: #NNN
  PR title: [title]
  Merged to: main
  Release tag: v[M].[N].[P]
  Merge date: [YYYY-MM-DD]

Documentation updates required (from PR description and DESIGN.md):

New components (require C4 diagram update):
  - [Component name]: [what it does — one sentence]

New API endpoints (require API guide update):
  - POST /v1/devices
  - GET /v1/devices/{id}
  - DELETE /v1/devices/{id}

New operational scenarios (require runbook creation/update):
  - Device registration failure (error: duplicate device_id)
  - Device status update failure (Kafka consumer lag)

Configuration changes (update operational guide):
  - DEVICE_TIMEOUT_MS: new variable, controls registration timeout

References:
  DESIGN.md: docs/DESIGN.md
  API spec: specs/device-api.yaml
  ADRs: ADR-007, ADR-012

Instructions for documentation-system-design:
  - Do not rewrite documentation that was not affected by this change
  - Update or add; do not delete existing content without confirming it is obsolete
  - Run documentation quality checklist before marking Stage 9 complete
```

### Receiving skill verification

Before starting Stage 9, confirm:
- [ ] PR merge confirmed (check `git log main --oneline`)
- [ ] List of new components, endpoints, and operational scenarios is available
- [ ] Existing documentation is read before updating (do not overwrite without reading)
