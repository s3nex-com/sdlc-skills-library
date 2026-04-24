# Pre-merge checklist

Run every item before creating the PR. This checklist is the gate between "implementation complete" and "ready for review". A PR that fails this checklist should not be submitted.

Print or copy this into `docs/pre-merge-[feature]-[date].md` and check items off as you go.

---

## 1. Implementation completeness

- [ ] All tasks in the target phase are marked "Complete" in `docs/implementation-status.md`
- [ ] No tasks are in "In progress" or "Blocked" state
- [ ] All deviations from `DESIGN.md` have approved ADRs (see deviations log in implementation status)
- [ ] No implementation for Phase N+1 has been included in this PR
- [ ] `docs/implementation-status.md` phase gate section is filled in

---

## 2. Test gate

### Unit tests
- [ ] All unit tests pass: `[command]` — [N] tests, 0 failures, 0 skipped without reason
- [ ] Tests cover: happy path, primary error paths, edge cases (empty input, max bounds, null/nil)
- [ ] No test asserts implementation details — tests assert behaviour and outcomes

### Integration tests
- [ ] All integration tests pass: `[command]` — [N] tests, 0 failures
- [ ] Integration tests use real dependencies (real DB, real queue) — no in-process mocks

### Contract tests
- [ ] All contract tests pass (if new API endpoints): `[command]`
- [ ] `validate_openapi.py` passes for all modified specs
- [ ] `diff_contracts.py` shows no unintended breaking changes

### Acceptance tests
- [ ] All BDD acceptance scenarios pass: `[command]` — [N] scenarios, 0 failures, 0 skipped
- [ ] Every story in this PR's scope (ST-NNN list) has at least one passing acceptance scenario

### Coverage
- [ ] Coverage meets or exceeds threshold: [N]% actual vs [N]% threshold
- [ ] Coverage has not dropped from the previous baseline on `main`

### Performance tests (if NFR-affecting code)
- [ ] Load test passes against NFR thresholds (if performance-critical code is included)

---

## 3. Security gate

### Gates 1 and 2 (design and implementation time)
- [ ] STRIDE threat analysis referenced (ADR or threat model doc — from Stage 4)
- [ ] Secure coding checklist applied during implementation (verify in `implementation-status.md`)

### Gate 3: Static analysis (SAST)
- [ ] SAST scan run on this branch (tool: [gitleaks / Semgrep / Snyk Code / etc.])
- [ ] No Critical findings
- [ ] No High findings (or all High findings have a documented accepted risk with owner and remediation date)

### Gate 4: Dependency scan
- [ ] Dependency vulnerability scan run (tool: [Snyk / Dependabot / OWASP DC / etc.])
- [ ] No Critical CVEs introduced by new or updated dependencies
- [ ] No High CVEs without a documented accepted risk

### Secret scanning
- [ ] Secret scanning clean: no API keys, tokens, passwords, or private keys in the diff
- [ ] No hardcoded connection strings or credentials

---

## 4. Code quality gate

- [ ] Linting passes with zero errors: `[linting command]`
- [ ] Type checking passes: `[type check command]`
- [ ] No dead code: no commented-out blocks, no unreachable paths, no unused imports
- [ ] No debug statements left in production code paths
- [ ] All new configuration values are documented (in PR description and in code comments if non-obvious)

---

## 5. Spec compliance gate

- [ ] All new endpoints match the spec exactly (path, method, request schema, response schema, status codes)
- [ ] `validate_openapi.py` passes in CI for all modified spec files
- [ ] `diff_contracts.py` reviewed: all breaking changes are intentional and communicated to consumers

---

## 6. Operational readiness gate

- [ ] Structured log statements added for all significant state changes in new code
- [ ] Metrics emitted for new latency-sensitive or high-volume operations
- [ ] All new configuration values have sensible defaults (or are documented as required)
- [ ] Database migrations are backward compatible with the current deployed version
- [ ] Runbooks updated (or confirmed no update needed) — flag for Stage 9 if update is required

---

## 7. Branch state gate

- [ ] Branch is up to date with `main` (rebased or merged within 24 hours)
- [ ] No merge conflicts
- [ ] CI is green on the latest commit on this branch (check: not a cached result from a previous commit)
- [ ] All commits on this branch have meaningful commit messages (not "fix", "wip", "asdf")

---

## 8. Final self-review

Before submitting the PR, do one complete read of the diff:

- [ ] Read every changed file end-to-end as if you are the reviewer, not the author
- [ ] Every change is intentional — no accidentally included changes
- [ ] PR scope matches what was planned — no extra changes that belong in a different PR
- [ ] PR description accurately describes what the diff does

---

## Pre-merge gate report

Fill this in and attach it to the PR description or `docs/pre-merge-[feature]-[date].md`.

```
## Pre-merge gate report

**PR:** [PR title]
**Branch:** [branch] → main
**Date:** [YYYY-MM-DD]
**Reviewer:** [Name]

| Gate | Status | Notes |
|------|--------|-------|
| Implementation complete | PASS / FAIL | |
| Unit tests | PASS / FAIL | [N] tests |
| Integration tests | PASS / FAIL | [N] tests |
| Contract tests | PASS / FAIL / N/A | |
| Acceptance tests | PASS / FAIL | [N] scenarios |
| Coverage | PASS / FAIL | [N]% |
| SAST | PASS / FAIL | [N findings, disposition] |
| Dependency scan | PASS / FAIL | [N CVEs, disposition] |
| Secret scanning | PASS | |
| Linting | PASS / FAIL | |
| Spec compliance | PASS / FAIL / N/A | |
| Branch up to date | PASS | |

**Result:** READY TO MERGE / BLOCKED

**Blocking items:**
- [Item — what fails and what is needed to fix it]
```
