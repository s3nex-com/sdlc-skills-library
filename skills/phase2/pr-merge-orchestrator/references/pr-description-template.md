# PR description template

Use this template for every pull request. A good PR description is the permanent record of a change — future engineers, incident responders, and reviewers depend on it. Generate it from the pipeline artifacts already produced, not from memory.

---

```markdown
## Summary

[2-3 sentences describing what this PR implements in plain English. Link to the PRD and design doc. State which phase of the implementation plan this completes.]

**PRD:** [link to docs/PRD.md]
**Design doc:** [link to docs/DESIGN.md]
**Implementation plan:** [link to docs/implementation-status.md]
**Phase:** Phase [N] of [M]
**Stories covered:** ST-NNN, ST-NNN, ST-NNN

---

## What changed

### Components added or modified

| Component | Change type | Description |
|-----------|------------|-------------|
| [Component / file / module] | New / Modified / Removed | [One sentence — what it does or why it changed] |
| | | |

### API changes

| Endpoint | Method | Change | Breaking? |
|----------|--------|--------|-----------|
| /v1/devices | POST | New endpoint | No — net new |
| /v1/devices/{id} | GET | New endpoint | No — net new |

[If no API changes: "No API changes in this PR."]

### Database changes

| Migration file | Direction | Description | Rollback safe? |
|---------------|-----------|-------------|---------------|
| [filename] | Forward | [What the migration does] | Yes / No — [reason if no] |

[If no DB changes: "No database migrations in this PR."]

### Configuration changes

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| [VAR_NAME] | Yes / No | [value] | [What it controls, when it was introduced] |

[If no config changes: "No new configuration variables."]

### Dependency changes

| Package | Version | Change | Reason |
|---------|---------|--------|--------|
| [package name] | [version] | Added / Updated / Removed | [Why] |

[If no dependency changes: "No dependency changes."]

---

## How to verify

### Automated verification

```bash
# Unit tests
[test command here]
# Expected: [N] tests, 0 failures

# Integration tests
[test command here]
# Expected: [N] tests, 0 failures

# Acceptance tests
[test command here]
# Expected: [N] scenarios, 0 failures

# Coverage
[coverage command]
# Current: [N]% (threshold: [N]%)
```

### Manual verification steps

To verify [primary story - ST-NNN]:
1. [Specific action — e.g., "Send POST /v1/devices with payload: {...}"]
2. [Expected result — e.g., "Response: 201 Created with device_id in body"]
3. [Follow-up action — e.g., "Send GET /v1/devices/{device_id}"]
4. [Expected result — e.g., "Response: 200 OK with device record"]

[Repeat for each major story in this PR]

---

## Security sign-off

- [ ] STRIDE analysis completed at design time — ADR-NNN
- [ ] Secure coding checklist applied during implementation — `docs/implementation-status.md` Phase [N]
- [ ] SAST scan: [PASS / N findings — all addressed with references]
- [ ] Dependency scan: [PASS / N CVEs — disposition: all below Critical threshold / addressed]
- [ ] Secret scanning: PASS
- [ ] Input validation applied to: [list new endpoints or handlers]

---

## Deployment notes

**Deployment strategy:** [Rolling / Blue-green / Canary / No infra change]
**Migration timing:** [N/A / Before deployment / After deployment]
**Deployment order:** [Single service / Service A then Service B]

**Rollback plan:**
- Trigger: [What condition triggers rollback — e.g., error rate > 1% sustained for 5 min]
- Steps:
  1. [Step]
  2. [Revert migration if applicable: `[command]`]
  3. [Redeploy previous version: `[command]`]

---

## Pre-merge checklist

- [ ] All CI checks pass on this commit (not a previous commit)
- [ ] Branch is up to date with `main` (rebased or merged within the last 24 hours)
- [ ] Self-reviewed: I have read every line of this diff as if reviewing someone else's work
- [ ] Tests are meaningful: assertions verify behaviour, not implementation details
- [ ] No debug code, temporary workarounds, or TODOs added without a linked issue
- [ ] Documentation updated: [runbooks / API guide / architecture diagrams — or "no updates needed"]
- [ ] Implementation status doc updated: all Phase [N] tasks marked Complete

---

## ADRs referenced

- [ADR-NNN: Decision title](link)
- [ADR-NNN: Decision title](link)

[If none: "No new ADRs. Existing ADRs: ADR-NNN, ADR-NNN."]

---

## Related

- PRD: [link]
- Design doc: [link]
- Related PRs: [links or "none"]
- Issues / tickets: [links]
```

---

## How to generate this description automatically

Use the following pipeline artifacts as source material:

| PR section | Source artifact | Where to find it |
|------------|----------------|-----------------|
| Summary | DESIGN.md overview + implementation-status.md | `docs/` |
| Stories covered | Traceability matrix | `docs/traceability-matrix.md` |
| Components changed | implementation-status.md phase tasks | `docs/implementation-status.md` |
| API changes | OpenAPI spec diff | Run `diff_contracts.py` |
| DB changes | Migration file names | `db/migrations/` |
| Config changes | Implementation notes | `docs/implementation-status.md` task notes |
| Test commands | implementation-status.md | Task 1.x test stubs section |
| Security sign-off | implementation-status.md security gate | Per-task security gate |
| ADRs | ADR index | `docs/adr/README.md` |
