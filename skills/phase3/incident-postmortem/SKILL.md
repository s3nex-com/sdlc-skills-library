---
name: incident-postmortem
description: >
  Activate when conducting a post-incident review, writing a post-mortem document, running
  a blameless incident retrospective, analysing a production outage to identify contributing
  factors and systemic improvements, tracking action items from prior post-mortems, or
  building the incident response process for a team. Use when something went wrong in
  production and the goal is to learn from it and prevent recurrence.
---

# Incident post-mortem

## Purpose

Every production incident is an opportunity to improve the system. Post-mortems — conducted well — extract the maximum learning from each incident and drive concrete improvements. The goal is always the same: understand what happened, improve the conditions that allowed it, and prevent recurrence.

---

## When to use

- A P1 or P2 production incident has been resolved and a post-mortem is required (within 5 business days)
- A P3 incident has recurred and warrants a structured review
- The incident response process itself needs to be built or improved for the team
- Action items from a previous post-mortem need to be reviewed for follow-through
- A near-miss occurred (no user impact but would have been an incident with slightly different timing) and deserves learning from

## When NOT to use

- **Proactive risk identification before anything has broken** — use `technical-risk-management`. Post-mortem is retrospective; risk management is forward-looking.
- **Ongoing monitoring, alerting, or SLO definition** — use `observability-sre-practice`. Post-mortem consumes telemetry; it does not define it.
- **Deliberate resilience testing (game days, fault injection)** — use `chaos-engineering`. Chaos is planned; post-mortems follow unplanned failures.
- **Recurring culture or process problems across many incidents** — once a pattern is visible, escalate to `team-coaching-engineering-culture`.
- **Minor degradations with workarounds (P3)** — a postmortem is only warranted if the P3 recurs. Log and move on otherwise.

---

## Process

### During and immediately after the incident

1. Capture the timeline while it is fresh — within 1 hour of resolution. Record timestamps, what was observed, what was tried, and when service was restored.
2. Determine severity (P1/P2/P3). A post-mortem is required for all P1 and P2 incidents.

### Writing the post-mortem

3. Complete the post-mortem document within 5 business days of resolution (48 hours for a P1 preliminary version).
4. Write the impact summary: what users experienced, how many were affected, and any data impact — specific and quantified, not vague.
5. Reconstruct the complete timeline from system telemetry, logs, and alert timestamps. Do not rely solely on memory.
6. Apply the 5 Whys: ask "why?" at least 5 times until you reach a systemic cause. Stop at "someone made a mistake" — that is not a root cause; ask why the system allowed the mistake.
7. Write the "What went well" section honestly. These practices need to be reinforced.
8. Write the "What went poorly" section in systemic terms: what conditions allowed this to happen? No individual blame.
9. Write action items: each must be specific, owned, and time-bound. Generic items ("improve monitoring") are not actionable; "add connection pool utilisation alert threshold 80% by Sprint 15 — owner Alice" is.
10. Share the draft with all participants at least 24 hours before the post-mortem meeting for corrections and additions.
11. Facilitate the 60–90 minute post-mortem meeting. Confirm action item owners and due dates.
12. Track action items formally. At the next monthly review, confirm which items are complete and verify they were effective (did the same incident type recur?).
13. Append the execution log entry.

## Blameless post-mortem principle

The goal of a post-mortem is to understand what happened and improve the system, not to find and punish individuals. Complex systems fail because of systemic factors — inadequate tooling, unclear processes, insufficient testing, missing monitoring — not because of individual incompetence.

**Blameless does not mean consequence-free.** Patterns of poor engineering practice, ignored warnings, or repeated process violations are system problems and should be addressed at the system level (better tools, clearer processes, training, oversight).

**A post-mortem that concludes "engineer X made a mistake" has failed.** The right question is always: "What conditions allowed this mistake to happen, and how do we change those conditions?"

---

## Incident severity

| Severity | Definition | Response |
|----------|-----------|----------|
| P1 — Critical | Service fully unavailable; data loss; security breach | Notify team immediately; status update every 30 minutes |
| P2 — High | Service degraded; significant user impact | Notify team within 1 hour; update when resolved |
| P3 — Medium | Minor degradation; workaround available | Log and resolve; notify if it may affect others |

Post-mortems are required for all P1 and P2 incidents. P3 warrants a post-mortem if it recurs.

---

## Incident timeline and response

### During the incident

