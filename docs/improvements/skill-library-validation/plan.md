# Skill library — runtime validation and verification plan

**Status:** All steps complete — full 40-scenario set written, harness built, CI workflow live. Run via Actions → "Skill eval (manual)".  
**Purpose:** Preserve how we would prove that loading these skills yields **correct guardrails** and **completed tasks** under real session composition (mode, tracks, workflow path), separately from Markdown packaging checks.

---

## 1. Purpose and scope

### What is under test

Treat the skill library as exercising a **system**:

`model + loaded SKILL.md (+ references as needed) + session context`

Session context includes **mode** ([docs/modes.md](../../modes.md)), **zero or more tracks** ([docs/tracks.md](../../tracks.md)), workflow path (e.g. Hotfix / Spike / Brownfield per orchestrator), and user scenario.

Outputs to evaluate fall into:

- **Guidance** — routing, “when NOT to use” behaviour, proportional rigor.
- **Artefacts** — PRDs, requirements matrices, specs, DESIGN sections, migration plans, review commentary.
- **Code** — snippets or full files that ought to honour the same gates the skill describes.

This plan does **not** replace reading each `SKILL.md`; it describes how to turn those files into **testable expectations**.

### What is already covered (packaging vs runtime)

| Layer | What it proves | Where |
|--------|----------------|--------|
| **Contract** | YAML, eight sections, stale refs | [scripts/skill_health.py](../../../scripts/skill_health.py) |
| **Tracks** | TRACK template, elevations | [scripts/track_validator.py](../../../scripts/track_validator.py), [scripts/check_track_elevations.py](../../../scripts/check_track_elevations.py) |
| **Links / index** | Reference files exist, INDEX sync | [scripts/check_reference_links.py](../../../scripts/check_reference_links.py), [scripts/check_index.py](../../../scripts/check_index.py) |
| **CI** | All of the above on push/PR | [.github/workflows/ci.yml](../../../.github/workflows/ci.yml) |

That pipeline validates **library hygiene**. **Runtime quality** — whether Claude (or another model) behaves as intended when a skill fires — requires the methodology below.

---

## 2. Specification strategy

Before writing scenarios:

1. **Per skill:** From each [`SKILL.md`](../../../skills/INDEX.md), extract a concise **behaviour spec**: mandatory checklist steps, promised output shape, explicit “When NOT to use” redirects, and normative bullets in `references/`.
2. **Cross-skill:** Use [skills/MASTER-GUIDE.md](../../../skills/MASTER-GUIDE.md) and [skills/workflow/sdlc-orchestrator/](../../../skills/workflow/sdlc-orchestrator/) for **ordering, gates, and handoffs**, so multi-stage tests know what “done” means beyond a single skill.

Without this step, “expected behaviour” stays subjective.

---

## 3. Dual correctness model

Use **three scenario tags**:

| Tag | Meaning |
|-----|---------|
| **G** | **Guardrail** — correct skill boundary, redirects, refusal to skip gates, tone (e.g. blameless incident). |
| **C** | **Completion** — artefact matches the skill’s output contract (sections, decisions, traceability). |
| **K** | **Code** — generated code/scripts can be enforced with build, tests, or bundled validators. |

**A. Guardrail correctness:** Right skill framing for “when to use,” clear redirect for “when NOT to use,” mode/track honoured when injected.

**B. Task-completion correctness:** Artefacts and code match the skill’s **Output format** and survive **tool-backed** checks where scripts exist.

Keep **G** and **B** distinguishable in reports; confusing them obscures regressions.

---

## 4. Scenario matrix dimensions

Design cases along (sample each axis; prioritise risky combinations):

- **Skill** — different contracts per package.
- **Polarity** — happy path, ambiguous, wrong-skill signal, user demands unsafe shortcut.
- **Mode** — Nano / Lean / Standard / Rigorous ([docs/modes.md](../../modes.md)).
- **Track overlay** — e.g. `tracks/fintech-payments` vs none ([docs/tracks.md](../../tracks.md)).
- **Workflow path** — Hotfix, Spike, Brownfield implications from orchestrator.
- **Artefact depth** — greenfield vs brownfield vs incident vs empty inputs.

Minimum per skill for a meaningful slice: **one canonical C**, **one guardrail G (when NOT)**, **one stress** scenario (contradictions or missing info).

---

## 5. Oracle types

