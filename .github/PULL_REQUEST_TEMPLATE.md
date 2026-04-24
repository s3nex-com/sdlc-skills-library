## What does this PR do?

<!-- One paragraph summary of the change and why it's being made. -->

## Type of change

<!-- Check all that apply -->

- [ ] New skill
- [ ] New domain track
- [ ] Reference file addition or improvement
- [ ] Script fix or enhancement
- [ ] CI improvement
- [ ] Bug fix
- [ ] Other (describe below)

## Affected skills / tracks

<!-- List the skill or track directories this PR touches, e.g. skills/phase2/database-migration/ -->

## Local CI — all must pass before submitting

- [ ] `python3 scripts/skill_health.py` — PASS
- [ ] `python3 scripts/track_validator.py` — PASS
- [ ] `python3 scripts/check_track_elevations.py` — PASS
- [ ] `python3 scripts/check_reference_links.py` — PASS
- [ ] `python3 scripts/check_index.py` — PASS
- [ ] `ruff check .` — PASS

## Template contract (if adding or editing a SKILL.md)

- [ ] YAML frontmatter present (`name:` and `description:`)
- [ ] Purpose section present
- [ ] When to use section present
- [ ] **When NOT to use** section present
- [ ] Process or checklist section present
- [ ] Output format with real examples present
- [ ] Skill execution log section present
- [ ] Reference files section present
- [ ] At least one file exists in `references/`
- [ ] Skill added to `skills/INDEX.md` and `skills/CLAUDE.md`

## Template contract (if adding or editing a TRACK.md)

- [ ] YAML frontmatter present
- [ ] Purpose section present
- [ ] When to activate section present
- [ ] When NOT to activate section present
- [ ] Skill elevations table present
- [ ] Gate modifications table present
- [ ] Reference injection map present
- [ ] Reference files section present
- [ ] Track added to `skills/INDEX.md` and `skills/tracks/CLAUDE.md`
