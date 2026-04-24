# Change management and approvals

Every framework in scope for this track — FedRAMP, SOC 2, ISO 27001, CMMC — requires documented change management with separation of duties. "Documented" does not mean paper. It means: the system of record shows who requested, who reviewed, who approved, who deployed, and those are not all the same person.

For a 3-5 person team the approval workflow must be mechanical — enforced by tooling, not goodwill. This document describes the approval workflow, separation-of-duties enforcement via GitHub CODEOWNERS and branch protection, the emergency change path, and approval logging.

---

## Change types

| Type | Definition | Approval requirement |
|------|------------|----------------------|
| Standard | Pre-approved low-risk change pattern (dependency patch bump within approved floor, log verbosity tweak, docs). | 1 reviewer, any team member who is not the author. Pattern must be in the standard-change catalog. |
| Normal | Anything not covered by standard. Feature code, infra change, config change. | 1 reviewer from CODEOWNERS for the touched area, who is not the author. Passing CI + security checks. |
| Significant | Architecture change, new data store, new external integration, crypto change, authZ/authN change, anything touching in-scope control implementation. | 2 reviewers, one being a security-owned path reviewer (often the same person wearing that hat). |
| Emergency | Production impact remediation when the normal path is too slow. | Retroactive approval within 24h. See emergency change process below. |

The standard-change catalog lives in `docs/change-catalog.md`. Adding a pattern to that catalog is itself a Normal change requiring reviewer approval.

---

## Separation of duties — the hard rule

The engineer who authored the change cannot:

1. Approve their own PR.
2. Merge their own PR to a protected branch without an approving reviewer.
3. Deploy their change to production without the deployment approval being given by another person.

Rules 1 and 2 are enforced by branch protection. Rule 3 is enforced by the deployment system's approval gate.

### GitHub enforcement mechanics

**Branch protection on `main` (and any release branch):**

- Require pull request before merging.
- Require at least 1 approving review from CODEOWNERS.
- Dismiss stale approvals on new commits.
- Require review from CODEOWNERS.
- Require status checks to pass (CI, security scan, any compliance check).
- Require conversation resolution before merging.
- Require linear history (prevent merge commits that bypass review).
- Include administrators (no bypass for team leads).
- Restrict who can push to matching branches (empty — merge only via PR).

**CODEOWNERS file:**

Every in-scope directory has a code owner. Minimum structure:

```
# Core platform
/services/auth/           @team-auth @security-reviewer
/services/payments/       @team-platform @security-reviewer
/infra/                   @team-infra @security-reviewer

# Compliance-sensitive files
/docs/evidence/           @security-reviewer
/.github/workflows/       @team-infra @security-reviewer
/scripts/deploy/          @team-infra @security-reviewer
```

For a team of 3-5 where every engineer is in every group, CODEOWNERS still does useful work: the rule "reviewer ≠ author" combined with "reviewer must be a CODEOWNER" leaves only the other 2-4 people eligible.

### Deployment approval

Production deploys require a manual approval step in the deployment system (GitHub Actions environments with required reviewers, Argo CD rollout gates, Spinnaker pipelines, whatever you use). The approver list for the production environment excludes the actor who triggered the deploy.

For GitHub Actions:

```yaml
jobs:
  deploy-prod:
    environment:
      name: production
      # environment is configured in Settings → Environments with
      # required reviewers = the deploy-approvers group
      #   and "Prevent self-review" = true
    steps:
      - ...
```

For other systems, the equivalent config must: (a) require an explicit approval before the deploy executes, and (b) forbid the triggerer from being the approver.

---

## Approval logging

Every approval event must produce a durable record with these fields:

| Field | Source |
|-------|--------|
| Change identifier | PR number or deploy ID |
| Author | Git commit author, GitHub login |
| Reviewer(s) | GitHub PR reviewer, with approval timestamp |
| Deployer | GitHub Actions actor or equivalent |
| Deploy approver | Environment approver |
| Change type | Standard / Normal / Significant / Emergency |
| Control IDs touched | Listed in PR description, per track convention |
| Deploy timestamp | From deployment system |
| Rollback executed? | Boolean, timestamp if yes |

GitHub already captures most of this. The gap fields — change type, control IDs touched, rollback status — go into the PR template:

```markdown
## Change type
- [ ] Standard (pre-approved pattern: <pattern name>)
- [ ] Normal
- [ ] Significant (2 reviewers required)
- [ ] Emergency (retroactive approval)

## Controls touched
<!-- List the control IDs whose implementation this change affects.
     Examples: AC-6, CC6.1, SI-2. Use "none" if no in-scope control is touched. -->

## Evidence artifacts produced
<!-- Paths under docs/evidence/ that this change adds or updates. -->
```

On a monthly cadence, export the PR + deploy history to `docs/evidence/CM-3/<YYYY-MM>/` as the change management evidence for that window. Use a script, not manual copy-paste.

---

## Emergency change process

An emergency change is a production change required to stop or reduce an active incident, where waiting for normal review would extend impact.

### Who can declare

The incident commander for the active incident. For a team too small to have a formal IC role, the on-call engineer declaring the incident is the declarer.

### What is permitted

1. Direct commit to `main` from a protected admin identity (break-glass account) IF branch protection cannot be satisfied in time. Use sparingly — it is auditable but costly.
2. Bypass of the deploy approval gate via the break-glass deploy workflow (logged separately).
3. Standard PR + merge with a reduced reviewer count (1 any-person review), if a second reviewer is unreachable.

### Mandatory follow-up within 24 hours

- Retroactive PR opened referencing the emergency change, describing what was done and why.
- Second reviewer assigned and approves the retroactive PR.
- Incident postmortem scheduled, which in this track triggers regulatory notification checks (see `vulnerability-disclosure-policy.md` and track TRACK.md).
- Evidence archived to `docs/evidence/CM-3/emergency/<date>/` with incident ID, timeline, break-glass actor identity, and commits made.

### Audit trail for break-glass

Break-glass accounts must:

- Have MFA (no exceptions, including for the break-glass account itself).
- Emit a high-severity alert on any authentication event.
- Have their credentials rotated within 24h of use.
- Be used only by the declared incident commander.

Any break-glass usage not followed by a postmortem within 7 days is an audit finding.

---

## Integration with other skills

- `devops-pipeline-governance` — sets up the CI/CD gates that enforce this workflow. Its output should include the CODEOWNERS file, branch protection config, and deployment environment config as deliverables.
- `pr-merge-orchestrator` — operates within this workflow. Its checklist must include "reviewer is not author" and "controls-touched field filled" as hard gates.
- `incident-postmortem` — triggered automatically for emergency changes.
- `release-readiness` — verifies the approval log for the release is complete before ship.

---

## Red flags in an audit

If any of these show up in a sample, expect a finding:

1. A PR merged with the author listed as the sole reviewer.
2. A deploy whose triggerer and approver are the same.
3. An emergency change with no follow-up PR after 48 hours.
4. A gap in the change log — a production commit with no corresponding PR.
5. A direct push to `main` from a non-break-glass account.
6. A CODEOWNERS entry pointing to a user no longer on the team.

Run a monthly self-check script against the PR and deploy history to catch these before the assessor does. Script output goes into the monthly evidence bundle.
