# Week-one checklist — fillable template

Copy this file to `docs/onboarding/<name>-<start-date>.md` on the new engineer's first day. The new engineer owns the file; the buddy reviews it daily in week 1. Check items off as they are completed. Do not backdate — if something slipped to day 3, record day 3.

---

## Metadata

- **Name:**
- **Start date:**
- **Team:**
- **Buddy:**
- **Hiring manager:**
- **First meaningful task (pre-selected by hiring manager):**

---

## Day 1 — access, laptop, hello world

Goal: one commit in `main` by end of day. The point is exercising the full pipeline, not the size of the change.

### Morning (access and laptop)
- [ ] Laptop unboxed; disk encryption enabled; password manager installed
- [ ] SSO signed in (Google/Okta/Entra as applicable)
- [ ] GitHub/GitLab org access confirmed: clone the main monorepo successfully
- [ ] Slack: joined `#eng`, `#eng-alerts`, team channel, social channel
- [ ] Password manager vault shared; all team secrets visible (don't read them, just confirm access)
- [ ] VPN connected (if applicable); cloud console read-only access confirmed
- [ ] Docs wiki access (Notion/Confluence/whatever); can open the INDEX page
- [ ] AI coding tool licence activated (Claude Code, Copilot, Cursor — whichever the team uses)
- [ ] PagerDuty account created, set to shadow-only for now

### Afternoon (local dev and first commit)
- [ ] Follow `references/local-dev-setup-patterns.md` steps
- [ ] Local dev stack running: `curl localhost:<port>/healthz` returns 200
- [ ] Seed data loaded; can log in to the local app as a test user
- [ ] Run the full test suite locally: all green
- [ ] Pick a trivial fix: typo, dead link, outdated comment, lint warning
- [ ] Open a PR
- [ ] Buddy reviews and approves
- [ ] PR merges; CI green; deploy to staging observed
- [ ] End-of-day: post a short intro in the team channel

**Blockers encountered:**
**Things that took longer than expected (feeds back into onboarding docs):**

---

## Week 1 — ship one real thing, pair broadly

Goal: the first meaningful task reaches production, and you've seen 3 different areas of the codebase.

### First meaningful task (production)
- [ ] Task understood; acceptance criteria clear
- [ ] Design discussed with buddy (even a 10-minute whiteboard)
- [ ] Code written
- [ ] Tests written (unit + integration as applicable)
- [ ] PR opened; under 400 lines; clear description
- [ ] Review feedback addressed
- [ ] Merged; deployed; verified in production
- [ ] Short note in team channel confirming it shipped

### Pairing — 3 engineers, 3 services
| Day | Paired with | Service | Activity | Key takeaway |
|-----|-------------|---------|----------|--------------|
|     |             |         |          |              |
|     |             |         |          |              |
|     |             |         |          |              |

### Reading — top 5 ADRs

Team maintains a `docs/adr/` directory. Read these five first. Ask the buddy which are still current:
- [ ] ADR #__ — __
- [ ] ADR #__ — __
- [ ] ADR #__ — __
- [ ] ADR #__ — __
- [ ] ADR #__ — __

### Observations
- [ ] Attended one oncall handover meeting as observer
- [ ] Shadowed one live code review (screen-share)
- [ ] Attended the team weekly sync

---

## Week 2 retro (20 min, with buddy)

Do this before leaving on Friday of week 2. Record:

- **What worked?** (things to keep doing for the next hire)
- **What was confusing or slow?** (fix in docs now)
- **What was missing?** (add to the checklist now)
- **Doc edit made before closing the retro:** (PR link)

No retro ends without at least one concrete doc change. This is the feedback loop. If nothing changed, the retro didn't happen.

---

## Month 1 — feature, oncall shadow, runbook

Goal: ship a user-facing feature; shadow one oncall shift; own one runbook.

### Feature ship
- [ ] Feature scoped with engineering lead / PM
- [ ] Design input given (even if small)
- [ ] Code written, tested, reviewed, merged, deployed
- [ ] Observed in prod: metrics look right, no error spike
- [ ] Demo given at team sync

### Oncall shadow
- [ ] Shadowed one full primary shift (no paging yet)
- [ ] Reviewed at least one real alert with the primary
- [ ] Read the relevant runbooks for the alerts that fired

### Runbook ownership
- [ ] Picked one runbook to own (new or existing)
- [ ] If new: wrote it end-to-end
- [ ] If existing: brought it current; removed stale steps; tested the documented recovery
- [ ] PR merged; runbook linked from the service's README

### Architecture review
- [ ] Participated in one architecture review as a reviewer (not author)

---

## Month 1 retro (20 min, with buddy)

Same structure as week 2 retro. Outputs:

- **What worked?**
- **What was confusing or slow?**
- **What was missing?**
- **Doc edit made before closing the retro:** (PR link)
- **Ready to go on primary oncall rotation?** Yes / No / When:
- **Ready to close this onboarding file?** Yes / No

If yes: archive to `docs/onboarding/archive/<name>-<start-date>.md` and note the archive in `docs/skill-log.md`.
