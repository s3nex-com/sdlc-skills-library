# Engineering norms — template

Copy this file to `docs/engineering-norms.md` and fill in the bracketed sections. This doc is owned by the whole team. Changes go through a PR with one-reviewer approval. Review annually or whenever the team surfaces a recurring friction caused by an implicit norm.

Principle: **make implicit norms explicit.** Any question a new engineer asks twice in their first month is a norm that should be in this doc.

---

## Metadata

- **Team:** [team name]
- **Last reviewed:** [YYYY-MM-DD]
- **Next review:** [YYYY-MM-DD]
- **Owner:** whole team

---

## Pull requests

### Size
- **Max 400 lines** of production code per PR (excluding lock files, generated code, migrations).
- Split anything larger. If you can't split it, PR description must explain why in one paragraph.
- Rationale: reviews over 400 lines miss defects; cycle time balloons.

### Review
- **One non-author review** required before merge.
- Reviewer count may be higher for: security-sensitive changes, public API changes, migrations.
- Review turnaround: same business day for PRs < 200 lines; ≤ 24h for larger.
- Reviewers mark comments as **Blocking / Suggestion / Question** so authors know what needs to change.

### Merge
- **Squash on merge.** One logical change per merged commit.
- Branch naming: `<initials>/<short-kebab-desc>`, e.g. `ac/fix-auth-retry`.
- Branch lifetime: aim for < 3 days from branch to merge. Longer branches mean either the PR is too big or the work is blocked.

### PR description requirements
- **What changed** (one line).
- **Why** (link to PRD / issue / ADR if applicable).
- **How to verify** (test commands, staging URL, or screenshots).
- **Risk / rollback** for anything touching prod data, auth, or billing.

---

## Commit messages

Conventional commits format:

```
<type>(<scope>): <subject>

<body explaining why, not what>

<footer: breaking changes, issue refs>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `build`, `ci`.

Example:
```
fix(auth): handle expired JWT without 500

When the signing key rotated mid-request, the verifier threw instead of
returning 401. Callers then saw 500 and retried, amplifying load.

Fixes #4832
```

---

## Branching strategy

### [Pick one and delete the other]

**Option A — Trunk-based (recommended for small teams):**
- Everyone commits to short-lived branches off `main`.
- No long-lived feature branches.
- Use **feature flags** (see `feature-flag-lifecycle` skill) for anything not ready to be on in prod.
- `main` is always deployable.

**Option B — GitFlow:**
- `main` = production. `develop` = integration.
- Feature branches cut from `develop`, merge back to `develop`.
- Release branches for release stabilisation.
- Only use if regulatory or compliance demands strict release gates.

---

## Code style

- **Formatter is non-negotiable.** Pre-commit hook runs `[tool]` — no manual style debates in review.
- **Linter** runs in CI. Warnings above baseline block merge.
- Language-specific standards live in `[link to language style guide]`.
- If you disagree with a rule, open a PR to change the rule — don't work around it.

---

## Testing norms

- Every bug fix includes a test that would have caught the bug.
- Every new public function or endpoint has at least one test.
- Minimum coverage gate: `[N]%` overall, enforced in CI.
- See `comprehensive-test-strategy` skill for the full test pyramid policy.

---

## On-call

- Rotation: `[weekly | two-weekly]`, handover on `[day, time]`.
- Primary responds to alerts; secondary is backup.
- New engineers shadow one full shift before going on primary.
- Swap process: post in `#oncall-swaps`, swap confirmed in PagerDuty.
- **Escalation path:** Primary → Secondary → Engineering Lead → [CTO / Director].
- Response time SLA: `[N minutes]` for P1, `[N minutes]` for P2.

---

## Pairing cadence

- Target: at least `[2h/week]` of pairing per engineer.
- Pair on: anything unfamiliar, anything crossing a domain boundary, anything security-sensitive.
- Pairing is not a review replacement — a paired PR still needs one non-author review.

---

## Definition of done

A change is done when:
- [ ] Code merged to `main`.
- [ ] CI green.
- [ ] Deployed to production.
- [ ] Verified in production (metrics, logs, or manual smoke test).
- [ ] Tests added as applicable.
- [ ] Docs updated (README, runbook, or ADR as applicable).
- [ ] Feature flag state explicit (if behind a flag).
- [ ] Observability in place: new endpoints have metrics and logs.

---

## Secrets

- **No secrets in source code, ever.** Enforced by pre-commit hook (`gitleaks` or similar).
- Local dev secrets live in `.env.local` (gitignored) — see `references/local-dev-setup-patterns.md`.
- Production secrets live in the team's secrets manager — see `security-audit-secure-sdlc` references.

---

## Communication

- **Async-first.** Slack is primary; prefer threads over DMs for anything technical.
- Decisions made in DMs or calls are written up in the relevant channel, issue, or ADR the same day.
- Status updates at agreed cadence (`[weekly async update in #team]`). Do not run meetings for this.

---

## Changing these norms

- Open a PR to this doc.
- One-reviewer approval from anyone on the team.
- Merged change is effective immediately; announce in `#eng`.
- If the change is contentious, put it on the next retro agenda instead of the PR.
