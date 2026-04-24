---
name: pr-merge-orchestrator
description: >
  Activate when the user wants to create a pull request, run pre-merge verification,
  manage the code review and approval process, merge code, create a release tag, or
  orchestrate the full PR lifecycle from ready-to-review through to merged. This skill
  runs all mandatory pre-merge gates before creating the PR and coordinates the merge
  process using outputs from code-review-quality-gates, release-readiness, and
  security-audit-secure-sdlc. Also trigger for: "create a PR", "open a pull request",
  "ready to merge", "merge the code", "submit for review", "pre-merge checklist",
  "PR description", "merge process", "tag the release", "ship it", "push to review".
---

# PR and merge orchestrator

## Purpose

Merging code is not just a git operation — it is the act of committing the team to a specific implementation being correct, tested, and production-safe. This skill runs the complete pre-merge process, creates a PR with a complete and accurate description, coordinates approvals, and executes the merge. It prevents incomplete or untested code from entering the main branch.

This skill is the final gate before code enters the main branch. It coordinates three existing quality skills:
- `code-review-quality-gates` — code correctness and quality review
- `release-readiness` — pre-production readiness checklist
- `security-audit-secure-sdlc` — security gate sign-off

---

## When to use

- When implementation is complete and tests pass — the code is ready to merge
- When a PR exists but is missing description, is missing approvals, or has failing gates
- When managing a cross-company code acceptance process
- When a release needs tagging after merge
- When a PR has been approved but the merge process needs to be coordinated

## When NOT to use

- Before all tests pass — fix the tests first
- Before the acceptance criteria are verified — run `executable-acceptance-verification` first
- Before the security gate is signed off — run `security-audit-secure-sdlc` first

---

## Process

1. Run the pre-PR checklist (5 items). If any item fails: stop and fix it. Do not create the PR until all five pass.
2. Generate the PR description from pipeline artifacts (implementation notes, spec compliance, test results, rollback plan). Use the PR description template.
3. Assign the minimum required reviewers: at least one engineer who did not write the code. Add security perspective for security-touching PRs; add architecture perspective for changes that deviate from the design doc.
4. Address all Blocking and Question comments before requesting final approval. Reply on every resolved comment.
5. Before merging: confirm CI is green on the latest commit, branch is up to date with the target, and all required approvals are present and not invalidated by subsequent commits.
6. Merge using the correct strategy: squash merge for feature work (clean linear history), merge commit for hotfixes (preserve fix history).
7. Write a meaningful merge commit message: what, why, which stories, which ADRs.
8. Post-merge: verify CI passes on main. Tag the release if this completes a milestone. Update `docs/implementation-status.md`.
9. Trigger `documentation-system-design` to update runbooks, API guides, or architecture docs for any new operational surfaces.
10. Append the execution log entry.

## Pre-PR checklist — 5 items

A PR may not be created until all five pass.

- [ ] **All tests pass** — unit, integration, and acceptance; zero failures; no tests skipped without documented reason
- [ ] **Security clean** — SAST clean (no Critical/High), dependency scan clean (no Critical CVEs), secret scan clean
- [ ] **Spec compliant** — all new endpoints match their spec exactly; no unintended breaking changes (`diff_contracts.py`)
- [ ] **No debug artifacts** — no hardcoded credentials, no commented-out code, no TODO blocks that should be resolved before merge
- [ ] **PR description written** — see template below; the description is the permanent record

That is the full checklist. The individual gates (SAST, tests, linting, type checking) run automatically in CI — they do not need manual verification beyond "CI is green."

---

## PR description — auto-generate from pipeline artifacts

A PR description is not a one-liner. It is the permanent record of what changed, why, and how to verify it. Generate it from the pipeline artifacts already produced.

### PR description template

```markdown
## Summary

[2-3 sentences: what this implements and why. Reference PRD and any ADRs if they exist.]

**Stories covered:** ST-NNN, ...
**Phase:** N of M _(omit for single-phase work)_

---

## What changed

| Component | Change | Notes |
|-----------|--------|-------|
| [name] | New / Modified / Removed | [one line] |

**API:** [New endpoints or breaking changes — or "none"]
**DB:** [Migration name + "additive only / destructive"] — or "none"
**Config:** [New env vars required] — or "none"

---

## How to verify

- Tests: `[command]` — all pass
- Manual: [1–2 specific steps if UI or integration behaviour needs eyeballing — omit if tests are sufficient]

---

## Rollback

[What to do if production breaks after merge — 1–3 steps. If additive-only and fully revertable by reverting the merge commit, say so.]

---

## Checklist
- [ ] Self-reviewed
- [ ] Tests verify behaviour, not implementation details
- [ ] No debug artifacts (hardcoded creds, commented-out code, unresolved TODOs)
- [ ] Docs updated if runbooks, API guide, or architecture diagrams changed
```

---

## Review coordination

### Assigning reviewers

