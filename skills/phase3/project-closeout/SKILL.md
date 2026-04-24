---
name: project-closeout
description: >
  Governs the formal end of a project: documentation audit, deliverables sign-off,
  knowledge transfer, operational handover, DORA final report, and lessons learned.
  Trigger when: a project is wrapping up, a system is being handed to a sustaining
  team, a contract engagement is ending, a major version is closed and moving to
  maintenance, or the team needs to verify readiness for handover. Also trigger for:
  "close out the project", "handover to ops", "final handover", "project done checklist",
  "project wrap-up", "lessons learned", "DORA final report", "is the project done",
  "hand off to sustaining team", "engagement wrap-up".
---

# Project closeout

## Purpose

The SDLC pipeline ends at Stage 5: merged, tagged, deployed. But that is not the same as the project being done. Documentation can be stale, only one person may know how the system actually operates, and the receiving team may not have access to all the systems they need. This skill handles everything between "deployed" and "project closed": documentation audit, deliverables sign-off, knowledge transfer, operational handover, DORA final report, and lessons learned. Without this step, handovers fail silently weeks later when someone needs something that was never documented.

## When to use

- A project or engagement is wrapping up and needs formal closure
- The team is handing the system to a sustaining or operations team
- A contract or statement of work is completing and deliverables need sign-off
- A major release version is closing and moving to maintenance mode
- The team wants to verify that operations can run the system without the original engineers present
- A lessons-learned session is overdue after a multi-month engagement

## When NOT to use

- **Post-incident review** — use `incident-postmortem`. A postmortem is not a closeout; it covers a specific failure event, not the end of a project.
- **DORA metrics mid-project** — use `delivery-metrics-dora` standalone. This skill calls it at the end; do not conflate the two.
- **Ongoing operations health checks** — use `observability-sre-practice` or `technical-debt-tracker`. Closeout is a one-time event, not a recurring cadence.
- **Sprint retrospectives** — not this skill. Closeout lessons learned is an engagement-level review, not a sprint ceremony.
- **Release readiness** — use `release-readiness`. Closeout comes after the release is already live and stable.

## Process

Work through each section in order. Do not mark the project closed until all six sections are complete or explicitly deferred with a documented owner and due date.

---

### 1. Documentation audit

Check that each of these exists, is current, and is accessible to the receiving team. "Current" means reflects the deployed system, not the system as designed six months ago.

- [ ] Architecture diagrams: C4 context diagram and C4 component diagram
- [ ] All ADRs written, dated, and indexed in `docs/decisions/` or equivalent
- [ ] API reference current for all live endpoints (OpenAPI / Protobuf / GraphQL schema)
- [ ] Runbooks covering all P1 and P2 operational scenarios (every alert must have a runbook)
- [ ] README updated with final setup and deployment instructions; a new engineer can follow it cold
- [ ] Dependency SBOM current (generated from the final release, not from an earlier build)

If any item is missing: assign an owner and a due date. Do not proceed to sign-off without completing it or explicitly deferring it with written acknowledgement from the receiving team.

---

### 2. Deliverables sign-off

- List every contractual deliverable from the PRD and/or contract
- For each deliverable: verify it is complete and matches the agreed acceptance criteria
- Obtain written acknowledgement from the receiving team or stakeholder for each deliverable
- Record where the acknowledgement lives (email thread, ticket, Confluence page, signed doc)
- Do NOT close the project until acceptance is on record for every deliverable

If a deliverable is disputed: document the dispute, pause closure on that item, and resolve it explicitly. Do not quietly drop a deliverable.

---

### 3. Knowledge transfer

- Identify single points of knowledge: situations where only one engineer knows how X works
- For each single point of knowledge: either document it in a runbook or ADR, or run a knowledge transfer session with at least one member of the receiving team
- Verify the runbooks are complete enough to operate the system: give them to someone not on the original project and ask them to perform a simulated P2 response. Fix gaps before handover.
- Confirm that the receiving team can answer: "The primary alert fires at 2am. Who gets paged? What do they do first?"

---

### 4. Operational handover

- Confirm on-call rotation is established and documented (who, what escalation path, what tool)
- Confirm alerting is configured: all critical alerts have recipients set and have been tested
- Confirm the receiving team has access to: production systems, monitoring dashboards, logs, secrets vault, incident tooling
- If the project used Standard or Rigorous mode: run one final game day or chaos scenario with the receiving team present and operating, not observing
- Record: who the handover was transferred to, when, and what access was confirmed

---

### 5. DORA final report

Run `delivery-metrics-dora` one final time to produce the engagement summary. The report must include:

- Deployment Frequency over the project duration
- Lead Time for Changes (average and median)
- Change Failure Rate
- Mean Time to Restore (MTTR)
- Total incidents by severity (P1, P2, P3)
- Total technical debt items created and resolved during the project
- Final test coverage percentage (from the last CI run)

This report is a deliverable. Include it in the project closeout record.

---

### 6. Lessons learned

Run a 30-minute session — not a ceremony, not a retrospective framework. Three questions only:

1. What worked well and should be adopted on other projects?
2. What would we do differently?
3. What was the most painful thing, and what would have prevented it?

Record the decisions and action items, not the discussion. Opinions and venting stay in the room. Append the findings to the project ADR index as `ADR-XXX-lessons-learned.md` so they are findable later.

---

## Output format

A completed project closeout summary looks like this:

```
Project: Device Telemetry Platform v2
Closed: 2026-04-20
Deliverables: 12/12 accepted
  — Written acknowledgement from ops team on 2026-04-18 (ticket #OPS-441)
Documentation: Complete
  — 3 runbooks (deploy, rollback, P2-alert-response)
  — 2 architecture diagrams (C4 context + component)
  — 8 ADRs indexed
  — API reference current (OpenAPI 3.1, rendered at /docs)
  — SBOM generated from v2.4.1 release
DORA (6-month average):
  — Deployment Frequency: 3/week
  — Lead Time: 18hrs
  — Change Failure Rate: 4%
  — MTTR: 45min
Incidents: 2 P2, 0 P1 — both resolved with < 1hr MTTR
Knowledge transfer: Completed 2026-04-15 with on-call team (3 sessions)
  — P2 runbook tested by ops engineer: passed
  — No remaining single points of knowledge
Handover: Received by ops team 2026-04-18
  — On-call rotation confirmed (PagerDuty, 4-person rotation)
  — Access confirmed: prod, Grafana, Loki, Vault
  — Final game day completed 2026-04-17
Open items (carry forward to v3):
  — ADR-012: Redis vs Kafka decision deferred pending load test results
  — Tech debt: 3 items deferred, tracked in tech-debt-tracker
Lessons learned: ADR-009-lessons-learned.md
```

Do not close the project with open items that do not have an explicit owner and a next-project reference. "Carry forward" is only acceptable if there is an active project to carry it to.

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] project-closeout | outcome: OK|BLOCKED|PARTIAL | next: [what is blocking or what comes next] | note: [one-line summary]
```

Examples:
```
[2026-04-20] project-closeout | outcome: OK | next: none — project closed | note: Device Telemetry Platform v2 closed, 12/12 deliverables accepted
[2026-04-20] project-closeout | outcome: BLOCKED | next: wait for ops access confirmation | note: handover blocked on Vault access — ticket OPS-441
[2026-04-20] project-closeout | outcome: PARTIAL | next: run DORA report after final deploy | note: docs audit done, waiting on final release for DORA metrics
```

---

## Reference files

- `references/closeout-checklist.md` — Full line-by-line checklist covering all six sections, suitable for use as a PR checklist or ticket description
