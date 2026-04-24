---
name: developer-onboarding
description: >
  Activate when a new engineer is joining, re-onboarding after extended leave, or the team needs
  to codify engineering norms. Triggers include "new engineer joining", "onboarding checklist",
  "local dev setup", "engineering norms", "engineering handbook", "first week tasks", and
  "knowledge transfer to new hire". Produces day 1 / week 1 / month 1 checklists, a tool-pinned
  local development setup, and an engineering norms doc the whole team agrees on.
---

# Developer onboarding

## Purpose

A new engineer should be productive in week one, not week six. This skill defines the mechanics: day 1 access and laptop, week 1 first ship, month 1 first feature and oncall shadow. It also codifies the implicit engineering norms (PR size, commit format, branching, review expectations) that every team has but few write down. Every onboarding ends with a retro that feeds back into the docs — so next hire has a better experience than this one. No hazing, no throwing someone into the deep end, no "read the code and figure it out".

---

## When to use

- Every time a new engineer joins — no exceptions, even for senior hires
- Re-onboarding after extended leave (parental leave, sabbatical, long medical leave): environment, access, and norms have all drifted
- After recurring friction that stems from an undocumented norm ("I didn't know PRs should stay under 400 lines")
- Annual review of engineering norms: are they still the right ones? Do they reflect how we actually work now?
- When moving a team member to a new service area they haven't owned before (a scoped mini-onboarding)

---

## When NOT to use

- **Ongoing team health, quarterly retros, culture coaching** → `team-coaching-engineering-culture`. That skill covers how the team functions over time; this one covers how new members get up to speed.
- **System architecture documentation, runbooks, ADR catalog** → `documentation-system-design`. Onboarding points new engineers *at* the system docs; it does not produce them.
- **Off-boarding, handover at project end, final knowledge transfer out** → `project-closeout`. That is the mirror skill: someone leaving, not someone arriving.
- **Performance management or underperformance after onboarding** → out of scope. That belongs to a human manager conversation, not this skill.

---

## Process or checklist

### Step 1 — Before day 1 (owner: hiring manager, 30 min, done the week before start)

- Assign an onboarding buddy (senior engineer, not the hiring manager). Buddy commits 2h on day 1 and 1h/day for the first week.
- Pre-provision access: GitHub/GitLab org, Slack, cloud console (read-only first, write later), password manager, VPN, docs wiki, PagerDuty (shadow-only), AI coding tool licence.
- Laptop arrives before start date. Do not let day 1 be "waiting for hardware".
- Select the first meaningful task: a real bug or a small user-visible change that exercises the full pipeline (local dev → PR → review → CI → deploy → prod). Not a fake "intro task". Budget 2–5 days.
- Send the welcome doc: links to INDEX of services, engineering norms, local dev setup, team directory, on-call rotation calendar.

### Step 2 — Day 1 checklist (owner: new engineer + buddy, target: one commit in main by end of day)

Run through `references/week-one-checklist.md` day 1 section. Core targets:
- Laptop set up: dotfiles, editor, terminal, SSH keys registered.
- Repo cloned; local dev stack (Docker Compose or equivalent) running; seed data loaded.
- All access confirmed by actually logging in, not by "I have the invite".
- One "hello world" change committed, reviewed, merged to main by end of day. Could be a typo fix, a dependency bump, or a README improvement. The point is exercising the pipeline.

### Step 3 — Week 1 checklist (owner: new engineer, buddy pairs daily)

- Complete the first meaningful task all the way to production. Every step counts: PR, review, CI green, deploy, verify in prod.
- Pair with 3 different engineers on 3 different services. Goal: see how different domains of the codebase work, not just the one you'll own.
- Read the top 5 ADRs (listed in `references/week-one-checklist.md`). Ask the buddy what has changed since they were written.
- Attend one oncall handover meeting as an observer.
- Shadow a code review on someone else's PR (screen-share, not async).

### Step 4 — Month 1 checklist (owner: new engineer, buddy weekly 1:1)

- Ship one user-facing feature end-to-end (design input, code, tests, deploy, observe in prod).
- Shadow one oncall shift. Do not get paged yet; observe the primary handling alerts.
- Own one runbook: either write a new one, or take over an existing one and bring it current.
- Participate in one architecture review (as a reviewer, not author).
- Give one demo at the team sync.

### Step 5 — Onboarding retros (owner: new engineer, facilitator: buddy)

