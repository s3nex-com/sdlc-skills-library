# SDLC pipeline status dashboard template

Copy this to `docs/sdlc-status.md` in your project at Stage 0. Update it at every stage gate. This is the single source of truth for where the pipeline is at any point in time.

---

```markdown
# SDLC pipeline status

**Feature:** [Feature name]
**PRD title:** [PRD title once created]
**Pipeline started:** [YYYY-MM-DD]
**Last updated:** [YYYY-MM-DD]
**Status:** In progress / Blocked / Complete

---

## Stage summary

| Stage | Name | Status | Gate date | Notes |
|-------|------|--------|-----------|-------|
| 0 | Initialisation | Complete | [date] | |
| 1 | PRD creation | Not started | — | |
| 2 | Requirements tracing | Not started | — | |
| 3 | Specification | Not started | — | |
| 4 | Design document | Not started | — | |
| 5 | Implementation | Not started | — | |
| 6 | Acceptance testing | Not started | — | |
| 7 | Security gate | Not started | — | |
| 8 | PR and merge | Not started | — | |
| 9 | Documentation | Not started | — | |

**Stage status values:** Not started / In progress / Blocked / Gate passed / Skipped (reason) / Complete

---

## Current stage

**Stage:** [N]
**Stage name:** [Name]
**Status:** [In progress / Blocked]
**Started:** [YYYY-MM-DD]

**Active work:**
[1-2 sentences describing what is being worked on right now]

**Blocker (if any):**
[Description of blocker, owner, and expected resolution date — or "None"]

**Next action:**
[Specific next step — actionable, not vague]

---

## Stage details

### Stage 1: PRD creation

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]

**Output:** [Link to docs/PRD.md or —]
**PRD version:** [1.0 / —]
**Approval:** [Names who approved or —]

**Gate items:**
- [ ] All 11 PRD sections complete
- [ ] Goals measurable
- [ ] NFRs defined (minimum 4)
- [ ] No open questions in goals, requirements, or metrics sections
- [ ] Product owner approved
- [ ] Engineering lead approved
- [ ] Partner company lead approved

**Notes:**
[Any notable context about this stage — decisions made, issues encountered]

---

### Stage 2: Requirements tracing

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** requirements-tracer

**Output:** [Link to docs/traceability-matrix.md or —]
**Stories created:** [N stories or —]
**Feature files:** [N files in tests/acceptance/ or —]

**Gate items:**
- [ ] Every FR-NNN has at least one user story
- [ ] Every story has BDD acceptance criteria
- [ ] Traceability matrix complete
- [ ] Partner handshake complete (both companies agree on requirements)

**Stories list:**
| Story ID | Title | Status | Feature file |
|----------|-------|--------|-------------|
| ST-001 | | — | |
| ST-002 | | — | |

**Notes:**

---

### Stage 3: Specification

**Status:** [Not started / In progress / Gate passed / Skipped — [reason] / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** specification-driven-development

**Output:** [List of spec files or —]
**Freeze date:** [YYYY-MM-DD or —]

**Gate items:**
- [ ] All API surfaces have a spec
- [ ] validate_openapi.py passes for all REST specs
- [ ] Contract review checklist complete
- [ ] Contract freeze signed by both companies
- [ ] ADRs created for significant API design decisions

**Spec files:**
| File | Format | Status | Notes |
|------|--------|--------|-------|
| `specs/[filename]` | OpenAPI 3.0 | Draft / Frozen | |

**Notes:**

---

### Stage 4: Design document

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** design-doc-generator

**Output:** [Link to docs/DESIGN.md or —]
**Architecture review:** [Date + reviewer name or —]
**Security review (STRIDE):** [Date + reviewer name or —]

**Gate items:**
- [ ] All 11 design sections complete
- [ ] Every story covered by a data flow
- [ ] Every NFR has a design mechanism
- [ ] No unresolved DQ items in Section 11 (or all have owners + deadlines)
- [ ] Architecture review sign-off obtained
- [ ] STRIDE threat model complete

**Open design questions:**
| DQ | Question | Owner | Deadline | Status |
|----|----------|-------|----------|--------|
| DQ-001 | | | | Open / Resolved |

**Notes:**

---

### Stage 5: Implementation

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** code-implementer

**Output:** [Link to docs/implementation-status.md or —]

**Phase progress:**
| Phase | Name | Status | Gate passed |
|-------|------|--------|-------------|
| 1 | | Not started | No |
| 2 | | Not started | No |

**Gate items:**
- [ ] All implementation tasks complete
- [ ] Unit tests pass, zero failures
- [ ] Integration tests pass, zero failures
- [ ] Coverage meets threshold
- [ ] All deviations have approved ADRs

**Current phase tasks:**
[Link to docs/implementation-status.md for detail]

**Notes:**

---

### Stage 6: Acceptance testing

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** executable-acceptance-verification

**Output:** [Link to acceptance sign-off document or —]

**Acceptance results:**
| Story | Scenarios | Passing | Sign-off |
|-------|-----------|---------|---------|
| ST-001 | N | N | Yes / No |

**Gate items:**
- [ ] All BDD scenarios pass, zero failures
- [ ] Every story has at least one passing scenario
- [ ] Acceptance sign-off document produced and signed
- [ ] Traceability matrix complete (test links populated)

**Notes:**

---

### Stage 7: Security gate

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** security-audit-secure-sdlc

**Gate items:**
- [ ] Gate 1 (STRIDE) — sign-off reference: [doc/ADR link]
- [ ] Gate 2 (secure coding) — sign-off reference: [implementation-status.md link]
- [ ] Gate 3 (SAST) — result: [PASS / N findings addressed]
- [ ] Gate 4 (dependency scan) — result: [PASS / N CVEs addressed]
- [ ] Secret scanning — result: PASS

**SAST findings:**
| ID | Severity | Finding | Resolution |
|----|----------|---------|-----------|
| | | | |

**Notes:**

---

### Stage 8: PR and merge

**Status:** [Not started / In progress / Gate passed / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** pr-merge-orchestrator

**PR details:**
| Item | Value |
|------|-------|
| PR number | [#NNN or —] |
| PR title | [title or —] |
| PR URL | [link or —] |
| Reviewers | [names or —] |
| Merge date | [date or —] |
| Release tag | [vX.Y.Z or —] |

**Gate items:**
- [ ] Pre-merge checklist complete (all gates pass)
- [ ] Required approvals obtained
- [ ] Merged to main
- [ ] CI green on main after merge
- [ ] Release tag created
- [ ] Stakeholders notified (if cross-company)

**Notes:**

---

### Stage 9: Documentation

**Status:** [Not started / In progress / Complete]
**Gate date:** [YYYY-MM-DD or —]
**Skill:** documentation-system-design

**Gate items:**
- [ ] Runbooks updated/created for all new P1/P2 scenarios
- [ ] C4 diagrams updated (if new components added)
- [ ] API usage guide updated (if new endpoints added)
- [ ] Operational handover document updated (if applicable)
- [ ] Documentation quality checklist complete

**Documentation changes:**
| Document | Change type | Status |
|----------|------------|--------|
| [filename] | New / Updated | Draft / Complete |

**Notes:**

---

## ADRs created in this pipeline

| ADR | Title | Stage created | Status |
|-----|-------|--------------|--------|
| ADR-NNN | [Title] | Stage N | Accepted |

---

## Blockers log

| Stage | Blocker | Raised | Owner | Resolved |
|-------|---------|--------|-------|---------|
| [N] | [Description] | [date] | [Name] | [date or open] |

---

## Pipeline complete

**Completion date:** [YYYY-MM-DD or —]
**Release:** [vX.Y.Z or —]
**Total pipeline duration:** [N days]
**Stories delivered:** [N of N]
**Outstanding items:** [None / list]
```
