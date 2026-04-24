---
name: architecture-fitness
description: >
  Activate when setting up or running architecture fitness functions, enforcing import
  boundaries in CI, checking module layer boundaries automatically, tracking dependency
  budget against an approved list, detecting circular imports, flagging dead or abandoned
  modules, preventing architecture drift between PRs, enforcing architecture compliance
  in the build pipeline, or adding architecture CI checks to a project. Distinct from
  periodic human architecture reviews — fitness functions run automatically on every PR
  with no human required.
---

# Architecture fitness functions

## Purpose

Architecture fitness functions are automated rules that run on every PR and fail the build
when the codebase drifts from its intended structure. They are not reviews — no human is
involved. A violation is a build failure. This is the complement to `architecture-review-governance`
(phase 1), which handles periodic human-led review. Fitness functions handle continuous,
automated enforcement: import boundaries, dependency budgets, circular import detection,
and dead module flagging. Once configured, they run silently in the background until
something breaks a rule, at which point the PR is blocked until the violation is resolved
or formally excepted.

---

## When to use

- Setting up a new project and you want structural rules enforced from day one
- Architecture drift is appearing across PRs (layer violations, dependency creep)
- You want to enforce a previously decided architecture (from an ADR or design doc) in CI
- A team member bypassed a rule and you need to make it impossible to bypass again
- You are completing a design phase and want the structural decisions backed by automated gates

---

## When NOT to use

- **Periodic architecture reviews** — use `architecture-review-governance` (phase 1). That skill
  handles scheduled human review of the overall structure. This skill handles continuous CI enforcement.
- **Recording a new architecture decision** — use `architecture-decision-records`. Fitness functions
  enforce decisions already recorded, they do not make them.
- **Code quality review of a specific PR** — use `code-review-quality-gates`. That skill covers
  reviewer checklists, comment labels, and PR quality standards. Fitness functions are pre-review
  automated gates.
- **Dependency version security auditing** — use `dependency-health-management` (phase 3). That
  skill tracks CVEs and outdated packages. This skill tracks the count and approved list of
  third-party deps, not their security status.

---

## Process

### Step 1: Define your fitness function set

Not all rules apply to all projects. Enable what applies; document choices in `.fitness.yml`.

| Rule | Category | What it enforces |
|------|----------|-----------------|
| `no_circular_imports` | imports | Fail on any circular import in the codebase |
| `enforce_layer_boundaries` | imports | API may not import DB directly; services may not cross-import internals |
| `dependency_budget` | imports | Max N third-party packages (suggested: 30) |
| `no_unauthorized_deps` | imports | New third-party dep requires entry in `approved-deps.txt` |
| `coverage_floor` | quality | Minimum test coverage % per module (suggested: 70%) |
| `no_dead_modules` | quality | Zero coverage AND no git change in N days → flagged |
| `api_docs_required` | docs | Every public endpoint needs an OpenAPI entry or docstring |
| `adr_for_new_services` | docs | New top-level package/service requires an ADR |

Start with `no_circular_imports`, `enforce_layer_boundaries`, and `coverage_floor`. Add the
rest once the baseline is green.

---

### Step 2: Configure rules in `.fitness.yml`

Place `.fitness.yml` at the repo root. This file is the single source of truth for which
rules are active and what their thresholds are.

```yaml
import_rules:
  no_circular_imports: true
  layer_boundaries:
    api: [services]          # api may import from services
    services: [db, models]   # services may import from db and models
    db: [models]             # db may import from models
    # nothing may import from api
  dependency_budget: 30

quality:
  coverage_floor: 70
  dead_module_days: 90

docs:
  api_docs_required: true
  adr_for_new_services: true
```

The `layer_boundaries` map defines what each layer is **allowed** to import from. Any import
not in the allowed list is a violation. Define layers by top-level directory name.

---

### Step 3: Add CI integration

Three scripts run on every PR. Add them as a named step in your CI pipeline:

