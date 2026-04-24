# Project closeout checklist

Use this as a PR checklist, a ticket description, or a shared doc during the closeout session. All items must be checked or explicitly deferred before the project is marked closed.

---

## 1. Documentation audit

### Architecture
- [ ] C4 context diagram exists and reflects the deployed system
- [ ] C4 component diagram exists and reflects the deployed system
- [ ] Both diagrams are version-controlled (not only in a slide deck or wiki)

### Architecture Decision Records
- [ ] All significant decisions have ADRs
- [ ] ADR index is current (no ADRs drafted but not indexed)
- [ ] ADRs reference the correct versions of the systems they describe

### API reference
- [ ] OpenAPI / Protobuf / GraphQL schema is current for all live endpoints
- [ ] API reference is rendered and accessible (not only as a raw file in the repo)
- [ ] The URL to the rendered API reference is in the root README

### Runbooks
- [ ] Every P1 alert has a runbook
- [ ] Every P2 alert has a runbook
- [ ] Each runbook has been reviewed by at least one person not on the original project
- [ ] Runbooks are accessible to the receiving team (not blocked by repo permissions)

### README and setup
- [ ] README reflects the final deployed architecture (not a design-time version)
- [ ] Setup instructions have been followed cold by at least one person and confirmed working
- [ ] Deployment instructions cover production, staging, and local development

### SBOM
- [ ] Dependency SBOM generated from the final release (not an earlier build)
- [ ] SBOM is stored alongside the release artefacts

---

## 2. Deliverables sign-off

- [ ] Full list of contractual deliverables identified (from PRD and/or contract)
- [ ] Each deliverable verified as complete
- [ ] Each deliverable matched against its acceptance criteria
- [ ] Written acknowledgement obtained from the receiving team/stakeholder for each deliverable
- [ ] Location of each acknowledgement recorded (ticket, email, doc)
- [ ] No deliverables quietly dropped without explicit agreement

**Deliverables log (fill in for each):**

| # | Deliverable | Status | Accepted by | Evidence location |
|---|-------------|--------|-------------|-------------------|
| 1 | | | | |
| 2 | | | | |

---

## 3. Knowledge transfer

- [ ] Single points of knowledge identified (list every "only X knows how Y works")
- [ ] For each: either documented in a runbook/ADR or a KT session held with the receiving team
- [ ] Runbook tested: someone unfamiliar with the system followed the P2 runbook and completed a simulated response
- [ ] Gaps found during runbook test are fixed (not deferred)
- [ ] Receiving team can answer: "The primary alert fires at 2am — who gets paged and what do they do first?"

**Single points of knowledge log:**

| Knowledge area | Only known by | Resolved via | Done? |
|----------------|--------------|--------------|-------|
| | | doc / KT session | |
| | | doc / KT session | |

---

## 4. Operational handover

### On-call
- [ ] On-call rotation established and documented (tool, members, escalation path)
- [ ] First on-call rotation confirmed (not just planned)

### Alerting
- [ ] All critical alerts have recipients configured
- [ ] All alerts have been tested (fired at least once in staging or prod)
- [ ] Alert routing reviewed: no alerts going to the original project team only

### Access
- [ ] Production systems: receiving team has access
- [ ] Monitoring dashboards: receiving team has access
- [ ] Log aggregation (Loki, Splunk, CloudWatch, etc.): receiving team has access
- [ ] Secrets vault (Vault, AWS Secrets Manager, etc.): receiving team has access
- [ ] Incident tooling (PagerDuty, OpsGenie, etc.): receiving team is configured
- [ ] CI/CD pipelines: receiving team has access and understands how to deploy

### Game day (Standard/Rigorous mode projects only)
- [ ] Final game day or chaos scenario completed with receiving team operating (not observing)
- [ ] Game day findings documented and addressed

**Handover record:**
- Transferred to: _______________
- Date: _______________
- Access confirmed by: _______________

---

## 5. DORA final report

- [ ] `delivery-metrics-dora` run against the full project duration
- [ ] Deployment Frequency recorded
- [ ] Lead Time for Changes (average and median) recorded
- [ ] Change Failure Rate recorded
- [ ] MTTR recorded
- [ ] Total incidents by severity (P1, P2, P3) recorded
- [ ] Total tech debt items created and resolved recorded
- [ ] Final test coverage percentage recorded (from last CI run)
- [ ] Report stored in the project record / docs directory

**DORA summary (fill in):**

| Metric | Value |
|--------|-------|
| Deployment Frequency | |
| Lead Time (avg) | |
| Lead Time (median) | |
| Change Failure Rate | |
| MTTR | |
| P1 incidents | |
| P2 incidents | |
| P3 incidents | |
| Tech debt created | |
| Tech debt resolved | |
| Final test coverage | |

---

## 6. Lessons learned

- [ ] 30-minute session held with the team
- [ ] Three questions answered:
  - [ ] What worked well and should be adopted elsewhere?
  - [ ] What would we do differently?
  - [ ] What was the most painful thing, and what would have prevented it?
- [ ] Decisions and action items recorded (not the discussion)
- [ ] Findings appended to ADR index as `ADR-XXX-lessons-learned.md`
- [ ] Action items have owners and are tracked (not just recorded)

---

## Final gate

Before marking the project closed:

- [ ] All six sections above are complete, or any deferred items have an explicit owner and a next-project reference
- [ ] Closeout summary written (see SKILL.md output format)
- [ ] `docs/skill-log.md` updated with closeout entry
- [ ] Project status in `docs/sdlc-status.md` set to CLOSED

**Open items (carry forward — must have owner and destination):**

| Item | Owner | Carried to | Due |
|------|-------|-----------|-----|
| | | | |
