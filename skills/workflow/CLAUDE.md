# skills/workflow/ — the SDLC orchestrator

One skill lives here: `sdlc-orchestrator`. It is the single entry point for all non-trivial feature work. It does not replace other skills — it runs them in the right order, verifies stage gates, and tracks state in `docs/sdlc-status.md`.

---

## The 5-stage pipeline

```
Stage 1 — Define    → PRD approved, goals and NFRs clear
Stage 2 — Design    → requirements traced, specs frozen, DESIGN.md complete
Stage 3 — Build     → implementation complete, tests passing, security gate signed off
Stage 4 — Verify    → acceptance criteria verified, performance validated, docs complete
Stage 5 — Ship      → release gate passed, merged, tagged, deployed
```

Skills invoked per stage:
- **Stage 1:** `prd-creator`
- **Stage 2:** `requirements-tracer`, `specification-driven-development`, `design-doc-generator`, `architecture-review-governance`, `security-audit-secure-sdlc`
- **Stage 3:** `code-implementer`, `comprehensive-test-strategy`, `security-audit-secure-sdlc`
- **Stage 4:** `executable-acceptance-verification`, `performance-reliability-engineering`, `code-review-quality-gates`, `documentation-system-design`
- **Stage 5:** `release-readiness`, `pr-merge-orchestrator`

---

## Workflow paths

Workflow paths modify *which stages run*. They are orthogonal to both mode and domain track — a session can be in `Lean mode + Fintech track + Hotfix path` simultaneously.

(Earlier docs called these "special tracks". They were renamed "workflow paths" to free up "track" for domain specialization — see `docs/tracks.md`.)

**Spike path** — for exploratory work that produces a decision, not a deployment:
- Timebox: 2–4 hours, max 1 day (hard cap — extend it and it becomes a feature)
- Output: a decision document or ADR, not deployable code
- Skip stages 3–5; the spike exits into stage 1 with a clearer PRD

**Hotfix path** — for production incidents requiring immediate code changes:
- Bypasses stages 1–2 (no PRD, no full design)
- Starts at stage 3 with a tight scope definition
- Still requires stage 4 verification and stage 5 merge gate
- Trigger: tell the orchestrator "this is a hotfix"

**Brownfield path** — for taking over an existing codebase:
- Runs a lightweight assessment (debt, DORA baseline, security scan, architecture map) before any feature work
- After the assessment, pick a mode (and any domain tracks) for ongoing work
- Full process in the SDLC orchestrator SKILL.md

---

## Domain tracks (separate concept — not in this directory)

Domain tracks live at `skills/tracks/` and are orthogonal to workflow paths. Where workflow paths change *which stages run*, a domain track changes *how a stage runs inside a given domain*: elevate mandatory skills, tighten gate criteria, inject domain reference material.

The 10 tracks: Fintech, SaaS B2B, Web product, Data platform / ML ops, Healthcare, Regulated / government, Real-time / streaming, Consumer, Open source, Mobile. Full guide: `docs/tracks.md`.

---

## Invariants — do not break these when editing

**The 5-stage structure is fixed.** Do not collapse it to 4 stages ("merge Design into Define"), do not expand it to 6. The boundaries exist because they map to real handoffs between roles and real quality gates.

**Stage gates are non-negotiable.** Each gate exists because skipping it creates a specific downstream failure. The gate descriptions must include what breaks if the gate is skipped — do not remove this reasoning.

**Lean rules must stay.** The orchestrator explicitly says "Stage 1 does not need 11 sections" and "a 3-person team does not need a steering committee review". These lean rules are core to the philosophy. Adding ceremony back is the #1 mistake when editing.

**Spike timebox is enforced.** The 2–4 hour / 1-day max is not a suggestion. A spike that runs longer is a mini-project and needs a real PRD. Do not soften this constraint.

**Audit trail files must always be updated.** Every stage transition must update `docs/sdlc-status.md`. Every skill execution must append to `docs/skill-log.md`. These are the pipeline's observable state — without them, you cannot resume a paused pipeline or verify what was done.

**Tracks compose with modes, not replace them.** A track never disables a mode's gate. A track can only elevate Advisory → Mandatory and tighten criteria. Do not let a track "replace" mode discipline — strictest-wins is the composition rule.

**Workflow paths are not domain tracks.** If you are tempted to move Hotfix/Spike/Brownfield into `skills/tracks/`, stop. They are fundamentally different: paths modify which stages run; tracks modify how stages run for a domain.

---

## Common mistakes when editing the orchestrator

- **Adding ceremony back.** The orchestrator was deliberately simplified. If you find yourself adding sign-off meetings, formal review boards, or multi-step approval processes, stop. These belong to `stakeholder-sync` at most, and only if the team actually needs them.
- **Making gates optional.** "Gate recommended but can be skipped if..." is not a gate. Either a stage exit criterion exists or it doesn't.
- **Removing lean rules.** The explicit callouts about proportionality ("you don't need X for a team of 3") are signal, not noise. Keep them.
- **Conflating the spike with stage 1.** A spike is time-limited exploration. Stage 1 is committed planning. They produce different outputs and must stay distinct.

---

## Reference files

- `references/workflow-usage-guide.md` — how to use the orchestrator in practice
- `references/sdlc-status-dashboard.md` — format for `docs/sdlc-status.md`
- `references/stage-handoff-templates.md` — output templates for each stage transition
- `references/troubleshooting.md` — what to do when the pipeline stalls
