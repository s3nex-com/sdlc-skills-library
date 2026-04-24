# Kill criteria examples

Kill criteria are explicit, pre-agreed conditions under which the project should be stopped or fundamentally restructured. Define them at project kickoff, when both companies are aligned and objective. A kill criterion agreed under pressure during a crisis is disputed; one agreed upfront is not.

**What makes a good kill criterion:**
- Specific and measurable — not "quality is unacceptable" but "defect density exceeds X per Y"
- Not subject to interpretation — both companies must agree whether the criterion is met, without debate
- Agreed by both companies and recorded in the project charter
- Has a decision owner — who calls the kill, and by when after the criterion is met?

---

## Kill criterion 1: Sustained delivery failure

**Criterion:** Company B misses three consecutive milestone deliveries with no mutually agreed recovery plan, where a "miss" is defined as delivering less than 60% of the committed milestone scope by the agreed date.

**Measurement:** Milestone acceptance record — acceptance criteria pass/fail results and percentage of stories delivered.

**Rationale:** Three consecutive misses without a recovery plan indicates a systemic capacity or capability problem that will not self-correct. Continuing to fund and wait without structural change is not a reasonable business decision.

**Decision owner:** VP Engineering (Company A), with notification to Company B leadership
**Decision deadline:** Within 5 business days of the third missed milestone

**Before pulling this trigger:** Confirm that: (1) scope changes did not inflate commitments unfairly, (2) Company A's delays did not contribute (API specs frozen late, review delays), (3) a structured recovery plan has been offered and declined or failed.

---

## Kill criterion 2: Critical security vulnerability discovered post-delivery

**Criterion:** A Critical CVSS 9.0+ vulnerability is discovered in delivered and deployed code that cannot be remediated without a full architectural redesign (i.e., it is not a patch-level fix), AND the vulnerability exposes customer data or enables unauthorised system access.

**Measurement:** CVSS score from security assessment; security lead's determination of remediation scope.

**Rationale:** A fundamental security flaw that cannot be patched creates ongoing legal liability for both companies and an unacceptable risk to customers. If the root cause is architectural, incremental patching is insufficient.

**Decision owner:** VP Engineering (Company A) in consultation with legal counsel
**Decision deadline:** Within 48 hours of the security assessment confirming the architectural nature of the flaw

---

## Kill criterion 3: IP contamination

**Criterion:** Delivered code is found to contain GPL or AGPL licensed components in a way that would require the entire codebase to be open-sourced under GPL/AGPL terms, and Company B is unable to replace the contaminating dependencies within 30 days.

**Measurement:** Legal review of dependency licences in the delivered codebase.

**Rationale:** GPL contamination in a proprietary commercial product is a legal and commercial existential threat to Company A. If the contamination cannot be remediated, the delivered work cannot be used.

**Decision owner:** Legal counsel (Company A) with VP Engineering
**Decision deadline:** 30 days after contamination is confirmed and a remediation plan has been attempted

---

## Kill criterion 4: Unresolvable scope dispute

**Criterion:** Both companies disagree on whether a significant deliverable is in scope (where "significant" means >10 person-days of effort), AND the disagreement has been escalated to VP level at both companies AND remains unresolved after 15 business days.

**Measurement:** Documented escalation record; decision log showing unresolved dispute.

**Rationale:** A scope dispute that reaches VP level and remains unresolved for three weeks indicates a fundamental breakdown in the commercial relationship. Continuing to deliver code against disputed scope creates legal risk and wasted investment.

**Decision owner:** Joint decision by both companies' VP Engineering; if no joint decision, commercial/legal teams take over

---

## Kill criterion 5: Technology target cannot be met

**Criterion:** Performance validation testing demonstrates that the system cannot meet the agreed throughput and latency SLOs (as defined in the charter NFRs) with the current architecture, AND two architecture alternatives have been evaluated and rejected (one by each company), AND the cost to re-architect exceeds 30% of the remaining project budget.

**Measurement:** Load test results showing sustained failure to meet NFR targets; architecture review findings.

**Rationale:** Delivering a system that cannot meet agreed contractual SLOs is not a deliverable — it is a liability. If the architecture fundamentally cannot meet the requirements and re-architecting is prohibitively expensive, the project terms must be renegotiated or stopped.

**Decision owner:** Joint decision by both companies' VP Engineering
**Decision deadline:** Within 10 business days of the load test results being reviewed

---

## Kill criterion 6: Regulatory or compliance failure

**Criterion:** A regulatory or compliance assessment determines that the system, as designed or implemented, cannot meet GDPR, SOC2, or other applicable compliance requirements agreed in the charter, AND the compliance gap requires a redesign of core data flows.

**Measurement:** Compliance assessment report from legal or external auditor.

**Rationale:** A system that cannot be lawfully operated in the target market is not a deliverable. Compliance is a non-negotiable requirement.

**Decision owner:** Legal counsel in consultation with both VP Engineering
**Decision deadline:** Within 10 business days of compliance assessment

---

## Kill criterion 7: Partner company financial instability

**Criterion:** Company B enters administration, receivership, or announces insolvency proceedings while the engagement is active.

**Measurement:** Public announcement or official notification from Company B.

**Rationale:** If Company B cannot continue to operate, the engagement cannot continue. Code escrow and handover procedures must be initiated immediately.

**Decision owner:** Automatic trigger — legal and commercial teams at Company A take over immediately
**Required actions on trigger:** Code escrow release, IP handover, runbook access transfer, system access audit

---

## Kill criterion 8: Repeated safety or ethics violation

**Criterion:** Company B's engineering team is found to have committed two or more deliberate violations of the agreed security or data handling policies (e.g., two instances of deliberate secrets committed to version control, or a second instance of data from a production environment used in development contrary to policy) within any 90-day period.

**Measurement:** Security audit findings; incident postmortem records.

**Rationale:** A single violation can be a mistake. A pattern indicates either inadequate controls or deliberate disregard for agreed policies. Either is incompatible with the trust required for a production software partnership.

**Decision owner:** VP Engineering (Company A), with Company B formally notified
**Decision deadline:** Within 5 business days of the second violation being confirmed

---

## Kill criteria review checklist

Before finalising the kill criteria:
- [ ] Every criterion is objectively measurable (no "when quality is unacceptable" type language)
- [ ] Every criterion has a named decision owner
- [ ] Every criterion has a decision deadline after the trigger
- [ ] Both companies have agreed to and signed the kill criteria (in the project charter)
- [ ] Both VP Engineering leads have read and discussed the kill criteria at kickoff
- [ ] The list of kill criteria is reviewed at each milestone (are they still appropriate?)
