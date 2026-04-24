---
name: code-review-quality-gates
description: >
  Activate when establishing code review processes, writing or improving PR review checklists,
  setting quality gate policies for CI/CD pipelines, reviewing code quality, setting merge
  criteria, defining linting and static analysis tool configurations, or coaching engineers
  on effective review practices. Use for everything from individual PR reviews to systemic
  quality improvement programmes, including identifying recurring defect patterns and
  measuring review effectiveness.
---

# Code review and quality gates

## Purpose

Code review is the primary mechanism for catching defects, knowledge transfer, and enforcing engineering standards before code reaches production. Every review is a shared accountability moment — the reviewer approving a PR shares responsibility for what merges.

---

## When to use

- A PR has been submitted and needs a code review before it can merge
- Setting up or improving the PR review process and comment labelling conventions for the team
- Defining the CI quality gates (linting, type checking, coverage thresholds, SAST) that block merges
- Analysing recurring defect patterns across multiple PRs to identify systemic quality issues
- Coaching an engineer on how to give effective, constructive code reviews
- A PR is large and needs guidance on whether to split it

## When NOT to use

- Orchestrating the actual merge, PR description generation from pipeline artefacts, and release tagging — use `pr-merge-orchestrator`.
- Writing the code being reviewed — use `code-implementer`.
- Defining the test strategy or coverage targets the review checks for — use `comprehensive-test-strategy`.
- Enforcing API contract conformance between services — use `api-contract-enforcer`.
- Reviewing AI-generated code specifically (elevated review checklist, IP policy) — use `ai-assisted-engineering`.
- Security threat modelling or the security gate sign-off itself — use `security-audit-secure-sdlc`.

---

## Code review principles

1. **Review the design, not just the implementation.** A well-implemented solution to the wrong problem is still wrong.
2. **Comment on the code, not the author.** "This query could be a performance problem under load" not "you wrote a slow query."
3. **Separate blocking issues from suggestions.** Mark comments as Blocking, Suggestion, or Question so the author knows what must change before merge.
4. **Approve what is correct and safe, not what is perfect.** Perfect is the enemy of shipped. Suggestions for non-blocking improvements go in as comments; they do not delay approval.
5. **The reviewer is also accountable.** A reviewer who approves a defect shares responsibility for it. Review with the same diligence you would apply to your own code.

---

## PR review checklist

### Correctness
- [ ] The code solves the problem described in the ticket or PR description
- [ ] Edge cases are handled (empty input, maximum input, null/nil, concurrent access)
- [ ] Error paths are handled and surfaced appropriately
- [ ] All tests pass; no tests are skipped without documented reason
- [ ] The change does not break backward compatibility unless explicitly intended

### Security (mandatory — see security-audit-secure-sdlc for full checklists)
- [ ] No secrets or credentials committed
- [ ] Input validation present at trust boundaries
- [ ] No SQL/NoSQL injection vectors
- [ ] Authentication and authorisation applied to new endpoints
- [ ] Error responses do not expose internal details

### Performance
- [ ] No N+1 query patterns introduced
- [ ] New database queries use indexes for the access pattern (check query plan if needed)
- [ ] No synchronous blocking operations in async code paths
- [ ] Resource lifecycle managed (connections, file handles, goroutines closed/cancelled)

### Maintainability
- [ ] Functions and types are named clearly; intent is evident from reading
- [ ] Complex logic has a brief comment explaining why (not just what)
- [ ] No dead code or commented-out code blocks
- [ ] New dependencies are necessary and reviewed (not a convenience import)
- [ ] Test coverage adequate for new business logic (at minimum happy path + primary error path)

### Operational readiness
- [ ] Structured log statements added for significant state changes
- [ ] Metrics emitted for new latency-sensitive or high-volume operations
- [ ] Configuration values are externalisable (not hardcoded)
- [ ] Database migrations are backward compatible with the current deployed version

---

## Comment severity labels

Every PR comment must be labelled so the author knows how to respond:

| Label | Meaning | Author action required |
|-------|---------|----------------------|
| `[Blocking]` | The PR must not merge until this is resolved | Fix before requesting re-review |
| `[Suggestion]` | Non-blocking improvement worth considering | Address or respond with rationale; either is fine |
| `[Question]` | Reviewer needs clarification to complete review | Respond; reviewer may reclassify after response |
| `[Nitpick]` | Style or minor preference; author's call | No response required |
| `[FYI]` | Sharing information, no action needed | No response required |

---

## Review SLAs

Unreviewed PRs stall delivery and create context-switching overhead for the author.

| PR size | First review response | Full review complete |
|---------|----------------------|---------------------|
| Small (< 200 lines) | Within 4 business hours | Within 1 business day |
| Medium (200–500 lines) | Within 1 business day | Within 2 business days |
| Large (500–1000 lines) | Within 1 business day | Within 3 business days |
| Very large (> 1000 lines) | Request split into smaller PRs | — |