Run a 20-minute retro at **week 2** and **month 1**. Structure:
- What worked? (keep doing)
- What was confusing or slow? (fix in docs)
- What was missing? (add to checklist)
- One specific change the new engineer will make to `references/week-one-checklist.md` or `docs/engineering-norms.md` before closing the retro. No retro ends without at least one doc edit.

This is how the onboarding improves over time. Every hire leaves it better than they found it.

### Step 6 — Update the engineering norms doc

The first time a new engineer asks "how big should my PR be?" or "should I squash commits?" the answer must exist in `docs/engineering-norms.md`. If the norm is implicit, make it explicit now — do not wait for the next hire. Use `references/engineering-norms-template.md` as the starting point. The doc is owned by the whole team; changes go through a PR with one-reviewer approval.

---

## Output format with real examples

### Day 1 checklist (extracted from week-one-checklist.md)

```
## Day 1 — Alice Chen, 2026-04-20

Buddy: Ben (paired 10am–12pm, 2pm–3pm)

Morning:
- [x] Laptop unboxed; FileVault enabled; SSO logged in
- [x] GitHub access verified (cloned monorepo)
- [x] Slack: joined #eng, #eng-alerts, #team-platform
- [x] 1Password vault shared; all team secrets visible
- [x] VPN connected; AWS console read-only access confirmed

Afternoon:
- [x] Docker Compose stack up; seed data loaded; local API returns 200 on /healthz
- [x] First PR opened: fixed typo in API README (PR #4821)
- [x] PR merged by Ben at 16:40
- [x] Deploy to staging observed (pipeline green)
- [x] End-of-day: posted intro message in #eng

Blocked on: none
Tomorrow: pair with Caro on auth-service local setup
```

### Week-one-checklist.md entry (week 1 pairing log)

```
## Week 1 pairing log

| Day | Paired with | Service | Activity | Takeaway |
|-----|-------------|---------|----------|----------|
| Tue | Ben | api-gateway | local dev walkthrough | config loading is env-based, not file-based |
| Wed | Caro | auth-service | JWT verification flow | key rotation is automated via KMS |
| Thu | Dan | billing | invoice pipeline | async job queue uses NATS, not Kafka |
```

### Engineering norms sample (from engineering-norms-template.md)

```
## Engineering norms — Platform team

Last reviewed: 2026-04-01. Owner: whole team. Changes via PR.

### PRs
- Max 400 lines of production code (excluding lock files, generated code). Split anything larger.
- One non-author review required before merge.
- Review turnaround target: same business day for PRs < 200 lines; ≤ 24h for larger.
- Squash on merge. Branch names: `<initials>/<short-desc>`.

### Commits
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Commit message body explains *why*, not *what*. The diff shows what.

### Branching
- Trunk-based. No long-lived feature branches.
- Feature flags (see `feature-flag-lifecycle`) for anything not ready to be on in prod.

### Code style
- Formatter is non-negotiable. Pre-commit hook runs `<formatter>` — no manual style debates.
- Linter warnings block CI when count > baseline.
```

---

## Skill execution log

Every firing appends one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] developer-onboarding | outcome: OK|BLOCKED|PARTIAL | next: <skill> | note: <brief>
```

Examples:
```
[2026-04-20] developer-onboarding | outcome: OK | next: none | note: Alice day 1 complete; first PR merged; paired with Ben 4h
[2026-05-04] developer-onboarding | outcome: PARTIAL | next: developer-onboarding | note: Alice week 2 retro — added 3 fixes to week-one-checklist.md; month 1 retro scheduled
[2026-04-01] developer-onboarding | outcome: OK | next: none | note: annual norms review; updated PR size limit 300→400 lines
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

---

## Reference files

- `references/week-one-checklist.md` — fillable day 1 / week 1 / month 1 checklist. One file per hire, saved to `docs/onboarding/<name>-<start-date>.md`. Owner: the new engineer, reviewed daily with the buddy in week 1.
- `references/engineering-norms-template.md` — starting point for the team's `docs/engineering-norms.md`. Covers PR size, commit format, branching, review expectations, code style, on-call, pairing cadence. Team fills in specifics; do not ship the template unchanged.
- `references/local-dev-setup-patterns.md` — patterns for a reproducible local dev environment: Docker Compose stack, asdf/mise tool version pinning, secrets for local dev, seed data, the `hello-world` smoke test. A new engineer should have the stack running in under 90 minutes on day 1.
