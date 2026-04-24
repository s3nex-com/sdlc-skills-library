# Scope change impact analysis template

## Purpose

Every scope change request must be accompanied by an impact analysis before it is approved or rejected. This analysis makes the true cost of the change visible — effort, risk, timeline, and downstream effects — so both companies can make an informed decision.

---

## Impact analysis format

**Change Request ID:** [SCR-YYYY-NNN]
**Analysis date:** [YYYY-MM-DD]
**Analyst:** [Name, Role, Company]

---

### 1. Change summary

**What is being requested:** [One clear sentence — what new capability or change is this?]

**Requesting party:** [Company and role]

**Business justification given:** [The reason the requestor gave for this change]

---

### 2. Affected requirements

List every existing requirement that this change touches, adds to, or supersedes.

| Req ID | Requirement summary | Impact type | Description of change |
|--------|-------------------|-------------|----------------------|
| REQ-NNN | [summary] | Modify / Extend / Supersede / No change | [what changes] |
| [New] | [new requirement] | New | [description] |

**Net change:** [X existing requirements modified, Y new requirements added, Z requirements superseded]

---

### 3. Affected code modules

| Module | Impact | Estimated change effort |
|--------|--------|------------------------|
| [service/module path] | [New / Modify / Refactor / Delete] | [days] |

---

### 4. Test changes required

| Test ID | Test type | Impact | Estimated effort |
|---------|-----------|--------|-----------------|
| [TC-NNN] | Unit | Modify / Add / Delete | [days] |
| [IT-NNN] | Integration | Modify / Add / Delete | [days] |
| [new] | Contract | New | [days] |

---

### 5. Effort estimate

| Category | Effort (days) | Owner |
|----------|--------------|-------|
| New development | | Company B |
| Modification of existing code | | Company B |
| New tests | | Company B |
| Specification updates | | Company A |
| Architecture review | | Company A |
| **Total** | | |

**Estimate confidence:** [High / Medium / Low — and why]

---

### 6. Timeline impact

| Milestone | Current date | Revised date if approved | Impact |
|-----------|-------------|--------------------------|--------|
| [Milestone name] | [date] | [date] | [+N days / No change] |

**Critical path impact:** [Does this change affect the critical path? If so, how?]

---

### 7. Risk assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| [e.g., Implementation complexity underestimated] | Medium | High | [spike/prototype before commitment] |
| [e.g., Change destabilises existing tested functionality] | Low | Medium | [regression test run before merge] |

**Overall risk rating:** [High / Medium / Low]

---

### 8. Recommendation

**Recommended decision:** [Approve / Reject / Approve with conditions / Defer to Phase 2]

**Rationale:** [Why is this the right call given the evidence above?]

**Conditions (if conditional approval):** [What must be true for approval to stand?]

**Alternative approach (if rejecting):** [Is there a cheaper way to meet the underlying business need?]

---

## Example: completed impact analysis

**Change Request ID:** SCR-2024-005
**Analysis date:** 2024-05-20
**Analyst:** Alice Chen, Lead Architect, Company A

### 1. Change summary

**What is being requested:** Add support for batch telemetry event ingestion — a new API endpoint accepting up to 1,000 events in a single HTTP request.

**Requesting party:** Company A Product Manager

**Business justification:** Three enterprise customers with high-frequency sensors report that per-event HTTP overhead (connection establishment, TLS handshake) creates unacceptable overhead at >10 events/second per device. Batch ingestion would reduce their network cost by ~80%.

### 2. Affected requirements

| Req ID | Requirement summary | Impact type | Description of change |
|--------|-------------------|-------------|----------------------|
| REQ-005 | Ingest telemetry events at 50k events/sec | Extend | Throughput target remains; batch endpoint must also meet it |
| [New] | Accept batch of up to 1,000 events in single POST | New | New REQ-012 |
| [New] | Return per-event success/failure in batch response | New | New REQ-013 |
| [New] | Reject batch if >1,000 events | New | New REQ-014 |

### 3. Affected code modules

| Module | Impact | Estimated effort |
|--------|--------|-----------------|
| `services/telemetry-ingestor/api/ingest.py` | Modify | 2 days |
| `services/telemetry-ingestor/validators.py` | Modify | 0.5 days |
| `services/telemetry-ingestor/kafka_producer.py` | Modify | 1 day |
| `api-specs/telemetry-ingestion.yaml` | Modify | 0.5 days |

### 4. Test changes

| Test type | Impact | Estimated effort |
|-----------|--------|-----------------|
| Unit tests for batch endpoint | New (8 test cases) | 1.5 days |
| Integration test for batch Kafka publish | New | 1 day |
| Contract tests for batch endpoint | New | 0.5 days |
| Load test for batch throughput | Modify PT-001 | 0.5 days |

### 5. Effort estimate

| Category | Effort |
|----------|--------|
| New development + code modifications | 4 days |
| Tests | 3.5 days |
| Spec update | 0.5 days |
| **Total** | **8 days** |

**Estimate confidence:** High — scope is well-understood, similar pattern already implemented.

### 6. Timeline impact

M2 shifts from 2024-06-15 to 2024-06-27 (+2 sprints assuming 1 sprint = 1 week).

### 7. Risk

Low overall. The batch endpoint is additive — it does not change existing per-event behaviour. Risk: batch validation edge cases (partial failure within a batch). Mitigation: write tests for all partial-failure scenarios before implementation.

### 8. Recommendation

**Approve.** 8-day effort is proportionate to the business value (enterprise customer retention, reduced network overhead). Risk is low. The implementation plan is clear. Recommend including in the M2 sprint.
