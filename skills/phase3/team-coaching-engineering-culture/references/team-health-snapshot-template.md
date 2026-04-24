# Team Health Snapshot template

Fill this in within 20 minutes of finishing the quarterly retro. Save the completed file as `docs/team-health-YYYY-QN.md`.

---

## Team Health Snapshot: [Q? YYYY]

**Date:** [YYYY-MM-DD]
**Retro participants:** [names]

---

### Velocity (DORA — pull from delivery-metrics-dora output)

| Metric | This quarter | Last quarter | Trend |
|--------|-------------|-------------|-------|
| Deployment frequency | | | |
| Lead time (idea to prod) | | | |
| Change failure rate | | | |
| MTTR | | | |

If DORA numbers are not available for this quarter, note why and use qualitative ("faster than last quarter", "no major incidents").

---

### Quality signals

| Signal | Value | Notes |
|--------|-------|-------|
| Test coverage (overall) | | |
| PR cycle time (open to merge) | | Target: define yours |
| Review turnaround (request to first review) | | Target: define yours |
| Open debt items (from technical-debt-tracker) | | |

Add or remove rows to match what your team tracks. If you don't track something, either start tracking it or drop the row — don't leave it blank quarter after quarter.

---

### Team satisfaction (from retro — explicit, not assumed)

**What went well this quarter:**
- [item]
- [item]

**Main friction points:**
- [item]
- [item]

**Energy level** (ask directly in the retro — no score required, just a temperature check):
- [one sentence per person, or "team consensus: good / drained / mixed"]

---

### Risks

| Risk | Severity (High/Med/Low) | Owner | Mitigation / next step |
|------|------------------------|-------|----------------------|
| [e.g. Only one person can deploy to prod] | High | | |
| [e.g. No runbook for X] | Medium | | |
| [e.g. Skill gap in Y — no one has done Z before] | Low | | |

Knowledge concentration check: for each critical system or practice, is there more than one person who can operate it? If not, that is a High risk row.

Burnout signals to watch for: consistent late commits, skipped retros, "I'll just do it myself" patterns, mounting on-call load for one person. If you see these, name them here — do not assume they will self-resolve.

---

### Action items from retro

| Item | Owner | Due | Status |
|------|-------|-----|--------|
| [specific, actionable commitment from retro] | | | Open |
| | | | |
| | | | |

Maximum 3 items. If you have more, prioritise — a list of 8 commitments means none of them will happen.

Each item must be: specific enough that you will know in 90 days whether it was done. "Improve documentation" is not an action item. "Write runbook for cache invalidation process" is.

---

### Growth plan updates (summary)

List any changes made to individual Growth Plans this quarter:

| Person | Item added / closed / updated |
|--------|------------------------------|
| | |

Full Growth Plans are maintained per-person in `docs/growth-plan-[name].md`.

---

### Notes

Anything that doesn't fit the above sections — context for future retros, things to watch, decisions made about how the team works.

---

**Next retro scheduled:** [YYYY-MM-DD or "end of Q? YYYY"]