1. **Detect** — alert fires or user reports arrive
2. **Acknowledge** — on-call engineer acknowledges within the SLA
3. **Assess** — what is the user impact? What is the severity?
4. **Communicate** — notify stakeholders; create incident channel
5. **Mitigate** — restore service (not necessarily fix root cause)
6. **Resolve** — service restored; users unaffected
7. **Document** — capture the timeline while it is fresh (within 1 hour of resolution)

### Incident status update template

```
[INCIDENT] {Service name} — P{severity} — Status: INVESTIGATING | MITIGATING | RESOLVED

Summary: {One sentence on user impact}

Timeline (UTC):
- {HH:MM} Detected: {how}
- {HH:MM} On-call acknowledged
- {HH:MM} {What was found / tried}

Impact: {users affected, functionality broken, any data impact}

Next update: {time} or when status changes
```

---

## Post-mortem document structure

Complete the post-mortem within 5 business days of incident resolution. For P1 incidents, a preliminary version should be shared within 48 hours.

```markdown
# Post-mortem: {Incident title}

**Incident ID:** INC-{number}
**Severity:** P{1|2|3}
**Date of incident:** {date}
**Duration:** {start time} to {end time} UTC ({total duration})
**Services affected:** {list}
**Authors:** {names of people involved in investigation}
**Status:** Draft | Under review | Final

---

## Impact summary

**User impact:** {What users experienced — specific, quantified where possible}
Example: "Device operators were unable to ingest telemetry events for 23 minutes.
Approximately 4,200 events were rejected with 503 errors. No data loss — rejected
events were retried by device firmware and successfully ingested after resolution."

**Business impact:** {Revenue impact, SLO impact, contractual impact}
Example: "Error budget consumed: 38% of the monthly 99.9% SLO budget.
One customer (Org-XYZ) submitted a support ticket about event gaps in their dashboard."

---

## Timeline

All times UTC.

| Time | Event |
|------|-------|
| 14:23 | PagerDuty fires: `IngestionAPIErrorRate > 1%` |
| 14:24 | Alice Chen acknowledges; begins investigation |
| 14:26 | Alice identifies error pattern: `connection pool exhausted` in logs |
| 14:28 | Alice notifies both companies' engineering leads |
| 14:31 | Alice increases database connection pool size via config change |
| 14:34 | Error rate drops to 0%; service restored |
| 14:40 | Alice confirms resolution and begins root cause analysis |
| 14:46 | Post-mortem draft created |

---

## Root cause analysis

### Immediate cause
{What directly caused the incident?}
Example: The ingestion service's database connection pool was exhausted. New requests could not
acquire a connection and failed with a 503 error.

### Contributing factors

Use the "5 Whys" to get to the systemic cause:

**Why 1:** Why was the connection pool exhausted?
The pool was sized at 50 connections. At peak load (Monday morning), 50 concurrent database
operations were in flight simultaneously.

**Why 2:** Why were 50 operations in flight simultaneously?
A Monday morning batch job run by the device-worker service submits 10,000 device status
queries in parallel, each requiring a database connection.

**Why 3:** Why does the batch job run queries in parallel without limiting concurrency?
The batch job was implemented without a concurrency limit. The original implementation
assumed < 1,000 devices; the fleet has grown to 50,000 devices over 6 months.

**Why 4:** Why was there no alerting on connection pool utilisation?
Connection pool utilisation was not instrumented as a metric. The only database metric
was query latency.

**Why 5:** Why was connection pool utilisation not monitored?
The original service setup checklist did not include connection pool monitoring as a required
metric. No one identified the gap during the last architecture review.

**Root cause:** The ingestion service's connection pool was sized for a device fleet 50× smaller
than current scale, and there was no monitoring to detect approaching exhaustion before it caused
a service outage.

---

## What went well

{Be specific — these are practices worth preserving and reinforcing}
- Alert fired within 60 seconds of the error rate exceeding threshold
- On-call engineer was familiar with the service; identified the root cause within 5 minutes
- Fix was applied without a deployment (runtime config change)
- Post-incident communication to affected customer was sent within 2 hours

---

## What went poorly

{Be specific and systemic — what conditions allowed this to happen?}
- Connection pool exhaustion is a predictable failure mode; it should have been detected before reaching users
- Batch job growth was not tracked against infrastructure sizing assumptions
- No capacity review was triggered when the device fleet doubled in size

---

## Action items

| ID | Action | Owner | Priority | Due date | Status |
|----|--------|-------|----------|----------|--------|
| AI-001 | Add connection pool utilisation metric and alert (> 80% triggers High alert) | Alice Chen | High | {date} | Open |
| AI-002 | Add concurrency limit to device-worker batch job (max 100 concurrent queries) | Bob Martin | High | {date} | Open |
| AI-003 | Review and update connection pool size based on current fleet size (50 → 150) | Alice Chen | High | {date} | Open |
| AI-004 | Add fleet size to capacity review triggers (alert when fleet grows > 20%) | Platform team | Medium | {date} | Open |
| AI-005 | Add connection pool monitoring to service setup checklist | Engineering lead | Medium | {date} | Open |
| AI-006 | Conduct capacity review for all services sized for < 10,000 devices | Tech lead | Medium | {date} | Open |

---

## Lessons learned

{2-4 concise lessons that apply beyond this specific incident}

1. **Scale assumptions require explicit tracking.** This incident was caused by a system designed
for 1,000 devices being used with 50,000. Capacity assumptions embedded in configurations
must be surfaced and reviewed when underlying scale changes.

2. **Connection pool exhaustion is a predictable, monitorable failure mode.** Unlike hardware
failures, pool exhaustion gives advance warning via utilisation metrics. The absence of
monitoring for a known failure mode is a system design gap, not bad luck.

3. **Batch jobs at scale behave differently from batch jobs at origin size.** Growth in the
subject data makes previously safe patterns dangerous. Batch job concurrency should be
bounded, not unbounded.

---

## Follow-up

Post-mortem review: {date and time}
Attendees: {team + relevant stakeholders}
Action item review in {n} weeks: {date}
```

