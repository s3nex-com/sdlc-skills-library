# Improvements and backlog docs

Tracked design notes that extend the skill library beyond what CI enforces today.

| Topic | Document | Status |
|--------|----------|--------|
| Runtime evaluation of skill behaviour — methodology, oracles, 40-scenario set, harness, and CI workflow | [skill-library-validation/plan.md](skill-library-validation/plan.md) | **Complete** |

## What was built

All three implementation steps are done. The eval system lives in `tests/` and `scripts/`:

| Artefact | Path | Description |
|----------|------|-------------|
| Scenario fixtures | `tests/scenarios/golden/` | 40 YAML scenarios (S-01–S-40), 4 per skill, 10 skills |
| Rubric stubs | `tests/rubrics/` | 4 binary rubrics for G/K scenarios (R-10, R-26, R-28, R-34) |
| Eval harness | `scripts/run_eval.py` | Replays scenarios against Claude API, runs oracles, emits report |
| Oracle modules | `scripts/oracles/` | structure, tool_backed, rubric |
| CI workflow | `.github/workflows/eval.yml` | Manual trigger via Actions UI; optional scenario ID and model inputs |
| Schema docs | `tests/README.md` | YAML schema, oracle kinds, run instructions |

To run: GitHub → Actions → "Skill eval (manual)" (requires `ANTHROPIC_API_KEY` repo secret).
Local dry-run (no API cost): `python3 scripts/run_eval.py --dry-run`