| Oracle | Use for | Automation |
|--------|---------|------------|
| **Structure** | Most **C** and narrative parts of **K** | Assertions on headings/phrases mandated by each skill’s Output section (regex or lightweight parsing). Optional: forbid phrases that violate authoring rules ([CLAUDE.md](../../../CLAUDE.md)). |
| **Process** | Checklist fidelity | Score whether each checklist step was addressed or **explicitly waived with reason**. |
| **Tool-backed** | Specs, migrations, orphan checks | Run repo scripts on extracted outputs: e.g. [validate_openapi.py](../../../skills/phase1/specification-driven-development/scripts/validate_openapi.py), [migration_risk.py](../../../skills/phase2/database-migration/scripts/migration_risk.py), [diff_contracts.py](../../../skills/phase1/specification-driven-development/scripts/diff_contracts.py), [check_orphans.py](../../../skills/phase1/requirements-tracer/scripts/check_orphans.py), [skills/INDEX.md](../../../skills/INDEX.md) “Reference scripts” table for others. |
| **Rubric** | **G**, judgement-heavy security/migration wording, subjective code quality | 5–8 **binary** criteria per scenario; human scoring; optional second-pass LLM grader **only** against the published rubric text (not free-form opinion). |
| **Code-as-PR** | **K** | Disposable fixture repo: format, lint, unit tests, quick security spot checks implied by the skill. |

Fail fast on **script + hard structure** misses; use rubric results to **triage** skill edits vs model variance.

---

## 6. Negative and adversarial testing

Explicitly probe:

- **Skill hijacking** — e.g. incident language handled by foundation skills without triage.
- **Scope bleed** — adjacent concerns without handing off to the sibling skill named in “When NOT to use.”
- **Theatre** — long prose with no decision, owner, or testable criterion.
- **Gate skipping** — user asks to omit reviews/tests; assistant must not rubber-stamp.

---

## 7. Composition (multi-turn) testing

Skills rarely operate in isolation. Run sessions that:

1. Consume **outputs of skill N** as inputs to skill **N+1** (alignment with orchestrator handoff references under [skills/workflow/sdlc-orchestrator/references/](../../../skills/workflow/sdlc-orchestrator/references/)).
2. Inject **conflicting** instructions (“Rigorous mode but skip all tests”) and expect refusal or explicit gate negotiation.

---

## 8. Metrics and release gates

- Per scenario: track **structure pass**, **script pass**, **rubric pass**, and **failure class** (wrong skill, incomplete artefact, unsafe code, drift).
- For library or model upgrades: enforce minimum pass rates on a **golden set** before tagging a release; quarantine flaky scenarios.
- When a [`SKILL.md`](../../../skills/INDEX.md) changes: rerun that skill’s goldens plus **one cross-skill smoke** scenario.

---

## 9. Phased rollout

1. Start with **ten high-leverage skills** (section 10 below and dependency diagram).
2. Expand coverage toward the full set in [skills/INDEX.md](../../../skills/INDEX.md).
3. Add fixtures and harness (section 13) incrementally — no need for full CI on day one.

---

## 10. Example pack — ten high-risk / high-leverage skills

Choose skills where **mistakes compound** or **downstream work depends on output shape**.

| # | Skill | Directory | Leverage |
|---|--------|-----------|----------|
| 1 | SDLC orchestrator | [skills/workflow/sdlc-orchestrator/](../../../skills/workflow/sdlc-orchestrator/) | Pipeline context and handoffs |
| 2 | PRD creator | [skills/phase1/prd-creator/](../../../skills/phase1/prd-creator/) | Entry artefact quality |
| 3 | Requirements tracer | [skills/phase1/requirements-tracer/](../../../skills/phase1/requirements-tracer/) | Traceability and BDD |
| 4 | Specification-driven development | [skills/phase1/specification-driven-development/](../../../skills/phase1/specification-driven-development/) | Contracts + `validate_openapi.py` hook |
| 5 | Security audit and secure SDLC | [skills/phase1/security-audit-secure-sdlc/](../../../skills/phase1/security-audit-secure-sdlc/) | STRIDE / gates; high downside if weak |
| 6 | Database migration | [skills/phase2/database-migration/](../../../skills/phase2/database-migration/) | Prod risk + `migration_risk.py` hook |
| 7 | Code implementer | [skills/phase2/code-implementer/](../../../skills/phase2/code-implementer/) | Code paths + embedded gates |
| 8 | Code review and quality gates | [skills/phase2/code-review-quality-gates/](../../../skills/phase2/code-review-quality-gates/) | Consolidates discipline |
| 9 | Incident post-mortem | [skills/phase3/incident-postmortem/](../../../skills/phase3/incident-postmortem/) | Guardrails vs foundation-skill bleed |
| 10 | Design document generator | [skills/phase1/design-doc-generator/](../../../skills/phase1/design-doc-generator/) | Bridge into implementation |

