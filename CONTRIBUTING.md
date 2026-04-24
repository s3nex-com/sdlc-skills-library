# Contributing to sdlc-skills-library

Thank you for your interest in contributing. This document covers everything you need to know before opening a PR.

---

## What contributions are welcome

- **New skills** — a well-scoped skill package with all 8 required sections, at least one reference file, and a clear "When NOT to use" section
- **New domain tracks** — a new `TRACK.md` following the track template contract, with reference files
- **Reference file improvements** — expanding, correcting, or updating content in `references/` files
- **Bug fixes** — broken links, incorrect section content, script errors
- **Script improvements** — enhancements to existing scripts in `scripts/` or skill-level `scripts/`
- **CI improvements** — new checks that catch real problems

## What will not be accepted

- Skills or tracks that duplicate existing ones without clear differentiation
- Content written for large enterprise orgs (steering committees, formal escalation chains, contractual deliverable language) — this library targets small engineering teams
- Reference files that belong in a different skill's scope — check the "When NOT to use" section of adjacent skills before adding content
- Passive-voice hedging ("it may be appropriate to consider...") — write for a senior engineer who wants to know exactly what to do
- Changes that break the template contract without updating the contract itself

---

## How to contribute

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/sdlc-skills-library.git
cd sdlc-skills-library
```

### 2. Create a branch

Use a descriptive branch name:

```bash
git checkout -b add-skill-<skill-name>
git checkout -b fix-<what-is-broken>
git checkout -b improve-<skill-name>-references
```

### 3. Make your changes

**Adding a skill:**
- Create `skills/phase<N>/<skill-name>/SKILL.md` following the 8-section template contract (see `skills/MASTER-GUIDE.md`)
- Add at least one file in `references/`
- Add the skill to `skills/INDEX.md` and `skills/CLAUDE.md`

**Adding a track:**
- Create `skills/tracks/<track-name>/TRACK.md` following the 8-section track template (see `skills/tracks/TRACK-TEMPLATE.md`)
- Add at least one reference file
- Add the track to `skills/INDEX.md` and `skills/tracks/CLAUDE.md`
- Add keyword triggers to `scripts/track_advisor.py`

**Editing reference files:**
- Keep content actionable and concrete — templates, worked examples, decision tables
- No multi-paragraph prose that doesn't lead to a decision or an action

### 4. Run the CI checks locally

```bash
pip install -r requirements.txt

python3 scripts/skill_health.py
python3 scripts/track_validator.py
python3 scripts/check_track_elevations.py
python3 scripts/check_reference_links.py
python3 scripts/check_index.py
ruff check .
```

All checks must pass before submitting. PRs with failing CI will not be reviewed.

### 5. Open a pull request

Push your branch to your fork and open a PR against `master`. Fill in the PR template — it only takes 2 minutes and makes review faster.

---

## Skill template contract

Every `SKILL.md` must contain these 8 sections in order:

1. YAML frontmatter (`name:` and `description:`)
2. Purpose
3. When to use
4. When NOT to use
5. Process or checklist
6. Output format with real examples
7. Skill execution log section
8. Reference files section

The CI `skill_health.py` check will fail if any section is missing.

## Track template contract

Every `TRACK.md` must contain these 8 sections in order:

1. YAML frontmatter
2. Purpose
3. When to activate
4. When NOT to activate
5. Skill elevations
6. Gate modifications
7. Reference injection map
8. Reference files

The CI `track_validator.py` check will fail if any section is missing.

---

## Questions

Open a GitHub Discussion or file an issue. Do not email directly for contribution questions — keeping the conversation in GitHub means others can benefit from the answer.
