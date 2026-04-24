# Implementation plan template

Copy and fill this template for each implementation phase. Maintain it at `docs/implementation-status.md`. Update it as tasks are completed — this is the live source of truth for implementation progress.

---

```markdown
# Implementation plan and status

**Feature:** [Feature name]
**PRD:** [link to PRD.md]
**Design doc:** [link to DESIGN.md]
**Started:** [YYYY-MM-DD]
**Last updated:** [YYYY-MM-DD]

---

## Phase summary

| Phase | Name | Status | Gate passed | Start date | Complete date |
|-------|------|--------|-------------|-----------|---------------|
| 1 | [Name] | Not started / In progress / Complete | Yes / No | | |
| 2 | [Name] | Not started | No | | |

**Current phase:** Phase [N]
**Current blocker:** None / [Description]

---

## Phase 1: [Phase name]

**Scope:** [2-3 sentences from DESIGN.md section 10]
**Prerequisites:** [What must exist before Phase 1 starts]
**Stories:** ST-NNN, ST-NNN

### Tasks

#### Task 1.1: [Component name — what specifically to implement]

**Status:** Not started / In progress / Complete / Blocked

**Description:**
[What exactly will be built in this task — specific enough that a different engineer could pick it up]

**Spec references:**
- API: `specs/[filename]` — endpoints: [list]
- Schema: `specs/[filename]` — schemas: [list]

**Story references:**
- ST-NNN: [Story title] — acceptance criterion: [link to feature file]

**Implementation order:**
1. [Step — e.g., "Create database migration for devices table"]
2. [Step — e.g., "Implement repository layer (DeviceRepository)"]
3. [Step — e.g., "Implement service layer (DeviceService)"]
4. [Step — e.g., "Implement HTTP handler (POST /v1/devices)"]
5. [Step — e.g., "Write unit tests for each layer"]
6. [Step — e.g., "Write integration test: handler + DB"]

**Dependencies:**
- [Task N.N must be complete before this task can start]
- [External: [description of external dependency]]

**Test stubs to write alongside:**

| Test name | Type | File path | Story |
|-----------|------|-----------|-------|
| TestRegisterDevice_HappyPath | Unit | `services/device_test.go` | ST-001 |
| TestRegisterDevice_DuplicateDevice | Unit | `services/device_test.go` | ST-001 |
| TestDeviceHandler_Register_Integration | Integration | `handlers/device_handler_test.go` | ST-001 |
| Feature: Device registration | Acceptance | `tests/acceptance/device_registration.feature` | ST-001 |

**Security gate:**
- [ ] Input validation applied (fields: [list the fields that need validation])
- [ ] Authentication required (mechanism: [JWT / API key / etc.])
- [ ] No SQL injection vectors (parameterised queries used throughout)
- [ ] Sensitive fields not logged or returned in error responses

**Completion criteria:**
- [ ] All steps above complete
- [ ] All test stubs above implemented and passing
- [ ] Security gate items checked
- [ ] Code reviewed by at least one other engineer
- [ ] `implementation-status.md` updated

**Completed:** [date] / In progress since: [date] / Blocked since: [date]

**Notes:**
[Any deviations from the design doc, decisions made during implementation, ADR references]

---

#### Task 1.2: [Next component]

[Repeat Task structure above]

---

### Phase 1 gate

Run at the end of Phase 1 before starting Phase 2.

- [ ] All Phase 1 tasks have status "Complete"
- [ ] Unit tests pass: `[test command]` — [N] tests, 0 failures
- [ ] Integration tests pass: `[test command]` — [N] tests, 0 failures
- [ ] Coverage meets threshold: [N]% (threshold: [N]%)
- [ ] Acceptance scenarios for Phase 1 stories pass: ST-NNN ✓, ST-NNN ✓
- [ ] Security checklist applied to all Phase 1 components
- [ ] Phase 1 components can be deployed without breaking existing functionality
- [ ] Design doc deviations documented (ADR references: [list or "none"])

**Gate result:** PASS / FAIL — [notes]
**Gate date:** [date]

---

## Phase 2: [Phase name]

**Status:** Not started (waiting for Phase 1 gate)

[Repeat Phase structure above when Phase 1 is complete]

---

## Deviations log

Record any deviation from DESIGN.md here. Every deviation must have an ADR or a documented reason.

| Task | Deviation | Reason | ADR | Date |
|------|-----------|--------|-----|------|
| [Task ID] | [What differs from the design] | [Why] | ADR-NNN / None (minor) | [date] |

---

## Blockers log

| Task | Blocker | Raised | Owner | Resolution |
|------|---------|--------|-------|-----------|
| [Task ID] | [Description] | [date] | [Name] | [Resolution or "open"] |
```
