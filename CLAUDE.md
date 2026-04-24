# sdlc-skills-library — 41-skill Claude skills library

This repo is a skills library for a small, high-velocity engineering team (3–5 senior engineers). It contains 41 production-ready skill packages that Claude loads on demand to assist with every phase of software development, plus 10 domain **tracks** that overlay the library for specific domains.

**Philosophy: move fast, leave a trail.** Strip ceremony. Keep discipline. Every skill produces a concrete output that unblocks the next stage. No theatre.

---

## Library structure

```
skills/
  workflow/         — sdlc-orchestrator: master pipeline conductor
  phase1/           — Foundation: establish what is being built and why (10 skills)
  phase2/           — Delivery quality: day-to-day implementation standards (20 skills)
  phase3/           — Sustained operations: post-go-live and continuous improvement (9 skills)
  phase4/           — Advanced assurance: critical systems only (1 skill)
  tracks/           — 10 domain overlays (Fintech, SaaS B2B, Healthcare, etc.)
docs/
  modes.md          — operating modes (Nano/Lean/Standard/Rigorous)
  tracks.md         — domain tracks overlay
  quickstart.md     — decision tree: where to start
  skill-triggers.md — trigger phrase reference
  skill-log.md      — append-only execution log (every skill firing is recorded here)
  sdlc-status.md    — current pipeline stage and status
```

Full skill list: `skills/INDEX.md`
When to use which skill: `skills/MASTER-GUIDE.md`
When to activate which track: `docs/tracks.md` and `skills/tracks/CLAUDE.md`

---

## Modes vs tracks — the two dimensions

- **Mode** answers *how much rigor*: Nano / Lean / Standard / Rigorous. Every session is in exactly one mode. Mode controls which base skills run and how hard the gates are.
- **Track** answers *what domain*: Fintech / SaaS B2B / Healthcare / Regulated / Data platform / Real-time / Consumer / Open-source / Mobile / Web product. Zero or more tracks per session. Tracks elevate mandatory skills, tighten gate criteria, and inject domain reference material.
- **Workflow path** (Hotfix / Spike / Brownfield) is a third, orthogonal concept — it modifies *which stages run*, not which skills or how strict gates are.

All three compose: `Lean mode + Fintech track + Hotfix path` is valid and meaningful.

---

## The skill template contract

Every `SKILL.md` must contain these sections in order:

1. **YAML frontmatter** — `name:` and `description:` (description = the trigger phrases that cause this skill to fire in Claude's context)
2. **Purpose** — one paragraph, plain English, what this skill does and why it exists
3. **When to use** — specific situations, triggers, signals
4. **When NOT to use** — adjacent situations that belong to a different skill. This section is non-negotiable; without it, skills bleed into each other.
5. **Process or checklist** — the actual steps, ordered, actionable
6. **Output format with real examples** — show what a good output looks like, not just describe it
7. **Skill execution log section** — a reminder to append to `docs/skill-log.md`
8. **Reference files section** — point to the `references/` directory and list what each file contains

When editing a SKILL.md, check that all 8 sections are present. Do not merge sections or mark any as optional.

---

## The track template contract

Every `TRACK.md` has a parallel 8-section structure:

1. **YAML frontmatter** — `name:` and `description:` (activation phrases and domain fingerprint)
2. **Purpose** — what domain this track covers and why it needs specialization
3. **When to activate** — specific signals and phrases
4. **When NOT to activate** — adjacent domains that belong to a different track
5. **Skill elevations** — table: which skills become mandatory per mode
6. **Gate modifications** — table: which stage gates tighten, new required evidence
7. **Reference injection map** — when skill X fires during this track, also load reference Y
8. **Reference files** — list of `references/*.md` with one-line descriptions

Template: `skills/tracks/TRACK-TEMPLATE.md`. Validator: `scripts/track_validator.py`. Elevation checker: `scripts/check_track_elevations.py`.

---

## Skill execution log

Every time a skill fires, it appends one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] skill-name — brief description of what was done
```

Example:
```
[2025-11-14] prd-creator — created PRD for auth service revamp (Mode A)
[2025-11-14] requirements-tracer — decomposed 7 stories into BDD acceptance criteria
[2025-11-15] design-doc-generator — synthesised PRD + specs into DESIGN.md
```

This log is the audit trail. Never delete entries. The sdlc-orchestrator reads it to verify stage completion.

---

## What NOT to write

These skills are for a small engineering team doing hands-on work. Do not write:

- Cross-company engagement framing ("both companies", "the partner company")
- Enterprise ceremony ("steering committee", "formal escalation", "contractual deliverable language")
- Role descriptions that assume a large org ("project manager", "account executive")
- Passive voice hedging ("it may be appropriate to consider...")

Write for a senior engineer who wants to know exactly what to do and why.

---

## Key files

- `skills/INDEX.md` — full skill list with directories and one-line descriptions
- `skills/MASTER-GUIDE.md` — when to use each skill, when NOT to, and what you get
- `docs/modes.md` — the four operating modes
- `docs/tracks.md` — the ten domain tracks
- `docs/quickstart.md` — decision tree for picking mode + track
- `docs/skill-triggers.md` — natural-language phrases that fire each skill / track
- `skills/tracks/CLAUDE.md` — track index and invariants

---

## Author and license

Authored by **Thanassis Zografos** — S3Nex Ltd (<tzografos@gmail.com> · <tz@s3nex.com> · [linkedin.com/in/sonaht](https://www.linkedin.com/in/sonaht/)). Licensed under MIT — see `LICENSE`. Free to use, modify, and redistribute; only requirement is to preserve the copyright notice.
