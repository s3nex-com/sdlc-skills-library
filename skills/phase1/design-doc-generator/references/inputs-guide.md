# Inputs guide: reading PRD, specs, and ADRs for design

This guide explains what to extract from each upstream artifact when generating a design document. Treat each artifact as a read-only source of truth — reference it, do not duplicate it.

---

## Reading the PRD (PRD.md)

The PRD answers WHAT and WHY. The design doc answers HOW.

| PRD section | What to extract for the design doc | Where it goes in DESIGN.md |
|-------------|----------------------------------|--------------------------|
| Section 1 (Executive summary) | Feature name, high-level scope | Section 1 (Overview) introduction |
| Section 2 (Problem statement) | Context that motivates design choices | Section 1 (Overview) background |
| Section 3 (Goals) | Success targets that constrain trade-offs | Section 9 (Performance) — link goals to design choices |
| Section 4 (Non-goals) | What the design must NOT include | Section 1 (Overview) exclusions |
| Section 5 (User personas) | Actors in the system context diagram | Section 2 (Context diagram) |
| Section 6 (Functional requirements) | What each component must do | Section 3 (Component design) responsibilities |
| Section 7 (NFRs) | Measurable constraints the design must satisfy | Section 9 (Performance and reliability) — one mechanism per NFR |
| Section 8 (Constraints) | Technology mandates, integration requirements | Section 7 (Infrastructure), Section 5 (API contracts) |
| Section 8 (Assumptions) | Design assumptions to validate | Section 1 (Overview), flag in Section 11 |
| Section 10 (Out of scope) | What not to design | Section 1 (Overview) exclusions |
| Section 11 (Open questions) | Unresolved decisions | Section 11 (Open questions) — carry forward with owners |

**Key extractions from the PRD:**
- Every NFR must have a corresponding mechanism in DESIGN.md Section 9. If you cannot define a mechanism for an NFR, it means either the NFR is not achievable or the design is incomplete.
- Constraints from PRD section 8 directly constrain technology and architecture choices. Do not ignore them.
- Open questions from PRD section 11 that are still unresolved become DQ items in DESIGN.md section 11.

---

## Reading the traceability matrix

The traceability matrix tells you what the design must implement. Every Story ID (ST-NNN) in the matrix must be traceable through the design.

**What to extract:**

1. **Story list** — the full list of ST-NNN IDs. Every story must be covered by at least one data flow in DESIGN.md Section 4.

2. **BDD acceptance criteria** — the Given/When/Then for each story. These define the exact behaviour the design must enable. If the design does not enable the acceptance criterion to pass, the design is wrong.

3. **Feature groupings** — stories grouped by feature tell you which components are related and likely to interact. This informs component boundaries in Section 3.

**How to use it:**
- For each story: ask "which component(s) are involved?" and "what is the sequence of calls?" — this gives you Section 3 and Section 4 content.
- Stories that share a component tell you about that component's responsibilities.
- Stories that span multiple components tell you about the integration points (Section 2 diagram arrows).

---

## Reading API specs (OpenAPI / Protobuf / AsyncAPI)

API specs define the contract boundaries. The design doc REFERENCES specs, not duplicates them.

**What to extract from OpenAPI specs:**

| Spec element | What to extract for DESIGN.md |
|---|---|
| Paths and methods | Section 5 table: endpoint list |
| Request/response schemas | Section 6: identify the data model entities implied by schemas |
| Security schemes | Section 8: authentication mechanism |
| Parameters | Section 3: component inputs |
| Error responses | Section 4: error paths in sequence diagrams |

**What to extract from Protobuf specs:**
- Service definitions → component boundaries (each service is a candidate component)
- Message types → data model entities in Section 6
- RPC methods → operations in Section 4 sequence diagrams

**What to extract from AsyncAPI specs:**
- Channels → event flow paths in Section 4
- Message schemas → data model entities in Section 6
- Publish/subscribe model → async boundaries in Section 3 (what components are producers vs consumers)

**Common mistake:** Copying endpoint definitions from the spec into the design doc. Do not do this — it creates duplication that diverges over time. Reference the spec file instead.

---

## Reading the ADR index

ADRs record decisions already made. The design doc must respect them — do not re-litigate closed ADRs.

**For each ADR, extract:**
1. **Status** — accepted, superseded, deprecated. Only accepted ADRs are constraints. Superseded ADRs show you what was tried and rejected.
2. **Decision** — the specific choice made (e.g., "We will use PostgreSQL", "We will use JWT for authentication")
3. **Consequences** — what the decision means for other design choices

**How to use ADRs in the design doc:**
- When a design choice is constrained by an ADR: reference the ADR by number in Section 8 (security), Section 3 (component design), or Section 7 (infrastructure) — wherever the decision manifests
- When you need to make a design choice: check if there is an ADR for it first. If yes, follow it. If no, you may need to create one.
- When an ADR conflicts with a PRD requirement: this is a flag — raise it before designing. Do not silently choose one over the other.

**ADR reference format in DESIGN.md:**
```
[Design choice]. See ADR-NNN: [Title].
```

Example:
```
Authentication uses JWT signed with RS256. See ADR-007: Authentication mechanism selection.
```

---

## Reading architecture review findings

If an architecture review has been conducted for a prior version of this design (or for related systems), extract:

1. **Approved patterns** — patterns the architecture review has blessed. Use them without justification.
2. **Rejected patterns (anti-patterns)** — patterns that have been explicitly rejected. Do not use them.
3. **Open findings** — review findings that have not yet been resolved. These become DQ items in DESIGN.md Section 11.
4. **NFR definitions** — the review may have refined NFRs from the PRD. Use the most specific version.

---

## Gap identification

After reading all inputs, identify gaps before writing the design doc:

| Gap type | Example | Action |
|----------|---------|--------|
| Story with no clear component owner | ST-015 involves 3 components but none claim responsibility | Assign ownership explicitly in Section 3 |
| NFR with no obvious design mechanism | "99.9% availability" but no HA design exists yet | Design the HA mechanism or flag as DQ |
| API spec exists but no data model | Spec uses a `Device` schema but no `devices` table is designed | Add the entity to Section 6 |
| ADR conflict with PRD | ADR-004 says "no Redis" but PRD NFR requires sub-10ms caching | Raise as DQ-001 before designing around it |
| Open PRD question blocks design | OQ-003 unresolved and affects the data model | Do not design the affected component; add as DQ |

List all identified gaps in DESIGN.md Section 11 before presenting the draft. Do not silently assume an answer to a gap.
