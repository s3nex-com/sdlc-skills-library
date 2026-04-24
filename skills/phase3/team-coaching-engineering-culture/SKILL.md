---
name: team-coaching-engineering-culture
description: >
  Activate when assessing engineering team health, coaching engineers on technical practices,
  identifying cultural gaps that drive quality or delivery problems, establishing shared
  engineering values and standards, addressing recurring issues that stem from team dynamics
  rather than technical problems, planning capability development, running retrospectives,
  tracking growth goals, or identifying knowledge concentration risks.
---

# Team coaching and engineering culture

## Purpose

For a 3–5 person senior engineering team, culture is either your biggest accelerator or your biggest hidden cost. Problems here do not look like culture problems — they look like recurring bugs, slow PRs, a single person who always gets paged, a skill that only one engineer has. This skill makes those patterns visible and produces concrete artifacts to address them: a quarterly Team Health Snapshot, per-person Growth Plans, and an Engineering Norms Doc. These are not reports to file — they are working tools the team updates as it improves.

---

## When to use

- Quarterly: run the structured retro, produce or update the Team Health Snapshot
- When the same quality problem recurs despite technical fixes — the root cause is cultural
- When one person is the single point of knowledge for a critical system or practice
- After a rough delivery: what process friction made it hard?
- When a team member identifies a skill they want to build — open a Growth Plan item
- When an implicit norm breaks down under pressure and needs to be made explicit

---

## When NOT to use

- **Performance management** — a Growth Plan is not a performance improvement plan. If you need to address underperformance, that is a people management conversation requiring a human, not a skill.
- **Team conflict resolution** — interpersonal conflict needs facilitation by a person. This skill does not substitute for it.
- **HR processes** — anything involving compensation, role changes, or formal disciplinary action is out of scope.
- **Post-incident review** — if a recurring problem was caused by a specific incident, use `incident-postmortem` first. Use this skill if the post-mortem reveals a cultural root cause.
- **DORA metrics** — measuring delivery performance belongs to `delivery-metrics-dora`. This skill uses those numbers as input to the Team Health Snapshot, but does not produce them.

---

## What "coaching" means for a small senior team

This is not top-down mentorship. Three senior engineers do not need coaching in the traditional sense. What they need is:

1. **Knowledge concentration visibility** — only one person knows the auth system, the deployment process, the customer integration. This is a risk. Make it visible. Distribute it through pairing and documentation.
2. **Process friction retrospection** — not just "what bugs did we ship" but "what about our process made this delivery slow or stressful." The answers are usually actionable.
3. **Growth goal tracking** — senior engineers still want to grow. Skills they want to build (new tech, new practices, depth in a domain) should be tracked and given space, not left to chance.
4. **Norm maintenance** — implicit norms (how big is a PR, who reviews what, how do we handle on-call) break down under pressure. Making them explicit and keeping them current prevents recurring friction.

---

## Process

Run this quarterly. Budget 45 minutes for the retro, 15 minutes to update artifacts. Total: one hour per quarter.

### Step 1: Run the quarterly structured retro (45 min)

Format: 45 minutes, whole team, rotating facilitator.

```
Check-in (5 min):
  One word that describes this quarter for you.

What went well? (10 min):
  Each person: 2–3 things. Capture. Dot-vote on the top 2 to preserve deliberately.

What created friction? (15 min):
  Each person: 2–3 friction points. No discussion yet — just gather.
  Group by theme. Pick the top 2 themes to discuss.
  For each: "What one change would have made this significantly easier?"
  Be specific: "frozen the API spec before starting" not "better communication."

Knowledge and growth check (10 min):
  For each critical system or practice: who else can operate it if the primary person is unavailable?
  Any skill gaps that slowed this quarter down?
  Any skills anyone wants to build next quarter?

Commitments (5 min):
  1–3 specific commitments: WHO does WHAT by WHEN.
  Write them down. These go into the Team Health Snapshot action items.
```

### Step 2: Produce or update the Team Health Snapshot (10 min)

Fill in `references/team-health-snapshot-template.md`. This takes 10 minutes after the retro — the data is fresh. Save the completed snapshot as `docs/team-health-YYYY-QN.md`.

The snapshot covers:
- **Velocity** — DORA metrics for the quarter (from `delivery-metrics-dora`)
- **Quality signals** — test coverage trend, PR cycle time, review turnaround
- **Team satisfaction** — explicit, from the retro (not assumed)
- **Risks** — knowledge concentration, burnout signals, skill gaps
- **Action items** — the 1–3 commitments from the retro, with owners and dates

### Step 3: Update Growth Plans (5 min)

Each person has at most 3 active growth plan items. After the retro:
- Close any item that was completed or abandoned
- Add any new skill goal identified in the growth check
- Update progress on open items

Growth plan items must be measurable:
- Not: "improve system design skills"
- Yes: "design and own the next major architectural decision end-to-end, producing an ADR — target: by end of Q3"
- Not: "get better at code review"
- Yes: "reduce PR review turnaround from 3 days to 1 day — track monthly, review in Q3 retro"

### Step 4: Update Engineering Norms Doc when friction is identified

If the retro surfaces a recurring friction point caused by an implicit norm, update `docs/engineering-norms.md`. Do not wait for the retro if a norm breaks down in the middle of a delivery — update it immediately.

Engineering Norms Doc covers:
- PR size limits (e.g. "PRs stay under 400 lines; split anything larger")
- Review expectations (e.g. "every PR needs one non-author review before merge; same-day turnaround target")
- On-call rotation (schedule, escalation path, swap process)
- Pairing cadence (e.g. "pair on anything unfamiliar or cross-domain; at least 2h/week")
- Definition of done additions specific to this team

---

## Culture-quality failure patterns

