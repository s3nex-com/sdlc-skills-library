# Risk rating matrix

## Probability scale (1–5)

| Level | Label | Definition | Example |
|-------|-------|-----------|---------|
| 1 | Rare | Unlikely to occur; no evidence of this happening in similar projects | A major cloud provider suffers a full regional outage lasting >24 hours |
| 2 | Unlikely | May occur but is not expected; less than 20% probability | A key engineer leaves the project unexpectedly mid-sprint |
| 3 | Possible | Could occur; roughly 50% probability based on similar engagements | Integration complexity is underestimated by 30% |
| 4 | Likely | Expected to occur in most similar projects; >70% probability | A scope change is requested during active development |
| 5 | Almost certain | Expected to occur; already showing early warning signs | Communication latency between teams due to timezone differences |

## Impact scale (1–5)

| Level | Label | Definition | Business impact |
|-------|-------|-----------|----------------|
| 1 | Negligible | Minor inconvenience; absorbed within current sprint | A single test flaking; a minor bug in a non-critical path |
| 2 | Low | Noticeable but manageable; absorbed within 2 sprints with no milestone impact | A dependency version update required; minor API contract clarification needed |
| 3 | Medium | Sprint-level impact; resolves within one milestone without threatening overall delivery | 2-week delay to a feature; requires scope negotiation for one milestone |
| 4 | High | Milestone-level impact; threatens delivery date or quality commitment | >2-week delay cascading across milestones; significant rework required |
| 5 | Critical | Project-level impact; threatens overall delivery, contractual commitments, security, or data integrity | Project failure; legal exposure; security breach; catastrophic data loss |

---

## 5×5 Probability × Impact matrix

**Composite score = P × I**

|  | **Impact 1** (Negligible) | **Impact 2** (Low) | **Impact 3** (Medium) | **Impact 4** (High) | **Impact 5** (Critical) |
|--|--------------------------|-------------------|-----------------------|---------------------|------------------------|
| **P5** Almost certain | 5 🟢 Low | 10 🟡 Medium | 15 🟠 High | 20 🔴 Critical | 25 🔴 Critical |
| **P4** Likely | 4 🟢 Low | 8 🟡 Medium | 12 🟠 High | 16 🟠 High | 20 🔴 Critical |
| **P3** Possible | 3 🟢 Low | 6 🟡 Medium | 9 🟡 Medium | 12 🟠 High | 15 🟠 High |
| **P2** Unlikely | 2 🟢 Low | 4 🟢 Low | 6 🟡 Medium | 8 🟡 Medium | 10 🟡 Medium |
| **P1** Rare | 1 🟢 Low | 2 🟢 Low | 3 🟢 Low | 4 🟢 Low | 5 🟢 Low |

---

## Priority bands and required actions

### 🔴 Critical (score 20–25)

**Action:** Immediate escalation to VP Engineering on both sides. Active mitigation must begin within 24 hours. Daily status update until the risk score drops to High or the risk is resolved. Report at every governance meeting.

**Examples at this level:** A security vulnerability discovered in production; Company B announces inability to meet the M2 milestone with no recovery plan; a contractual dispute over IP ownership is raised.

### 🟠 High (score 12–19)

**Action:** Active mitigation required. Mitigation plan must be agreed within one sprint. Risk reviewed at every weekly sync. Escalate to Engineering Manager if mitigation is not progressing.

**Examples at this level:** Kafka throughput target unvalidated with delivery approaching; key engineer absence during critical sprint; third-party API changes their authentication model.

### 🟡 Medium (score 6–11)

**Action:** Mitigation plan documented and assigned. Review at monthly steering committee. No immediate escalation required unless early warning indicators trigger.

**Examples at this level:** Timezone communication overhead between teams; single-person knowledge of a critical component; unclear SLA definition for a partner service.

### 🟢 Low (score 1–5)

**Action:** Logged in the risk register. Monitor for changes. No active mitigation required.

**Examples at this level:** A non-critical third-party library approaching end-of-life (>12 months away); minor documentation gaps; optional feature with unclear requirements.

---

## Escalation thresholds

Escalate immediately (same day) when:
- Any risk scores Critical (20+)
- Any High risk's score increases by 4+ points since last review
- Any risk moves to status "Escalated"
- An early warning indicator for a Critical or High risk is triggered

Escalate at next governance meeting when:
- A new High risk is identified
- A Medium risk's mitigation is not progressing
- Two or more new Medium risks are identified in the same sprint