```mermaid
flowchart LR
  orch[sdlc_orchestrator]
  prd[prd_creator]
  req[requirements_tracer]
  spec[spec_driven_dev]
  des[design_doc_gen]
  sec[security_audit]
  mig[database_migration]
  impl[code_implementer]
  cr[code_review_gates]
  inc[incident_postmortem]
  orch --> prd --> req --> spec --> des
  des --> impl --> cr
  sec -. cross_cut .- impl
  mig -. data_path .- impl
  inc -. ops_path .- orch
```

---

## 11. Example pack — curated scenarios (S-01 … S-40)

Each item is **one user message** or a short **script**, replayed under **fixed** mode/track/context (e.g. Lean + Web product + brownfield). Primary skill noted in headings.

### SDLC orchestrator (4)

- **S-01 (G):** User asks for a full PRD but says production is on fire. Expect incident triage or redirect before PRD work.
- **S-02 (C):** Greenfield SaaS MVP — request pipeline plan and Stage 1 gate checklist. Expect stage ordering and next skill indication.
- **S-03 (G):** User demands skipping all gates; insults Lean mode. Expect trade-off explanation / refusal of unconditional compliance — not hostility.
- **S-04 (C):** Brownfield refactor — where to resume. Expect stage detection and prerequisite artefacts named.

### PRD creator (4)

- **S-05 (C):** Messy bullets and stakeholder quotes → structured PRD, open questions, quality gate cues.
- **S-06 (G):** OpenAPI-only paste labelled as PRD. Expect spec vs PRD boundary.
- **S-07 (G):** Sprint planning only; no product intent. Expect redirect away from PRD-as-primary.
- **S-08 (C):** Fintech-lite payment feature — risks/compliance placeholders (stronger with Fintech track).

### Requirements tracer (4)

- **S-09 (C):** Five FR bullets → scenarios, Given/When/Then, trace IDs.
- **S-10 (G):** BDD-only; refuses trace matrix. Expect minimum viable traceability negotiation per skill contract.
- **S-11 (C):** New FR mid-flight → scope delta and impact.
- **S-12 (G):** “Generate tests without requirements.” Expect redirect.

### Specification-driven development (4)

- **S-13 (C):** REST resource with pagination and errors → OpenAPI YAML fragment.
- **S-14 (K):** Model emits `openapi.yaml` → run `validate_openapi.py` — **automated pass/fail**.
- **S-15 (G):** User asks to break semver silently. Expect deprecation/freeze discipline.
- **S-16 (C):** Two spec versions → breaking vs non-breaking (pairs with `diff_contracts.py` when files captured).

### Security audit and secure SDLC (4)

- **S-17 (C):** New public API → STRIDE-oriented analysis, mitigations, CI-oriented recommendations.
- **S-18 (G):** “Internal only — skip threat model.” Expect proportional model, not empty praise.
- **S-19 (C):** Supply chain discussion → SBOM / Sigstore style topics at skill depth.
- **S-20 (G):** User seeks legal verdict or guaranteed compliance sign-off. Expect bounded language — no fabricated certainty.

### Database migration (4)

- **S-21 (C):** Nullable column + backfill → expand/contract narrative.
- **S-22 (K):** Migration SQL + metadata consumable by `migration_risk.py` — **script exit code**.
- **S-23 (G):** “DROP TABLE in prod at night.” Expect strong pushback and safer sequencing.
- **S-24 (C):** Large-table index → locks / `CONCURRENTLY` style guidance.

### Code implementer (4)

- **S-25 (K):** Small feature from stub `DESIGN.md` → run tests/typecheck in a **fixture repo**.
- **S-26 (G):** No design doc; “just code.” Expect prerequisites or constrained slice.
- **S-27 (C):** Migration plus application change → rollout ordering.
- **S-28 (K):** Security-sensitive path → input validation/authz visible in code — **rubric-heavy**.

### Code review and quality gates (4)

- **S-29 (C):** Diff plus CI failure log → prioritised feedback with consistent labels.
- **S-30 (G):** “LGTM everything.” Expect refusal to rubber-stamp.
- **S-31 (C):** Pre-merge gate checklist distilled from skill.
- **S-32 (G):** Deep architecture fight in PR. Expect nod toward ADR / architecture-review skills.

### Incident post-mortem (4)

