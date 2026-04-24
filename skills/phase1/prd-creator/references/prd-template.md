# PRD template

Copy this template to `PRD.md` in your project documentation directory. Fill every section. Do not remove sections you think are not relevant — if a section does not apply, state why explicitly.

---

```markdown
# PRD: [Feature / Product Name]

**Version:** 1.0
**Status:** Draft
**Author:** [Name, Company]
**Reviewers:** [Name, Role], [Name, Role]
**Date created:** [YYYY-MM-DD]
**Date approved:** —
**Related documents:** —

---

## 1. Executive summary

[One paragraph. What is being built, for whom, and why now. Readable by a non-technical stakeholder in 60 seconds. Do not mention implementation details.]

---

## 2. Problem statement

**What is the problem or opportunity?**
[2-4 sentences describing the core problem.]

**Who experiences this problem?**
[Who is affected, in what context, and at what frequency.]

**What is the cost of not solving it?**
[User impact: ...]
[Business impact: ...]

**What evidence exists that this is a real problem?**
[Data point / user research finding / support ticket volume / revenue impact / etc.]

---

## 3. Goals

[Write goals as measurable outcomes, not features. Each goal must contain a number or a verifiable condition.]

1. [Goal — e.g., "Reduce device onboarding time from 45 minutes to under 5 minutes for 90% of users"]
2. [Goal]
3. [Goal]

---

## 4. Non-goals

[What this product/feature will NOT do. Each entry must answer: "Is this something a reasonable person might expect this product to do?"]

- NOT: [Statement of what is explicitly excluded]
- NOT: [Statement]
- NOT: [Statement]

---

## 5. User personas and use cases

### Persona 1: [Role / type]

**Context:** [Environment they work in, how frequently they use the product, technical level]
**Primary use case:** [The main thing this persona does with this feature]
**Workflow:** [Step-by-step: what they do, in what order, and what they expect at each step]
**Pain point addressed:** [What frustration or friction this feature removes for them]

### Persona 2: [Role / type]
[Repeat structure above]

---

## 6. Functional requirements

[Each requirement must be: unambiguous (one interpretation only), testable (pass/fail), and independent (understood without reading others).]

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-001 | [Requirement statement] | Must have / Should have / Nice to have | |
| FR-002 | | | |
| FR-003 | | | |

[Minimum 3 requirements. Use "shall" for mandatory, "should" for optional.]

---

## 7. Non-functional requirements

[At minimum: performance, availability, scalability, security, and compliance.]

| ID | Category | Requirement | Measurement method |
|----|----------|-------------|-------------------|
| NFR-001 | Performance | The API must respond within 200ms at p99 under 1,000 concurrent requests | Load test at target concurrency |
| NFR-002 | Availability | The system must achieve 99.9% uptime, measured monthly | Uptime monitoring |
| NFR-003 | Scalability | The system must support 10,000 active devices per tenant without degradation | Load test at target device count |
| NFR-004 | Security | All API endpoints must require authentication via [mechanism] | Security gate review |
| NFR-005 | Compliance | [If applicable: GDPR, SOC2, HIPAA, etc.] | Compliance audit |

---

## 8. Constraints and dependencies

### Technical constraints
- [Existing architecture component that limits design choices]
- [Technology mandate from either company]
- [Infrastructure constraint]

### Business constraints
- [Timeline: must be complete by...]
- [Budget: implementation budget is...]
- [Regulatory: must comply with...]

### External dependencies
- [Partner company deliverable: what, by when, who is responsible]
- [Third-party API: name, version, availability]
- [Data source: what data, from where, under what agreement]

### Assumptions
- [Assumption being made that, if wrong, would change the design]
- [Assumption]

---

## 9. Success metrics

**Primary metric:** [The one number that matters most. How will you know this worked?]
- Metric: [Name]
- Target: [Specific value]
- Measurement: [Where does this data come from?]
- Evaluation timeline: [When will you measure this? e.g., "30 days post-launch"]

**Secondary metrics:**
| Metric | Target | Measurement source | Timeline |
|--------|--------|--------------------|----------|
| [Metric name] | [Target value] | [Data source] | [Timeline] |
| [Metric name] | | | |

---

## 10. Out of scope

[Things explicitly excluded from this release that will be built in a future phase. Distinct from non-goals: non-goals are permanent boundaries; out-of-scope items are deferred to future work.]

- Phase 2: [Feature that will come later]
- Future: [Capability that is not in this release]

---

## 11. Open questions and decisions required

[Every unresolved question must have an owner and a deadline. No PRD with open questions in sections 3, 6, 7, or 9 is ready to proceed.]

| # | Question | Owner | Deadline | Impact if unresolved |
|---|----------|-------|----------|---------------------|
| OQ-001 | [Question] | [Name] | [Date] | [What decisions are blocked] |
| OQ-002 | | | | |

---

## Approval

| Role | Name | Decision | Date | Notes |
|------|------|----------|------|-------|
| Product owner | | Approved / Changes requested / Rejected | | |
| Engineering lead | | Approved / Changes requested / Rejected | | |
| Partner company lead | | Approved / Changes requested / Rejected | | |
| Security reviewer | | Approved / Changes requested / Rejected | | |

**Status after approval:** Ready to enter requirements tracing (Stage 2 of SDLC pipeline)
```
