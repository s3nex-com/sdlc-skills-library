# skills/phase1/ — Foundation

Phase 1 skills run at the start of any project. They establish what is being built, why it is being built, what constraints apply, and what the architecture looks like. If phase 1 is weak, every downstream phase suffers from unclear scope, misaligned design, and missed risks.

"Move fast" means getting to implementation quickly — not skipping the foundation. A strong phase 1 makes phase 2 faster because the team spends less time re-litigating decisions.

---

## The 10 skills

| Skill | What it does |
|-------|-------------|
| **prd-creator** | Creates or validates the Product Requirements Document. Pipeline entry point. Nothing downstream starts without an approved PRD. |
| **requirements-tracer** | Decomposes the PRD into BDD stories and testable acceptance criteria. Builds the traceability matrix from requirement to code to test. |
| **design-doc-generator** | Synthesises PRD + requirements + specs + ADRs into an implementation-ready `DESIGN.md`. The bridge between "what" and "how". |
| **specification-driven-development** | Writes API contracts (OpenAPI, Protobuf, AsyncAPI) before implementation begins. Freezes the contract before either side builds against it. |
| **architecture-review-governance** | Reviews new services and architectures systematically. Covers NFRs, anti-patterns, trade-off analysis, and quarterly health reviews. |
| **architecture-decision-records** | Documents significant technical decisions permanently. Context, alternatives considered, consequences. Future engineers must be able to understand why. |
| **technical-risk-management** | Identifies and tracks technical risks before they become incidents. P×I matrix, risk register, kill criteria. |
| **security-audit-secure-sdlc** | Threat modelling (STRIDE), secure coding standards, security gates in CI, secrets management, NIST SSDF compliance. Runs alongside all phases. |
| **stakeholder-sync** | Async-first stakeholder communication: decision logging, scope change handling, status cadence, lean escalation, project scope/charter and RACI for a small team. |
| **data-governance-privacy** | Data classification, PIAs, GDPR/CCPA workflows, retention policy, EU AI Act data transparency. |

---

## Design principles for all phase 1 skills

**No enterprise ceremony.** Write for a senior engineer doing hands-on work. A 3-person team does not need a steering committee. A 2-week sprint does not need a formal scope change board. Proportionality is not optional — it is part of the philosophy.

**Every skill pushes toward an output that unblocks the next stage.** A PRD is useless if the requirements-tracer cannot start after it. A design doc is useless if code-implementer cannot start after it. Each phase 1 skill should end with a concrete artefact that is immediately useful downstream.

**"Move fast" and foundation are not opposites.** The right amount of phase 1 for a small team is: clear goals, clear NFRs, clear API contracts, one design review, and known risks. That is achievable in days, not weeks.

**Framing conventions:** Write "team", "stakeholders", "engineering lead", "leadership". Do not write "partner company", "both companies", "the client", "the vendor". This library is for internal team use.

---

## Pipeline position

Phase 1 feeds directly into phase 2. The key handoffs:

- `prd-creator` → `requirements-tracer` → `design-doc-generator` → `code-implementer`
- `specification-driven-development` → `api-contract-enforcer` (phase 2)
- `architecture-decision-records` → feeds `design-doc-generator` and informs `code-implementer`
- `security-audit-secure-sdlc` → security gate at every subsequent phase

The `sdlc-orchestrator` manages these handoffs. When working in phase 1 standalone (not through the orchestrator), verify that your outputs match what the next skill expects as inputs.

---

## When editing a phase 1 skill

Check the "when NOT to use it" section before adding anything. Phase 1 skills have clean boundaries:
- Technical decisions belong in `architecture-decision-records`, not in the PRD
- Runtime contract enforcement belongs in `api-contract-enforcer` (phase 2), not here
- Writing runbooks belongs in `documentation-system-design` (phase 2), not here

If you find a phase 1 skill growing into phase 2 territory, split the content.
