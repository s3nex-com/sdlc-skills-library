# Contract freeze process

## Purpose

A frozen contract is a mutual commitment. Once frozen, no unilateral changes are permitted. This process establishes the formal sign-off and the change control procedure that applies after freezing.

---

## Pre-freeze requirements

Before a contract can be frozen, ALL of the following must be true:

- [ ] The contract review checklist has been completed with no Critical failures
- [ ] Both companies' technical leads have reviewed the spec
- [ ] All review findings have been resolved or explicitly accepted with documented rationale
- [ ] At least one example exists for every operation's request and success response
- [ ] The spec is stored in version control
- [ ] The spec version number is set correctly (e.g., `1.0.0` for initial freeze)

---

## Freeze steps

### Step 1: Final review

Both companies' lead engineers conduct a final review pass using the contract review checklist. Any remaining Critical findings block the freeze. High findings require explicit sign-off to proceed.

### Step 2: Sign-off record

Both parties send an explicit written approval. An email with the subject line below is sufficient — no formal signature process required unless specified in the project charter.

**Subject:** `[CONTRACT FREEZE APPROVAL] {Spec name} v{version} — {Company name} approval`

**Body template:**
```
I confirm that [Company name] approves the freeze of {spec name} version {version}
as of {date}.

Spec location: {git repository and file path}
Git commit: {full commit SHA}

Reviewed by: {name, role}
Approved by: {name, role — if different from reviewer}

Outstanding items accepted without resolution:
- {item, rationale} OR "None"
```

Both companies must send this email before the spec is tagged as frozen.

### Step 3: Version control tagging

After both approvals are received:

1. Create a git tag for the freeze: `contract/{spec-name}/v{version}-frozen`
   ```bash
   git tag contract/telemetry-ingestion-api/v1.0.0-frozen {commit-sha}
   git push origin contract/telemetry-ingestion-api/v1.0.0-frozen
   ```

2. Apply branch protection to the spec file path (GitHub example):
   - Require PR review from both companies' technical leads before merging changes
   - Do not allow direct pushes to the spec file on main

3. Store the sign-off emails (or links to them) in the project governance repository.

---

## Post-freeze change control

After a contract is frozen, changes follow this process:

### Non-breaking and additive changes (new optional fields, new endpoints)

1. Author submits a PR with the proposed spec change
2. `scripts/diff_contracts.py` is run automatically by CI/CD, confirming the change is non-breaking
3. Technical lead from both companies reviews and approves the PR
4. The spec version is incremented (minor version bump: `1.0.0` → `1.1.0`)
5. A new freeze tag is created for the updated spec
6. Both companies are notified of the change and the effective date

### Breaking changes (removed fields, changed types, removed endpoints)

Breaking changes require a higher level of sign-off because they require coordinated updates to both companies' code.

1. Author submits a change proposal with impact analysis (see `../requirements-tracer/references/scope-impact-template.md`)
2. Both companies' engineering managers review and approve
3. A migration timeline is agreed: minimum 4 weeks notice for cross-company changes
4. Deprecated endpoints/fields are marked in the spec with `deprecated: true` and a sunset date
5. The spec version receives a major version bump: `1.x.x` → `2.0.0`
6. The new version is deployed alongside the old version for the agreed migration period
7. After the migration period, the old version is retired per the sunset date

### Emergency changes (security vulnerabilities)

If a security vulnerability requires an immediate breaking change:

1. Notify both VP Engineering leads immediately (same day)
2. Describe the security risk and the minimum change required
3. Agree the change and timeline verbally, then document in writing
4. The change is made and tagged with a security release note
5. Both companies update their implementations within the agreed security SLA

---

## Freeze sign-off record format

Keep this record in the project governance repository for audit purposes.

```markdown
# Contract freeze record: {spec name}

**Version frozen:** {version}
**Freeze date:** {date}
**Spec location:** {git repo and file path}
**Frozen commit SHA:** {full SHA}

## Company A sign-off
**Reviewer:** {name, role}
**Approver:** {name, role}
**Date:** {date}
**Email reference:** {link or filename}

## Company B sign-off
**Reviewer:** {name, role}
**Approver:** {name, role}
**Date:** {date}
**Email reference:** {link or filename}

## Outstanding items accepted without resolution
| Item | Severity | Rationale for acceptance |
|------|----------|-------------------------|
| {item} | {severity} | {rationale} |

## Subsequent versions
| Version | Date | Change type | PR link |
|---------|------|------------|---------|
| 1.1.0 | {date} | Non-breaking: added optional `metadata` field | {PR link} |
```
