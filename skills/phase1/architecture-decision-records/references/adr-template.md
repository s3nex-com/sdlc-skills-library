# ADR template

## Instructions

Copy the template below for each new ADR. File name: `ADR-NNN-short-title-in-kebab-case.md`

Fill in every field. Do not leave fields blank. For "Alternatives considered", provide at minimum two genuine alternatives — if you can only think of one alternative, spend more time researching before writing the ADR.

---

# ADR-[NNN]: [Title — state the decision, not the question]

**Date:** [YYYY-MM-DD — the date the decision was made]
**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-NNN]
**Owner:** [Name, Role, Company — who made or approved this decision]
**Review date:** [When should this decision be re-evaluated? e.g., "Phase 2 planning" or "2025-01-01"]

---

## Context

[What situation, constraint, or requirement forced this decision? What was the state of the system when this decision was made? What pressures — technical, commercial, timeline — existed? Write enough context that someone reading this 2 years later understands WHY this decision had to be made. Minimum 3 sentences. Do not describe the decision here — only the context that made a decision necessary.]

---

## Decision

[State precisely what was decided. Use active voice: "We will use X" not "It was decided to use X". Be specific: name the technology, version, pattern, or policy being adopted. One or two sentences maximum — clarity over comprehensiveness here.]

---

## Alternatives considered

| Alternative | Pros | Cons | Reason rejected |
|-------------|------|------|-----------------|
| [Option 1 — chosen option] | [genuine benefits] | [genuine costs and risks] | Chosen |
| [Option 2] | [genuine benefits] | [genuine costs and risks] | [specific reason not chosen] |
| [Option 3] | [genuine benefits] | [genuine costs and risks] | [specific reason not chosen] |

---

## Consequences

**What becomes easier as a result of this decision:**
- [specific outcome]
- [specific outcome]

**What becomes harder or more constrained:**
- [specific outcome — every decision has costs; if this list is empty, look harder]
- [specific outcome]

**New risks introduced:**
- [risk] — [how it will be mitigated]
- [risk] — [how it will be mitigated]

**Dependencies created (things that must now be true for this decision to succeed):**
- [dependency]
- [dependency]

---

---

# Worked example: ADR-004

# ADR-004: Use PostgreSQL as the primary relational data store

**Date:** 2024-03-10
**Status:** Accepted
**Owner:** Alice Chen, Lead Architect, Company A
**Review date:** Phase 2 planning — re-evaluate if write throughput exceeds 50,000 writes/second sustained

---

## Context

The platform requires a persistent data store for device registry, alert configurations, and user account data. These data sets share three characteristics: they have well-defined relational structures (devices belong to organisations, alerts belong to device types), they require strong consistency (a device's configuration must be consistent across all readers), and they are accessed primarily via structured queries with filtering and aggregation. The engineering teams on both sides have significant PostgreSQL experience. The system is expected to reach 10,000 registered devices and 500,000 alert configuration records in Phase 1. Phase 2 growth projections are unclear but conservatively estimated at 10× Phase 1 volume over 24 months.

A previous prototype used MongoDB for this workload. During prototype evaluation, the team identified two issues: the schema flexibility of MongoDB was a liability (inconsistent documents in development caused hard-to-debug query failures), and MongoDB's default eventual consistency model required additional application-level complexity to achieve the consistency guarantees needed for device configuration data.

---

## Decision

We will use PostgreSQL 15 (managed via AWS RDS) as the primary data store for device registry, alert configurations, and user account data.

---

## Alternatives considered

| Alternative | Pros | Cons | Reason rejected |
|-------------|------|------|-----------------|
| **PostgreSQL 15 (chosen)** | ACID transactions, strong consistency, excellent query planner, proven at scale, team expertise, rich ecosystem | Horizontal write scaling requires sharding (not needed at Phase 1 scale); managed cost higher than self-hosted | Chosen |
| MongoDB | Schema flexibility, document model natural for device configuration, horizontal scaling built in | Eventual consistency by default; schema flexibility is a liability not a benefit for structured data; prototype issues; less team expertise | Consistency issues surfaced in prototype; team expertise gap |
| MySQL 8 | Mature, widely supported, good performance | Fewer advanced features (partial indexes, JSONB, CTEs performance); less team expertise than PostgreSQL | PostgreSQL more capable for analytics queries planned in Phase 2 |
| CockroachDB | Distributed, globally consistent, horizontal scaling built in | Operational complexity; cost; team has no CockroachDB experience; Phase 1 scale does not justify it | Premature optimisation; team expertise gap |

---

## Consequences

**What becomes easier:**
- ACID transactions across device registry and alert configuration tables — no distributed transaction complexity
- Complex analytical queries using PostgreSQL's window functions and CTEs for reporting
- Schema evolution using migrations (Alembic/Flyway) with well-understood patterns
- Debugging with psql and standard PostgreSQL tooling that both teams know

**What becomes harder or more constrained:**
- Horizontal write scaling if write throughput exceeds ~50,000 writes/second sustained — would require read replicas or sharding, neither of which is in scope for Phase 1
- Schema migrations must be backward compatible to support zero-downtime deployments (this is a constraint, but a healthy one)
- Cross-service data access is forbidden by the architecture principles — all consumers must go through the service API, not directly to the database

**New risks introduced:**
- AWS RDS cost at scale — mitigated by cost alerts configured at 120% of baseline spend
- Single-region availability (RDS in eu-west-1 only) — mitigated by Multi-AZ deployment; Phase 2 will evaluate cross-region replication

**Dependencies created:**
- AWS RDS provisioning by Company A infrastructure team (target: M0 + 1 week)
- Database migration tooling (Alembic for Python services) adopted by Company B
- Backup and restore testing procedure established before production deployment