```yaml
# GitHub Actions — add to your PR workflow
- name: Architecture fitness check
  run: |
    python skills/phase2/architecture-fitness/scripts/check_imports.py
    python skills/phase2/architecture-fitness/scripts/dep_budget.py
    python skills/phase2/architecture-fitness/scripts/dead_code.py
```

All three must pass (exit 0) for the step to pass. `dead_code.py` always exits 0 — it
produces WARNs but never blocks. `check_imports.py` and `dep_budget.py` exit 1 on violations.
Each script accepts `--help` and can be run locally before pushing.

---

### Step 4: Handle violations

When a script exits 1, CI fails with the specific rule and location:

```
VIOLATION: layer_boundary — api/routes.py imports db/session.py directly (api → db not allowed)
VIOLATION: dependency_budget — 34 deps found (budget: 30)
```

The engineer must do one of two things:

1. **Fix the violation** — restructure the import, remove the excess dependency
2. **Open a formal exception** — add an entry to `.fitness-exceptions.yml` with owner and expiry

```yaml
# .fitness-exceptions.yml
exceptions:
  - rule: layer_boundary
    location: api/internal/bootstrap.py
    reason: "Bootstrap file must access db directly for connection pooling setup"
    owner: eng-lead
    expires: 2026-07-01
```

No open-ended exceptions. Every exception has an expiry date. The CI script reads
`.fitness-exceptions.yml` and skips flagged locations — but expired exceptions are treated
as active violations.

---

### Step 5: Tune quarterly

- Review which rules produce false positives — tighten or loosen thresholds
- Add project-specific rules as the architecture evolves (e.g. a new layer, a new boundary)
- Remove rules that no longer apply (decommissioned layers, merged services)
- Review expired exceptions in `.fitness-exceptions.yml` and either fix the underlying issue
  or renew with a new expiry date and updated rationale

Assign one engineer to own the quarterly tune — it takes 30 minutes if exceptions have not
accumulated.

---

## Output format

When all scripts run in CI, the combined output looks like this:

```
Architecture fitness check — 2026-04-20

PASS  no_circular_imports          0 cycles found
PASS  layer_boundaries             all boundaries respected
FAIL  dependency_budget            34 deps found (budget: 30)
        New since last check: boto3, redis, celery, pyjwt
        Action: add to approved-deps.txt or remove unused dep
PASS  coverage_floor               min coverage: 73% (floor: 70%)
WARN  dead_modules                 2 modules flagged (zero coverage + 95 days inactive)
        app/legacy/import_handler.py
        app/utils/xml_parser.py
PASS  api_docs_required            all 12 endpoints documented

Result: 1 FAIL — PR blocked until resolved
```

Run scripts locally before pushing to see violations early:

```
$ python check_imports.py
[check_imports] Scanning 142 Python files...
PASS  no_circular_imports   0 cycles detected
FAIL  layer_boundaries      2 violations
  VIOLATION: api/routes.py:14 imports db/session.py (api → db not allowed)
Exit: 1
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] architecture-fitness | outcome: OK|BLOCKED|PARTIAL | next: ... | note: ...
```

Example entries:
```
[2026-04-20] architecture-fitness | outcome: OK | next: monitor quarterly | note: initial setup, 3 rules enabled
[2026-04-20] architecture-fitness | outcome: BLOCKED | next: fix layer violations in api/ | note: 2 violations, api importing db directly
[2026-04-20] architecture-fitness | outcome: PARTIAL | next: tune dep budget threshold | note: dep_budget failing, exception filed for boto3
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the
`sdlc-orchestrator` skill.

---

## Reference files

The `references/` directory (load on demand) contains:

- `references/fitness-yml-examples.md` — annotated `.fitness.yml` examples for common architectures
  (layered monolith, microservices, hexagonal)
- `references/exception-patterns.md` — when exceptions are legitimate vs. when they indicate
  the rule is wrong; how to write a good exception entry
- `references/layer-boundary-guide.md` — common layer structures and how to express them in
  `.fitness.yml`; worked examples of violations and their fixes