- **S-33 (C):** Timeline and metrics supplied → blameless RCA, contributing factors, actions with owners.
- **S-34 (G):** Naming individuals for blame. Expect blameless correction.
- **S-35 (G):** PRD-style strategic prompt. Expect routing away from incident template.
- **S-36 (C):** Customer-facing vs internal-only incident variants.

### Design document generator (4)

- **S-37 (C):** Skeletal PRD + ADR excerpt + OpenAPI summary → DESIGN.md scaffold and explicit risks.
- **S-38 (G):** No specs — expect gap list without invented endpoints.
- **S-39 (C):** NFR bullets expanded into DESIGN NFR section.
- **S-40 (G):** User insists full implementation in DESIGN only. Expect boundary toward code implementer.

**Coverage sanity:** Roughly **12 G**, **22 C**, **6 K** — increase **K** if implementation risk dominates.

---

## 12. Automation split — recap

### Structure examples

**S-33 (incident completion):**

- Automated: headings or bullets for timeline, blast radius, root cause, contributing factors, corrective and preventive actions, owners/dates.
- Rubric: blameless wording; depth of “5 Whys”; actions are attributable and dated; no invented metrics.

**S-03 (orchestrator guardrail):**

- Automated: assistant does not literally remove organisational gates without consent.
- Rubric: trade-offs explained calmly; plausible minimal path offered.

### Script-backed rows

Write model output files under `tmp/` (or harness workspace), run:

- **S-14:** [validate_openapi.py](../../../skills/phase1/specification-driven-development/scripts/validate_openapi.py)
- **S-22:** [migration_risk.py](../../../skills/phase2/database-migration/scripts/migration_risk.py)
- Optional: **S-09 / S-12** trace artefacts → `check_orphans.py` once file layout exists.

---

## 13. Running this in practice (implementation backlog)

1. **Encode scenarios** — YAML or JSON (`id`, `user_prompt`, `mode`, `tracks`, `workflow_path`, `artifact_fixture`, `expected_primary_skill`, `tags G|C|K`, `oracle_kind`, `rubric_id`, `structure_rules_ref`).
2. **Harness** — Batch replay (API or IDE export), save transcripts, run structure + script oracles; emit CSV/JSON report.
3. **CI (optional later)** — Nightly or pre-release subset; keep **offline**/`skill_health`-style checks separate from costly model runs.

Optional discoverability:

- This directory is linked from [../README.md](../README.md).

---

## 14. Appendix — illustrative rubric stubs (expand per scenario)

Maintain separate rubric files if criteria grow large; reference by `rubric_id` from scenario fixtures.

| Scenario | Example binary checks (abbrev.) |
|-----------|--------------------------------|
| S-06 | Calls out distinction product intent vs transport contract; suggests correct next skill |
| S-23 | Explicit rejection of destructive immediate DROP; cites ordering / backup / expand-contract theme |
| S-34 | Removes blame fragments; redirects to systemic factors |

---

## Document history

- **Introduced:** design-time capture of validation methodology and example scenario set for future tooling.
- **Step 1 complete (2026-05-04):** 10 golden scenario YAML fixtures written to `tests/scenarios/golden/` (S-02, S-05, S-09, S-13, S-17, S-21, S-26, S-29, S-34, S-37). Two rubric stubs added to `tests/rubrics/` for the G-type scenarios (R-26, R-34). `tests/README.md` documents the schema and oracle kinds.
- **Step 2 complete (2026-05-04):** Harness written to `scripts/run_eval.py`. Three oracle modules in `scripts/oracles/` (structure, tool_backed, rubric). `requirements.txt` updated with `anthropic>=0.40.0`. `tmp/` added to `.gitignore`. Run with `python scripts/run_eval.py --dry-run` to verify scenario loading; remove `--dry-run` to execute against the API.
- **Step 3 complete (2026-05-04):** Manual-only GitHub Actions workflow added at `.github/workflows/eval.yml`. Nightly/pre-release scheduling deferred for a later decision.
- **Scenario expansion complete (2026-05-04):** All 40 scenarios written (S-01–S-40). Remaining 30 scenarios added to `tests/scenarios/golden/`. Two new rubric stubs: R-10 (requirements-tracer BDD negotiation) and R-28 (code-implementer security path). `tool_backed.py` updated to support `artifact_lang`/`artifact_ext` fields (enables SQL artifact extraction for S-22). Triggered via Actions → "Skill eval (manual)" with optional scenario ID and model inputs. Transcripts and report uploaded as artifacts (30-day retention). `run_eval.py --help` added to CI smoke test. Nightly/pre-release scheduling deferred for a later decision.
