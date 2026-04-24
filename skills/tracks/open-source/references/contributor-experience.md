# Contributor experience

External contributors are users with extra steps. If their first PR takes three weeks to get a reply, you will not get a second PR. This reference defines the contributor-facing surface — `CONTRIBUTING.md`, PR templates, issue labels, SLAs — and the maintainer-side discipline needed to sustain it.

---

## `CONTRIBUTING.md` structure

Place at repo root. GitHub surfaces it on new issue and new PR flows. Keep it scannable — contributors bounce off walls of text.

```markdown
# Contributing

Thanks for considering a contribution. This guide covers the essentials.

## Ways to contribute

- Report a bug — open an issue using the bug template.
- Suggest a feature — open a discussion first, then an issue if there's interest.
- Fix a bug or implement a feature — see "Sending a pull request" below.
- Improve docs — PRs against `docs/` are welcome with no prior discussion.
- Triage issues — `good-first-issue` and `help-wanted` labels are always open.

## Project setup

```bash
git clone https://github.com/ORG/REPO.git
cd REPO
<setup command>
<test command>
```

The full test suite should complete in under 5 minutes on a developer laptop.
If it doesn't, open an issue — that's a bug.

## Sending a pull request

1. Open an issue first for anything larger than a typo or a one-line fix.
   This saves both of us the cost of a rejected PR.
2. Fork and create a branch from `main`.
3. Follow the existing code style. Run `<format command>` before committing.
4. Add or update tests. Untested PRs are closed with a request for tests.
5. Update the CHANGELOG under the `## [Unreleased]` section.
6. Sign off your commits: `git commit -s`. See DCO section below.
7. Open the PR. Fill out the PR template.

## Commit sign-off (DCO)

All commits must be signed off under the Developer Certificate of Origin.
Add `-s` to your git commit: `git commit -s -m "..."`. This appends a
`Signed-off-by` trailer certifying you wrote the code and have the right
to submit it under the project's license. The DCO text is at
https://developercertificate.org.

## Review

A maintainer will respond within 10 business days. If you haven't heard
back after that, leave a comment on the PR — we may have missed the
notification. Reviews are a conversation, not a gate; expect back-and-forth.

## Code of conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
Report unacceptable behaviour to conduct@example.com.
```

Keep this file under 100 lines. Longer rules live in `docs/development.md`, linked once from here.

---

## CLA versus DCO — pick one, document it

| | CLA | DCO |
|-|-|-|
| What it is | Signed agreement transferring or licensing rights | Per-commit attestation the contributor wrote it |
| Friction | Higher — signing flow before first merge | Very low — `git commit -s` adds a trailer |
| Enforcement | CLA bot checks a signed-agreements database | `probot/dco` or GitHub Action verifies `Signed-off-by:` |
| Recommended for | Foundation projects, dual-license commercial, corporate sign-off needs | Everything else |

**Default: DCO.** Lower friction, acceptable legal cover for most projects. Only pick CLA for a specific legal reason (dual licensing with commercial arm, foundation requirement, corporate policy). Document the choice in `CONTRIBUTING.md` and enforce it in CI — inconsistent enforcement is worse than none.

---

## Issue labels — standard set

Start with these. Add more as the project grows. Prune labels that collect zero issues after six months.

| Label | Meaning |
|-------|---------|
| `bug` / `feature` / `docs` / `question` | Category |
| `good-first-issue` | Small, well-scoped, no deep context needed. Curated, not "whatever is tiny". |
| `help-wanted` | Larger than `good-first-issue`; PRs welcome |
| `needs-repro` | Bug report missing a reproducible case |
| `needs-triage` | Default for new issues |
| `blocked` | Waiting on something external |
| `wontfix` / `duplicate` | Declined or closed with a link |
| `breaking-change` | Will require a major version bump |
| `security` | Attached to public fix PRs after disclosure |
| `priority:high` / `priority:med` / `priority:low` | Applied during triage |

A `good-first-issue` must have: clear description, expected outcome, pointer to the relevant file(s), and no requirement to reverse-engineer internals.

---

## PR template

Place at `.github/pull_request_template.md`. Keep it short — long templates get ignored.

```markdown
## What this PR does

<!-- One or two sentences. -->

## Why this change

<!-- Link the issue number if one exists: closes #123 -->

## How to verify

<!-- Commands or steps a reviewer can run to confirm this works. -->

## Checklist

- [ ] Tests added or updated
- [ ] CHANGELOG updated under `## [Unreleased]`
- [ ] Commits signed off (`git commit -s`)
- [ ] Breaking change? If yes, explain the migration path.
```

---

## Issue templates

Provide a bug template and a feature template at `.github/ISSUE_TEMPLATE/`. The bug template must ask for: library version, runtime version, OS, minimal reproduction, expected vs actual behaviour. Turn off the blank-issue option to force template use.

---

## Code of conduct

Adopt [Contributor Covenant v2.1](https://www.contributor-covenant.org/) verbatim. Do not write a bespoke one — it creates legal ambiguity without benefit. Designate a named contact address (`conduct@` or a named maintainer); unassigned enforcement is theatre. Document the escalation path in the file.

---

## Triage and review SLAs

Publish the SLAs so contributors know what to expect. Missed SLAs require a note ("sorry, we're backed up, expect a reply by X"), not silence.

| Event | Default SLA |
|-------|-------------|
| New issue — first response | 5 business days |
| New PR — first review | 10 business days |
| Follow-up review after contributor addresses feedback | 5 business days |
| Security report acknowledgement | 3 business days (see SECURITY.md) |
| `good-first-issue` review | 5 business days (prioritise first-time contributors — they will not return if ignored) |
| Stale PR — proactive check-in | 30 days |

For a 3–5 person team, these SLAs survive normal week-to-week variance. They fail under incident load or team turnover — in those cases, post a banner on the repo README acknowledging the backlog instead of letting silence accumulate.

---

## First-time contributor support

Most first-time contributors bounce at one of three friction points:

1. **Can't get the project running locally.** One-command setup, tested monthly.
2. **PR ignored for weeks.** Enforce the first-review SLA even for PRs you plan to decline — a quick decline beats silence.
3. **CI fails in a way that is not their fault.** Flaky-test hygiene matters; a third forced rebase to retry CI is when they give up.

A first-time contributor's first PR should merge within two weeks. First-time contributor merge time is the headline health metric for the contributor pipeline.

---

## Maintainer burnout prevention

A 3–5 person team maintaining a project at non-trivial adoption will burn out within 18 months without explicit counter-measures:

- **Rotate on-call.** One person per week owns the triage queue. Everyone else ignores it until their week.
- **Bounded review budget.** Commit one hour per day to OSS review, not unbounded time. The backlog is not an emergency.
- **Allow declining.** `wontfix` is a healthy state. Scope creep kills projects faster than bugs.
- **Grow maintainers.** After a contributor lands 5+ substantive PRs, offer commit access.
- **Maintainer emeritus.** A maintainer stepping back is not a failure. Name them as emeritus in `MAINTAINERS.md` and move on.
- **Decline mandatory features.** "Not planned — PRs welcome" is a valid response.

The fastest way to kill a project is to try to be infinitely responsive. Publish SLAs, meet them, and protect the rest of your time.
