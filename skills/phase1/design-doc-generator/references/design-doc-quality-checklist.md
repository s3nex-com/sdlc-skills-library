# Design document quality checklist

Run this checklist before approving `DESIGN.md` and passing it to `code-implementer`. This is the gate between design and implementation — a weak design doc produces implementation drift, unplanned rework, and integration failures.

---

## Inputs verification

Before generating or reviewing a design doc, confirm these inputs were used:

- [ ] `PRD.md` (approved) was read and referenced
- [ ] Traceability matrix was read — all stories from the matrix are accounted for in the design
- [ ] API spec files are referenced in Section 5 (not duplicated — referenced)
- [ ] ADR index was consulted — existing decisions are not re-litigated in the design
- [ ] Architecture review findings (if any) are incorporated

---

## Section completeness

- [ ] Section 1 (Overview) — scope is explicit, exclusions are stated
- [ ] Section 2 (System context) — diagram present, all external systems and actors shown
- [ ] Section 3 (Component design) — every component has inputs, outputs, state, key logic, and failure modes
- [ ] Section 4 (Data flows) — one flow per user story (every ST-NNN has a corresponding flow)
- [ ] Section 5 (API contracts) — all API surfaces from the stories are listed with spec references
- [ ] Section 6 (Data models) — all entities owned by this system have schemas defined
- [ ] Section 7 (Infrastructure) — all compute, storage, and network resources are listed
- [ ] Section 8 (Security) — STRIDE categories addressed, auth/authz mechanism named
- [ ] Section 9 (Performance) — every NFR from PRD section 7 has a design mechanism
- [ ] Section 10 (Implementation phases) — phases are defined, each with exit criteria
- [ ] Section 11 (Open questions) — all DQ items have owners and deadlines

---

## Coverage verification

- [ ] Every Story ID (ST-NNN) from the traceability matrix is covered by at least one data flow in Section 4
- [ ] Every functional requirement (FR-NNN) from the PRD has a corresponding component or flow
- [ ] Every NFR (NFR-NNN) from the PRD has a named design mechanism in Section 9
- [ ] No story is left unaddressed ("will be handled in implementation" is not acceptable)

---

## Diagram quality

- [ ] System context diagram shows all external actors and systems (including partner company systems)
- [ ] Every arrow in the diagram is labelled with protocol and data type
- [ ] Sequence diagrams exist for all primary flows (happy path minimum)
- [ ] Error paths are shown in sequence diagrams for at least the most critical flows
- [ ] Diagrams are consistent with the component descriptions (nothing appears in the diagram that isn't described in Section 3)

---

## Data model quality

- [ ] Every entity has a primary key defined
- [ ] Foreign keys are explicit (no implied relationships)
- [ ] Indexes exist for every column that will be used as a filter in a query
- [ ] Multi-tenant systems have tenant isolation at the query level, not just the application level
- [ ] Migration strategy is stated for every new or modified table
- [ ] Migrations are backward compatible with the current deployed version

---

## Security quality

- [ ] STRIDE threat analysis has been run (`security-audit-secure-sdlc`)
- [ ] Every threat category (S, T, R, I, D, E) has an entry in Section 8 — "not applicable" is acceptable but must be stated
- [ ] Authentication mechanism is named and specific (not just "auth will be in place")
- [ ] Authorisation model handles multi-tenancy if applicable
- [ ] All fields containing PII or sensitive data are identified
- [ ] Audit log requirements are specified

---

## Implementation phases quality

- [ ] Each phase is independently deployable (does not require a subsequent phase to function)
- [ ] Phase 1 is the smallest useful slice (not "implement everything, then test")
- [ ] Exit criteria for each phase are specific and verifiable
- [ ] Stories (ST-NNN) are assigned to specific phases
- [ ] No phase has a dependency on an external item that is not confirmed available

---

## Open questions

- [ ] No DQ items in Section 11 affect the design of Phase 1 components (Phase 1 must be unambiguous)
- [ ] All DQ items have an owner and a deadline
- [ ] No DQ item is older than 5 business days without an update

---

## Architecture and security review

- [ ] Architecture review conducted by a designated reviewer (`architecture-review-governance`)
- [ ] All blocking findings from architecture review are resolved
- [ ] STRIDE threat modelling run by security reviewer (`security-audit-secure-sdlc`)
- [ ] All blocking security findings are resolved

---

## Scoring

| Result | Criteria |
|--------|----------|
| PASS — ready for implementation | All items checked |
| CONDITIONAL PASS | All mandatory items checked; minor gaps agreed with timeline |
| FAIL — return to design | Any story uncovered, any NFR without a mechanism, blocking findings unresolved |

---

## Gap report format

```
## Design doc quality gap report

**Document:** DESIGN.md
**Feature:** [Feature name]
**Reviewed by:** [Name, Role]
**Date:** [date]
**Result:** FAIL

### Blocking gaps

| Section | Item | Problem | Required action |
|---------|------|---------|-----------------|
| Section 4 | ST-007 | No data flow defined for this story | Add sequence diagram for the device decommission flow |
| Section 9 | NFR-003 | No design mechanism for 99.9% availability NFR | Add HA design (load balancing, health checks, restart policy) |

### Non-blocking gaps

| Section | Item | Problem | Recommendation |
|---------|------|---------|----------------|
| Section 6 | devices table | No index on tenant_id | Add index — every query will filter by tenant_id |
```