### Pattern: "Tests slow us down"

**Symptoms:** Low test coverage, skipped tests under deadline, tests written after the fact.

**Root cause:** The team has learned tests are a cost, not an investment — usually because tests are slow, brittle, or poorly written. No direct experience of time saved by catching regressions early.

**Fix:**
1. Find a real example where a test caught a regression before production — make it concrete.
2. Fix slow/brittle tests first. Speed and reliability directly affect whether engineers write them.
3. Make untested code impossible to merge (gate), not just frowned upon.
4. Never publicly skip tests under deadline pressure ("we'll add them later"). Later never comes.

### Pattern: "Code review is a rubber stamp"

**Symptoms:** PRs approved within minutes; no blocking comments; same defect types appear across multiple PRs.

**Root cause:** Reviewers do not feel empowered to block a colleague's PR, or don't want the social friction. Sometimes: "I don't have time to review this properly, I'll just approve it."

**Fix:**
1. Make blocking feedback normal. The first time a reviewer blocks a PR should not be remarkable.
2. Label comments: Blocking / Suggestion / Question. Authors know what needs to change.
3. "Approving a PR makes you partly responsible for it." A rubber-stamp approval takes on risk without doing the work.
4. Senior engineers model substantive reviews, not approvals.

### Pattern: "Only one person knows X"

**Symptoms:** A specific person is always paged; everyone waits for one person to review certain PRs; knowledge leaves with someone on holiday.

**Root cause:** Knowledge concentration accumulated silently — no one noticed it happening until it became a bottleneck or risk.

**Fix:**
1. Name it explicitly in the Team Health Snapshot risks section.
2. Run a pairing session: the owner walks someone else through the system. Goal: two people can operate it.
3. Write a runbook for anything that requires tribal knowledge to operate. If it's in someone's head, it's a risk.
4. In the next delivery, deliberately involve a second person in that area.

### Pattern: "We'll add security later"

**Symptoms:** Auth is "TODO"; secrets occasionally committed; no threat modelling in design.

**Fix:**
1. Security is in the definition of done. An endpoint without auth is not a completed endpoint.
2. Run one STRIDE session together — make threat modelling feel accessible, not academic.
3. SAST and secret scanning in the pipeline removes the need for humans to remember.
4. Share a real example of a security incident from the actual type of issue being deferred.

---

## Coaching conversations

Coaching requires directness without blame. The goal is to raise standards without creating defensiveness.

### Conversation structure for a recurring quality issue

```
1. Observation (specific, not judgement)
   "Across the last three deliveries, input validation is consistently
   missing on new API endpoints."

2. Impact (concrete)
   "This creates a security risk at the ingestion boundary — malformed
   device IDs can bypass registry checks."

3. Standard (clear reference)
   "Our secure coding standards require validation at all trust boundaries."

4. Request (specific, actionable)
   "Let's add input validation to the PR template acceptance criteria
   and the code review checklist. Agreed?"

5. Support offer
   "Happy to run a short session on the validation patterns we use."
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] team-coaching-engineering-culture | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: brief description
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] team-coaching-engineering-culture | outcome: OK | next: none | note: Q1 retro run; Team Health Snapshot produced; 2 growth plan items updated
[2026-04-20] team-coaching-engineering-culture | outcome: PARTIAL | next: team-coaching-engineering-culture | note: retro run but Engineering Norms Doc not updated — schedule follow-up
```

---

## Output format

### Team Health Snapshot

Saved as `docs/team-health-YYYY-QN.md`. Filled in from `references/team-health-snapshot-template.md`. A completed snapshot looks like this:

```
## Team Health Snapshot: Q1 2026

**Date:** 2026-04-20
**Retro participants:** Alice, Ben, Caro

### Velocity (DORA — from delivery-metrics-dora)
| Metric | This quarter | Last quarter | Trend |
|--------|-------------|-------------|-------|
| Deployment frequency | 8/month | 6/month | Up |
| Lead time (idea to prod) | 4 days | 6 days | Down (good) |
| Change failure rate | 4% | 7% | Down (good) |
| MTTR | 45 min | 90 min | Down (good) |

### Quality signals
| Signal | Value | Notes |
|--------|-------|-------|
| Test coverage (overall) | 74% | +3% vs last quarter |
| PR cycle time (open to merge) | 1.8 days | Target: <2 days — on track |
| Review turnaround (request to first review) | 0.9 days | Target: <1 day — on track |

### Team satisfaction (from retro)
- What went well: faster deployment pipeline, pair session on auth system paid off
- Main friction: unclear ownership on the metrics dashboard; review backlog during holidays

### Risks
| Risk | Severity | Owner | Mitigation |
|------|----------|-------|-----------|
| Only Ben can deploy to prod | High | Alice | Pair deploy session scheduled for April |
| No runbook for cache invalidation | Medium | Caro | Write runbook by end of quarter |

### Action items from retro
| Item | Owner | Due |
|------|-------|-----|
| Pair deploy session: Alice shadows Ben | Alice + Ben | 2026-04-30 |
| Write cache invalidation runbook | Caro | 2026-05-15 |
| Add "ownership" column to services table in docs | Ben | 2026-04-30 |
```

### Growth Plan (per person, updated quarterly)

```
## Growth plan: Alice

**Last updated:** 2026-04-20

| Goal | Measurable milestone | Target | Status |
|------|---------------------|--------|--------|
| Own an architectural decision end-to-end | Design and ship the metrics pipeline redesign; produce ADR | Q2 2026 | In progress |
| Reduce PR review turnaround | From 2.1 days to <1 day; measured monthly | Q3 2026 | Open |
```

---

## Reference files

- `references/team-health-snapshot-template.md` — fillable template for the quarterly Team Health Snapshot; complete after each retro in ~20 minutes
