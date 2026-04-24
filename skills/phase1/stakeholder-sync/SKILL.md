---
name: stakeholder-sync
description: >
  Activate when keeping external stakeholders (clients, users, partners, leadership)
  aligned. Use when: setting communication cadence, drafting a status update, logging a
  decision that affects someone outside the team, handling a scope change request,
  writing a difficult message, or calibrating tone for a non-technical audience. Also
  trigger on: "how do I tell the client", "weekly update", "they're asking for scope
  changes", "we need to escalate", "I need to document what was agreed".
---

# Stakeholder sync

## Purpose

A small engineering team still has stakeholders — clients, end users, leadership, external
partners — who need to know what is happening, what has changed, and what decisions have
been made. This skill keeps those people aligned without turning alignment into a job. It
covers decision logging, scope change handling, communication cadence, status updates, and
escalation — done at the pace of a 3-person team that communicates directly, not through
intermediaries.

---

## When to use

- Setting or adjusting how often you communicate with stakeholders (cadence)
- Writing or structuring a status update, risk notice, or difficult message
- A stakeholder requests a scope change — you need to surface, evaluate, and respond
- A significant decision was made and needs to be recorded before being acted on
- Something is blocked and you need a stakeholder to take action within a specific window
- You need to calibrate the same message for a technical and a non-technical audience

---

## When NOT to use

- Recording a purely internal technical decision (architecture, library choice) → use
  `architecture-decision-records`
- Writing API specs or contracts → use `specification-driven-development`
- A production incident requiring immediate response → use `incident-postmortem`
- Recording technical architecture decisions → `architecture-decision-records`

---

## Process

### 1. Set communication cadence up front

On any engagement lasting more than two weeks, agree on cadence at kickoff. Default model
for small teams:

| Channel | Frequency | Format | Who initiates |
|---------|-----------|--------|---------------|
| Async status update | Weekly | Short written summary (Slack, email, shared doc) | Engineering lead |
| Live sync | Only when blocked or at a milestone | 30-min call | Either side |
| Decision record | On every significant decision | Written entry in decision log | Whoever made the call |
| Scope change | On request | Written record, approval required | Requestor writes it |

Async-first. Reserve live calls for genuine blockers, milestone reviews, and anything where
misreading tone would cost you more time than the call itself.

### 2. Write status updates that are factual, not optimistic

Status updates are not morale reports. They convey facts.

Structure every status update with:
1. **Overall status** — one of: On track / At risk / Blocked — plus one sentence why
2. **Delivered this week** — specific, against what was committed
3. **At risk or blocked** — specific, with estimated impact and what you need
4. **Planned next week** — against agreed commitments
5. **Decisions needed** — explicit asks, with deadline

Lead with the most important thing. If something is blocked, that goes first.

### 3. Log decisions before acting on them

Every decision that affects scope, timeline, external commitments, or what the stakeholder
is expecting must be written down before work continues. Log to `docs/decision-log.md`
using the format in `references/decision-log-template.md`.

"Significant" includes: technology choices the stakeholder cares about, any timeline change,
anything you verbally agreed to in a call that isn't already documented.

### 4. Handle scope change requests in writing

When a stakeholder asks for something outside current scope:

1. Acknowledge the ask immediately (same day) — do not leave it unanswered
2. Stop any work already started on that area
3. Write up the change: what, why, impact on timeline and design (use `references/scope-change-template.md`)
4. Get written approval before proceeding — a Slack message with "approved" counts
5. Update the decision log and any relevant planning documents
6. Resume work

Never accept a scope change verbally only. If it happened on a call, follow up in writing
the same day to confirm what was agreed.

### 5. Calibrate message for audience

The same facts need different framing for different readers:

| Audience | What they need | What to cut |
|----------|---------------|-------------|
| Technical stakeholder | Specific, precise, actionable | Reassurance, softening |
| Non-technical leadership | Business impact + what decision is needed | Implementation detail |
| Mixed audience | Summary first, detail available below | Nothing — layer the message |

Write the most important sentence first. State asks explicitly: "I need approval on X by
Thursday" rather than "please let me know your thoughts."

### 6. Escalate when stuck — not when anxious

Escalation means: something is blocked, you cannot unblock it at your level, and delay
has a specific cost. It is not a way to share anxiety or document yourself.

Escalate when:
- A decision is needed that the current contact cannot make
- A blocker has not moved in more than two working days despite direct follow-up
- Scope or timeline is at risk and the stakeholder does not yet know

How to escalate on a small team (no "steering committee"):
1. Send a direct message to whoever can unblock it — do not CC others performatively
2. Be specific: what is blocked, what you need, by when, what happens if not resolved
3. If unresolved after one follow-up, escalate one level up (engineering lead → leadership)
4. Log the escalation in the decision log so there is a record

---

## Output format with real examples

### Weekly status update

```
Status: At risk — integration test coverage at 42%, target 80% before release gate.

Delivered: Auth service login/logout endpoints on staging; JWT expiry decision logged (#12).
At risk: Test coverage 2 days short. Will miss Thursday milestone unless date slips.
Next week: Complete coverage (priority 1); begin user profile endpoints.
Decision needed: Hold Thursday or slip to Monday? Call by Tuesday EOD.
```

### Scope change record

Use `references/scope-change-template.md`. Fill it in, send it to the requestor for
written confirmation, log the decision, then proceed.

### Escalation message (Slack or email)

```
Subject: [BLOCKED] Auth service — staging credentials needed by Thursday EOD

Blocked: staging credentials were rotated; new ones not shared. Integration tests
cannot complete until resolved.

Impact: Thursday milestone slips to Monday if not fixed today.
Need: Updated credentials from [name/team].
Tried: Followed up with [contact] twice (Mon, Wed) — no response.
Ask: Can you unblock this?
```

### Decision log entry

Full format and examples in `references/decision-log-template.md`. One-line form:

```
| [date] | [decision] | [rationale] | [owner] | [alternatives rejected] |
```

---

## Skill execution log

Append one line to `docs/skill-log.md` when this skill fires:

```
[YYYY-MM-DD] stakeholder-sync — [brief description]
```

Examples:
```
[2026-04-20] stakeholder-sync — weekly status update drafted for auth service milestone
[2026-04-20] stakeholder-sync — scope change logged: add CSV export, deferred to phase 2
[2026-04-21] stakeholder-sync — escalation drafted, staging access blocker
```

If `docs/skill-log.md` does not exist, create it with the header from `sdlc-orchestrator`.

---

## Reference files

- `references/decision-log-template.md` — Decision log format with example entries and
  guidance on what counts as a "significant" decision
- `references/scope-change-template.md` — Lean scope change record: what, why, impact,
  approval
