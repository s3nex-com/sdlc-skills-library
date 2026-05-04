# Skill library — evaluation fixtures

This directory holds **runtime evaluation scenarios** for the skill library. These are distinct from the packaging checks in `scripts/` (which verify Markdown structure and link hygiene). These fixtures test whether a model loaded with a given `SKILL.md` actually behaves correctly: routing, guardrails, artefact shape, and gate enforcement.

See the full methodology: [`docs/improvements/skill-library-validation/plan.md`](../docs/improvements/skill-library-validation/plan.md)

---

## Directory layout

```
tests/
  scenarios/
    golden/          ← 10 high-leverage scenarios, one per skill (Step 1)
  rubrics/           ← binary rubric checklists for G-type scenarios (Step 2+)
```

---

## Scenario YAML schema

Every file under `scenarios/` must conform to this shape:

```yaml
id: S-XX                          # unique scenario ID matching plan.md
name: kebab-case-slug             # human-readable slug
description: >-                   # one-line description
  ...
tag: G | C | K                   # correctness category (see below)
skill: skill-kebab-name           # which skill this scenario targets
skill_directory: skills/phase/x/  # relative path to the SKILL.md directory
mode: nano | lean | standard | rigorous
tracks: []                        # list of track names, empty if none
workflow_path: null | hotfix | spike | brownfield
user_prompt: |                    # exact prompt to replay
  ...
context:
  artifact_fixture: null | path   # optional fixture file injected as context
  skill_load_path: path/SKILL.md  # path used by the harness to load the skill
expected_primary_skill: name      # which skill must fire
oracle:
  kind: structure | rubric | tool_backed | process
  script: null | path/to/script   # for tool_backed oracles
  structure_rules:
    required_sections: []         # headings or bold labels that must appear
    required_phrases: []          # keywords or phrases that must appear
    forbidden_phrases: []         # phrases that must NOT appear
  rubric_id: null | R-XX          # links to tests/rubrics/R-XX.yaml
notes: >-                         # what this scenario validates and why
  ...
```

---

## Tags

| Tag | Meaning |
|-----|---------|
| **G** | **Guardrail** — correct skill boundary, redirect on wrong-skill signal, refusal to skip gates, blameless tone. |
| **C** | **Completion** — artefact matches the skill's output contract (sections, decisions, traceability). |
| **K** | **Code** — generated code/scripts pass build, lint, or script-backed validators. |

---

## Oracle kinds

| Kind | How it works |
|------|--------------|
| `structure` | Assert presence/absence of headings and phrases in the model response. Automatable with regex. |
| `rubric` | Human-graded binary checklist stored in `tests/rubrics/R-XX.yaml`. Used for G scenarios where structure alone is insufficient. |
| `tool_backed` | Extract an artefact from the response, write to `tmp/`, run the referenced script, check exit code. |
| `process` | Score whether each checklist step from the skill was addressed or explicitly waived with reason. |

---

## Running scenarios

```bash
# Install dependencies
pip install anthropic pyyaml

# Set API key
export ANTHROPIC_API_KEY=sk-...

# Dry run — load all golden scenarios, skip API calls
python scripts/run_eval.py --dry-run

# Run all 10 golden scenarios
python scripts/run_eval.py

# Run a single scenario
python scripts/run_eval.py --scenario S-02

# JSON report
python scripts/run_eval.py --json --output-dir tmp/

# Different model
python scripts/run_eval.py --model claude-opus-4-7
```

Outputs land in `tmp/` (gitignored):
- `tmp/transcripts/{id}.json` — full prompt + response per scenario
- `tmp/artifacts/{id}-output.yaml` — extracted code artifact (tool_backed scenarios only)
- `tmp/rubrics/{id}-review.md` — human-review checklist (rubric scenarios)
- `tmp/report.json` — machine-readable results for all scenarios

---

## Full scenario set — 40 scenarios (4 per skill)

| ID | Skill | Tag | Oracle |
|----|-------|-----|--------|
| S-01 | sdlc-orchestrator | G | structure |
| S-02 | sdlc-orchestrator | C | structure |
| S-03 | sdlc-orchestrator | G | structure |
| S-04 | sdlc-orchestrator | C | structure |
| S-05 | prd-creator | C | structure |
| S-06 | prd-creator | G | structure |
| S-07 | prd-creator | G | structure |
| S-08 | prd-creator | C | structure |
| S-09 | requirements-tracer | C | structure |
| S-10 | requirements-tracer | G | rubric → R-10 |
| S-11 | requirements-tracer | C | structure |
| S-12 | requirements-tracer | G | structure |
| S-13 | specification-driven-development | C | tool_backed → validate_openapi.py |
| S-14 | specification-driven-development | K | tool_backed → validate_openapi.py |
| S-15 | specification-driven-development | G | structure |
| S-16 | specification-driven-development | C | structure |
| S-17 | security-audit-secure-sdlc | C | structure |
| S-18 | security-audit-secure-sdlc | G | structure |
| S-19 | security-audit-secure-sdlc | C | structure |
| S-20 | security-audit-secure-sdlc | G | structure |
| S-21 | database-migration | C | structure |
| S-22 | database-migration | K | tool_backed → migration_risk.py |
| S-23 | database-migration | G | structure |
| S-24 | database-migration | C | structure |
| S-25 | code-implementer | C | structure |
| S-26 | code-implementer | G | rubric → R-26 |
| S-27 | code-implementer | C | structure |
| S-28 | code-implementer | K | rubric → R-28 |
| S-29 | code-review-quality-gates | C | structure |
| S-30 | code-review-quality-gates | G | structure |
| S-31 | code-review-quality-gates | C | structure |
| S-32 | code-review-quality-gates | G | structure |
| S-33 | incident-postmortem | C | structure |
| S-34 | incident-postmortem | G | rubric → R-34 |
| S-35 | incident-postmortem | G | structure |
| S-36 | incident-postmortem | C | structure |
| S-37 | design-doc-generator | C | structure |
| S-38 | design-doc-generator | G | structure |
| S-39 | design-doc-generator | C | structure |
| S-40 | design-doc-generator | G | structure |
