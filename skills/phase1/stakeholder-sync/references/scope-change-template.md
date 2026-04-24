# Scope change record template

Use this when a stakeholder requests something outside the current agreed scope.
Fill it in, send it to the requestor for confirmation, then get written approval before
any work begins.

---

## Template

```markdown
## Scope change: [short description]

**Requested by:** [name]  
**Date received:** [YYYY-MM-DD]  
**Project / phase:** [project name, phase]

### What changes
[Specific description of what is being requested. Be precise — "add CSV export to the
user report screen" not "improve reporting".]

### Why
[Business or technical reason given by the requestor. One or two sentences.]

### Impact

| Area | Detail |
|------|--------|
| Timeline | +[X] days estimated; current milestone [date] would slip to [new date] |
| Design | [What existing design changes — new endpoints, schema changes, etc.] |
| Effort | [Rough estimate — hours or days] |
| Risk | Low / Medium / High — [one sentence on the main risk if added] |

### Decision

- [ ] Approved — proceed with change
- [ ] Rejected — not in scope for this phase
- [ ] Deferred — will be addressed in [phase / sprint / date]

**Decision owner:** [name]  
**Date approved / rejected:** [YYYY-MM-DD]  
**Notes:** [Any conditions, caveats, or follow-up required]
```

---

## Example (filled)

```markdown
## Scope change: Add CSV export to user report screen

**Requested by:** Sarah (product)  
**Date received:** 2026-04-20  
**Project / phase:** device-registry v2, phase 1

### What changes
Add a "Download CSV" button to the user report screen that exports the currently filtered
result set. Requires a new `/reports/export` endpoint and async job handling for large
result sets.

### Why
Sales is demoing next month and customers have asked for data portability. Current
phase 1 scope only includes the screen display.

### Impact

| Area | Detail |
|------|--------|
| Timeline | +5 days estimated; current milestone 2026-05-01 would slip to 2026-05-06 |
| Design | New endpoint, async job queue, S3 storage for export files |
| Effort | ~40 hours |
| Risk | Medium — async job handling is a new pattern in this service |

### Decision

- [ ] Approved — proceed with change
- [x] Deferred — will be addressed in phase 2

**Decision owner:** [engineering lead name]  
**Date approved / rejected:** 2026-04-21  
**Notes:** Phase 2 kickoff to include CSV export as a committed deliverable. Logged in
decision log as decision #14.
```

---

## After approval

1. Add a row to `docs/decision-log.md`
2. Update the project charter if scope sections change
3. Update any planning documents (sprint backlog, milestone list)
4. Notify the requestor in writing with the outcome