---

## Post-mortem facilitation guide

### Before the meeting

1. Share the draft post-mortem with all participants at least 24 hours before the meeting
2. Ask participants to add any timeline events they observed
3. Ask: "What questions should we make sure we answer in this meeting?"

### During the meeting (60 minutes typical for P2, 90 minutes for P1)

| Time | Topic |
|------|-------|
| 0–5 min | Agree the meeting norms: blameless, curious, constructive |
| 5–15 min | Walk through the timeline — corrections and additions |
| 15–35 min | Root cause analysis — use 5 Whys, resist stopping at "human error" |
| 35–50 min | What went well? What went poorly? |
| 50–60 min | Action items — who owns what? When? |

### Facilitation prompts

- "What would have needed to be true for this not to happen?"
- "If this engineer hadn't been here, what would have happened?"
- "What made this hard to diagnose quickly?"
- "At what point did we first have enough information to prevent the user impact?"
- "What would change if our on-call rotation included someone who had never seen this service before?"

---

## Action item tracking

Post-mortem value is in the follow-through. Track action items formally:

```
## Post-mortem action item review: {Month}

| Incident | AI ID | Action | Owner | Due | Status | Notes |
|----------|-------|--------|-------|-----|--------|-------|
| INC-047 | AI-001 | Connection pool alert | Alice | {date} | ✅ Done | Alert deployed 2024-03-20 |
| INC-047 | AI-002 | Batch job concurrency limit | Bob | {date} | 🔄 In progress | PR in review |
| INC-047 | AI-003 | Pool size increase | Alice | {date} | ✅ Done | Config updated |
| INC-047 | AI-004 | Fleet size capacity trigger | Platform | {date} | ❌ Overdue | Deprioritised; escalate |
```

Overdue action items are surfaced to the team. Closed action items trigger a
"did it work?" verification: if the same incident type recurs, the action item was ineffective
and a new root cause analysis is needed.

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] incident-postmortem — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] incident-postmortem — Post-mortem for INC-047: connection pool exhaustion
[2026-04-20] incident-postmortem — Action item review: 3 of 6 items from INC-047 complete
```

---

## Output format

### Incident summary (for sharing with stakeholders)

```
## Incident summary: {Incident ID} — {Title}

**Date:** {date} | **Duration:** {duration} | **Severity:** P{level}

### User impact
{Plain-English description of what users experienced}

### Root cause (summary)
{2-3 sentences on the root cause}

### Resolution
{What was done to restore service}

### Data impact
{Any data lost, corrupted, or delayed? Quantify if possible.}

### Action items committed
{List with owners and dates}

**Contact for questions:** {name, email}
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for postmortem document templates, 5-Whys facilitation guides, and action item tracking formats as they are developed.