A PR over 1000 lines of meaningful logic (excluding generated code and lock files) is a design smell. Split it. Reviewers are not obligated to provide a thorough review of an excessively large PR.

---

## Self-review eligibility

In Nano mode, self-review is acceptable **only** for changes that are pure internal logic with no security surface. Peer review is required — even in Nano mode — if the change touches any of the following:

| Change type | Review required |
|------------|----------------|
| Authentication or session handling | Peer review — not self-review |
| Authorisation logic or role/permission checks | Peer review — not self-review |
| Database schema (`ALTER TABLE`, `DROP`, index) | Peer review — not self-review (and auto-promotes to Lean) |
| Any interface or method other code calls directly | Peer review — not self-review |
| New external dependency | Peer review — not self-review |

In Lean and above, peer review is always required. A reviewer who approves a PR with one of these change types shares full accountability for that surface.

---

## Quality gates in CI

### Mandatory gates (all PRs)

| Gate | Tool | Applies in | Failure action |
|------|------|-----------|---------------|
| Tests pass | Language test runner | All modes | Block merge |
| Linting | Language-appropriate linter | All modes | Block merge |
| Type checking | mypy / tsc / go vet | All modes | Block merge |
| Secret scanning | gitleaks | All modes | Block merge — no exceptions |
| SAST | Semgrep | Lean and above; Nano if change touches auth/permissions | Block on Critical/High |
| SCA (dependency scan) | Trivy / Grype / Snyk | Lean and above; Nano if new library added | Block on Critical CVEs |
| Code coverage | Coverage tool | Lean and above | Block if coverage drops below threshold |

---

## Recurring defect pattern tracking

Track finding types across reviews to identify systemic quality issues:

```
## Quality defect trend: {Quarter}

| Category | Q1 count | Q2 count | Trend | Action |
|----------|----------|----------|-------|--------|
| Missing input validation | 12 | 18 | ↑ 50% | Secure coding training; SAST rule tightened |
| N+1 queries | 8 | 3 | ↓ 62% | Improvement — keep monitoring |
| Unhandled error paths | 15 | 14 | → Flat | Add linting rule for unhandled errors |
| Missing structured logging | 9 | 5 | ↓ 44% | Improvement — standardise log helper |
```

Review defect trends monthly. Systemic issues (same defect type appearing repeatedly) indicate a training gap, tooling gap, or standards gap — not individual engineer mistakes.

---

## Process

### Conducting a PR review

1. Read the PR description: understand what changed and why before reading any code. If the description is absent or unclear, ask for clarification before reviewing.
2. Check PR size. If it is over 1000 lines of meaningful logic, ask for it to be split rather than attempting a thorough review.
3. Work through the PR review checklist (Correctness → Security → Performance → Maintainability → Operational readiness). Use the checklist as a structured guide, not a box-ticking exercise.
4. Label every comment: `[Blocking]`, `[Suggestion]`, `[Question]`, `[Nitpick]`, or `[FYI]`. The label tells the author exactly what action is required.
5. For Blocking findings: be specific. "This query will N+1 on any non-trivial dataset — see line 47" is actionable. "Performance concerns" is not.
6. Verify that CI is green on the latest commit. If it is not, note that as a Blocking finding before proceeding with the rest of the review.
7. Produce the PR review summary in the output format.

### Setting up quality gates (CI)

1. Confirm which mandatory gates apply (tests, linting, type check, secret scan, SAST, coverage).
2. Add gate configuration to the CI pipeline. Ensure each gate blocks on failure — advisory-only gates are not gates.
3. Set coverage threshold to enforce the agreed floor; fail the build if it drops below.

### Tracking defect patterns

1. After each sprint or review cycle, tally findings by category.
2. Identify any category that is trending up. Systemic increases signal a training, tooling, or standards gap — address it at that level.

### All sub-tasks

3. Append the execution log entry.

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] code-review-quality-gates — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] code-review-quality-gates — PR review: device-registry authentication handler
[2026-04-20] code-review-quality-gates — Recurring defect analysis: 5 SQL injection vectors this sprint
```

---

## Output format

### PR review summary

```
## PR review: {PR title}

**Repository:** {repo}
**Branch:** {branch}
**Reviewer:** {name, role}
**Date:** {date}

**Summary:** {2-3 sentence overview of what the change does and any overarching concerns}

**Blocking findings:** {n}
**Suggestions:** {n}
**Questions:** {n}

**Recommendation:** Approve | Approve with conditions | Request changes

### Blocking findings
{list}

### Suggestions
{list}

### Positive observations
{optional — call out what was done well}
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for PR review templates, review SLA policy examples, and quality gate configuration guides as they are developed.
