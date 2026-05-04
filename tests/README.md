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

## Running scenarios (harness not yet built)

Step 2 of the implementation plan will build `scripts/run_eval.py`. Until then:

1. Load the skill file at `context.skill_load_path` as the system prompt.
2. Send `user_prompt` to the model with the specified `mode` and `tracks` as injected context.
3. Evaluate the response against `oracle` rules.
4. For `tool_backed` oracles: extract the artefact block from the response and pipe it through `oracle.script`.

---

## Golden set — 10 scenarios (one per high-leverage skill)

| ID | Skill | Tag | Oracle |
|----|-------|-----|--------|
| S-02 | sdlc-orchestrator | C | structure |
| S-05 | prd-creator | C | structure |
| S-09 | requirements-tracer | C | structure |
| S-13 | specification-driven-development | C | tool_backed |
| S-17 | security-audit-secure-sdlc | C | structure |
| S-21 | database-migration | C | structure |
| S-26 | code-implementer | G | rubric |
| S-29 | code-review-quality-gates | C | structure |
| S-34 | incident-postmortem | G | rubric |
| S-37 | design-doc-generator | C | structure |
