# Decision log template

File: `docs/decision-log.md`

---

## What counts as a significant decision

Log a decision when it affects any of the following:
- Scope (what is being built or not built)
- Timeline (a date or milestone changes)
- Architecture or technology choice (the stakeholder cares about it, or it creates a constraint)
- External commitments (something was agreed with a client, user, or partner)
- Security posture (an exception was made, a requirement relaxed)

Do not log every implementation detail. Log the decisions someone might later ask
"who decided that, and why?"

---

## Format

```markdown
| Date | Decision | Rationale | Owner | Alternatives rejected |
|------|----------|-----------|-------|-----------------------|
```

---

## Example entries

| Date | Decision | Rationale | Owner | Alternatives rejected |
|------|----------|-----------|-------|-----------------------|
| 2026-04-20 | Use PostgreSQL as primary store | Team has expertise; relational model fits; no need for document flexibility | [name] | MongoDB — JSON flexibility not needed for this schema |
| 2026-04-20 | Defer CSV export to phase 2 | Scope change request received; timeline impact too high for phase 1 | [name] | Include in phase 1 — adds 5 days; would slip milestone |
| 2026-04-21 | Use 7-day JWT expiry | Short enough for security; long enough to avoid re-auth friction | [name] | 24h — too frequent; 30-day — revocation window too wide |
| 2026-04-22 | Accept staging environment downtime Thu 22:00–23:00 | Required for infrastructure migration; low traffic window | [name] | Daytime window — higher user impact |

---

## Usage notes

- One row per decision. Keep rationale to one sentence — enough to reconstruct why.
- "Owner" is the person who made the call, not a committee.
- "Alternatives rejected" is the most important column for future readers. Without it,
  the log just records what happened, not why the alternatives were worse.
- Append only. Never edit or delete rows. If a decision is reversed, add a new row
  referencing the original: "Reverts decision 2026-04-20: PostgreSQL → migrating to..."
