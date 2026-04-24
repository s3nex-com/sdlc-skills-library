# Merge runbook

Step-by-step process for merging a PR. Follow this in order. This runbook applies to any merge into `main`. For release branch merges, also consult `release-readiness`.

---

## Pre-flight (before requesting review)

1. Run `references/pre-merge-checklist.md` — all items must pass
2. Generate PR description using `references/pr-description-template.md`
3. Push final branch state to remote: `git push origin [branch]`
4. Confirm CI is green on the latest commit (not a cached status)

---

## Creating the PR

```bash
# Using GitHub CLI (preferred — creates PR from branch to main)
gh pr create \
  --title "[type]: [concise description] ([Phase N])" \
  --body "$(cat docs/pr-description.md)" \
  --reviewer "[reviewer1],[reviewer2]" \
  --label "[phase-N],[feature-name]"
```

**PR title format:**
- `feat(scope): description` — new feature
- `fix(scope): description` — bug fix
- `refactor(scope): description` — refactor, no behaviour change
- `chore(scope): description` — non-functional change

**Title length:** Under 70 characters. Put detail in the description, not the title.

**Reviewer assignment:**
| Scenario | Reviewers to assign |
|----------|---------------------|
| Standard PR | 2 engineers (1 senior) |
| New auth/security change | + Security reviewer |
| DB migration | + Data lead / DBA |
| Cross-company delivery | + Partner company reviewer |
| Architecture change | + Architecture lead |

---

## During review

### Monitoring the review

Check review status daily during the SLA window:
- Small PR: first response within 4 business hours
- Medium PR (200–500 lines): within 1 business day
- Large PR (500–1000 lines): within 1 business day

If a reviewer has not responded within the SLA:
1. Ping them directly (not a broadcast message)
2. If still unresponsive after one additional business day: escalate to the engineering lead

### Responding to review comments

For each `[Blocking]` comment:
1. Read the comment fully before responding
2. Either fix the issue OR write a documented counter-argument
3. If fixing: commit the fix, push, reply on the comment with what was done
4. If disputing: explain why the current implementation is correct; do not just re-assert
5. Re-request review from the specific reviewer who left the blocking comment

For each `[Question]`:
1. Answer in the comment thread
2. If the question reveals a missing piece of context: update the PR description or add a code comment
3. The reviewer re-classifies after your response — do not self-approve

For each `[Suggestion]`:
1. Either apply it (preferred if it improves the code) or explain why you are not
2. A "wontfix" decision must be explained — "I disagree" is not sufficient

**Never** push new commits to the branch without checking if they invalidate any approvals. In most repo configurations, a new commit requires re-approval. Confirm before adding commits post-approval.

### Handling a "Request changes" review

1. Do not re-request review until ALL blocking findings are addressed
2. Address every comment — including suggestions (respond to them even if not applying the change)
3. When all blocking findings are resolved: re-request review from the reviewer (only)
4. The reviewer does a targeted re-review of the blocking items; they do not re-review the entire PR

---

## Pre-merge final check (immediately before merging)

Do this check right before clicking merge — not an hour before.

```bash
# 1. Confirm CI is green on the LATEST commit
gh pr checks [PR number]

# 2. Confirm branch is up to date
git fetch origin main
git log HEAD..origin/main --oneline
# Should be empty (no commits on main that are not in this branch)

# 3. If behind main: rebase
git rebase origin/main
git push --force-with-lease origin [branch]
# Then wait for CI to re-run and confirm it is green

# 4. Confirm approvals are still valid
gh pr view [PR number] --json reviews
# All required reviewers must show "APPROVED"
# If any review was submitted before the last commit, it may be invalidated — check repo policy
```

---

## Merge execution

### Squash merge (default for feature PRs)

```bash
gh pr merge [PR number] --squash --subject "[type](scope): [description]" --body "$(cat docs/merge-commit-body.md)"
```

The merge commit message body should include:
- Stories covered: ST-NNN list
- PRD reference
- ADRs: ADR-NNN list

**Good squash commit message:**
```
feat(devices): implement device registration API (Phase 1)

Implements POST /v1/devices, GET /v1/devices/{id} per spec device-api.yaml v1.2.
Covers: ST-001 (device registration), ST-002 (device retrieval), ST-003 (duplicate detection).
Migration: 0003_add_devices_table (additive, backward compatible).

ADRs: ADR-007 (JWT auth), ADR-012 (audit log)
PRD: docs/PRD.md
Design: docs/DESIGN.md
```

### Merge commit (for hotfixes and release branches)

```bash
gh pr merge [PR number] --merge
```

---

## Post-merge verification

```bash
# 1. Confirm CI passes on main after merge
gh run list --branch main --limit 1
gh run view [run-id]

# 2. Confirm the merged commit appears correctly
git log origin/main --oneline --limit 5

# 3. If CI fails on main after merge: create a revert PR immediately
gh pr create --title "revert: [original PR title]" --body "Reverting [PR number] — CI failure on main" --head revert-[PR number]
# Do not leave a broken main branch unaddressed
```

---

## Release tagging

Tag every milestone merge. A milestone is: a complete phase, a delivery to the partner company, or a production deployment.

```bash
# Determine the next version (semantic versioning)
git tag --sort=-version:refname | head -5
# Decide: major (breaking), minor (new feature), patch (fix)

# Create and push the tag
git tag -a v[M].[N].[P] -m "$(cat <<'EOF'
Release v[M].[N].[P]: [Phase/milestone name]

Stories: ST-NNN, ST-NNN
PRD: docs/PRD.md v[version]
Design: docs/DESIGN.md v[version]
EOF
)"

git push origin v[M].[N].[P]
```

---

## Post-merge tasks

Complete these within 1 business day of merge:

1. **Update implementation status:**
   ```
   docs/implementation-status.md → Phase [N]: Status = Merged, date = [today]
   ```

2. **Update pipeline dashboard:**
   ```
   docs/sdlc-status.md → Stage 8 = Complete, Stage 9 = In progress
   ```

3. **Notify stakeholders** (if cross-company delivery):
   - Use `stakeholder-sync` delivery announcement pattern
   - Include: what was delivered, which stories are done, the release tag, verification instructions

4. **Trigger Stage 9** (documentation):
   - Invoke `documentation-system-design`
   - Update runbooks for any new operational scenarios
   - Update C4 diagrams if new components were added
   - Update API usage guide for new endpoints

5. **Flag for observability check:**
   - Verify new metrics and log statements appear in the monitoring dashboard after deployment
   - Confirm alerting rules are in place for any new SLOs
   - If monitoring is not in place: raise as a blocker for production deployment

---

## Emergency: revert after merge

If a critical issue is found after merge, before a revert:

1. **Assess impact:** Is the issue P1 (users affected now) or P2 (degraded, not down)?
2. **P1:** Revert immediately using the command below, then investigate
3. **P2:** Investigate first; revert only if a fix cannot be deployed within the agreed error budget

```bash
# Revert via PR (preferred — maintains history)
gh pr create \
  --title "revert: [original PR title]" \
  --body "Reverts PR #[number]. Reason: [specific issue]. Root cause under investigation." \
  --base main

# Review and merge the revert PR immediately (it still needs CI to pass)
```

After reverting: trigger `incident-postmortem` if users were affected.