Minimum: one engineer who did not write the code. They should be familiar enough with the system to understand the change.

Additional reviewers when needed:
- Security-touching PR (new auth, new data handling, SAST flagged): add security perspective (can be same engineer wearing a different hat)
- Change deviates from design doc or introduces a new architectural pattern: add architecture perspective before merging

### Review SLA

From `code-review-quality-gates`:
- Small PR (< 200 lines): first response within 4 business hours
- Medium PR (200–500 lines): first response within 1 business day
- Large PR (500–1000 lines): first response within 1 business day
- A PR over 1000 lines must be split before submission

### Resolving review comments

For each `[Blocking]` comment:
1. Fix the issue or raise a documented counter-argument
2. Reply on the comment with what was done
3. Re-request review from the specific reviewer (not the whole team)

For each `[Question]` comment:
1. Answer the question in the comment thread
2. If the answer reveals a design issue, raise it explicitly before merging

A PR with unresolved `[Blocking]` or `[Question]` comments must not merge.

---

## Approval requirements

| Scenario | Required before merge |
|----------|-----------------------|
| Standard PR | 1 approval from an engineer who didn't write the code |
| Security-touching PR | 1 approval with security perspective sign-off |
| Database migration | 1 approval from someone who has reviewed the migration script and rollback |

On a small team, one thoughtful approval is better than two rubber stamps.

---

## Merge process

### Pre-merge final check

Before clicking merge:

1. Confirm CI is green on the latest commit (not a previous commit)
2. Confirm branch is up to date with the target branch (rebase or merge main in if behind)
3. Confirm all required approvals are present and no approvals have been invalidated by subsequent commits
4. Confirm no new commits have been pushed since the last approval (if so, re-request review)

### Merge strategy

| Scenario | Strategy | Rationale |
|----------|----------|-----------|
| Feature work | Squash merge | Clean linear history; each feature = one commit |
| Hotfix | Merge commit | Preserve the fix history for post-incident review |
| Release branch → main | Merge commit | Preserve release history |

Always write a meaningful merge commit message if squashing. The commit message is the permanent record — "Merge PR #42" is not acceptable.

**Good merge commit message:**
```
feat(devices): implement device registration API (Phase 1)

Implements POST /v1/devices, GET /v1/devices/{id} per spec device-api.yaml v1.2.
Covers stories ST-001, ST-002, ST-003 from the Device Management PRD.
All acceptance criteria pass. Migration 0003_add_devices_table is backward compatible.

ADRs: ADR-007 (JWT auth), ADR-012 (audit log pattern)
```

### Post-merge steps

1. Verify CI passes on the main branch after merge
2. Tag the release if this completes a delivery milestone (see below)
3. Update `docs/implementation-status.md` — mark phase as merged
4. Notify relevant stakeholders if this was a client-facing delivery
5. Trigger `documentation-system-design` — update runbooks, API guides, or architecture docs

---

## Release tagging

Tag every milestone merge:

```bash
git tag -a v[major].[minor].[patch] -m "Release v[version]: [phase/milestone name]

Stories: [ST-NNN list]
PRD: [link]
Design doc: [link]
"
git push origin v[major].[minor].[patch]
```

Use semantic versioning:
- **Major:** Breaking change to API contract or data model
- **Minor:** New functionality, backward compatible
- **Patch:** Bug fix or non-functional change

---

## Output format

### Pre-merge gate report

```markdown
## Pre-merge gate report: [PR title]

**Date:** [date]
**Branch:** [branch name] → [target branch]
**Reviewer:** [name]

### Gate summary
| Gate | Status | Notes |
|------|--------|-------|
| Implementation complete | PASS / FAIL | |
| Unit tests | PASS / FAIL | [N] tests |
| Integration tests | PASS / FAIL | [N] tests |
| Acceptance tests | PASS / FAIL | [N] scenarios |
| Coverage | PASS / FAIL | [N]% vs [threshold]% |
| Security (SAST) | PASS / FAIL | [N] findings |
| Dependency scan | PASS / FAIL | [N] CVEs |
| Secret scanning | PASS / FAIL | |
| Linting | PASS / FAIL | |
| Spec compliance | PASS / FAIL | |

### Result
READY TO MERGE | BLOCKED — [list of failing gates]
```

---

## Handoff after merge

1. Pass to `documentation-system-design` — update all operational documentation
2. Pass to `release-readiness` — if this triggers a production deployment
3. Pass to `observability-sre-practice` — verify monitoring and alerting are in place for new components

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] pr-merge-orchestrator — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] pr-merge-orchestrator — PR #142 merged: device telemetry ingestion feature
[2026-04-20] pr-merge-orchestrator — Release v1.2.0 tagged after merge
```

---

## Reference files

- `references/pr-description-template.md` — Blank PR description template
- `references/pre-merge-checklist.md` — Printable pre-merge verification checklist
- `references/merge-runbook.md` — Step-by-step merge process for complex releases
