# Architecture decision records index

All architecture decisions for this project are recorded here. Each ADR captures what was decided, why, what alternatives were considered, and what the consequences are.

**Location:** `docs/adr/`
**Naming convention:** `ADR-NNN-short-title-in-kebab-case.md`

---

## How to navigate this index

- **Status column:** Filter by `Accepted` to see active decisions. `Superseded` decisions are kept for historical context — check the "Superseded by" column to find the current decision.
- **Domain column:** Filter by domain to find all decisions in a specific area (e.g., all Security decisions, all Data decisions).
- **Cross-reference:** ADRs often reference each other. When reading an ADR, check whether it has been superseded.

---

## ADR index

| ADR # | Title | Status | Date | Domain | Supersedes | Superseded by |
|-------|-------|--------|------|--------|-----------|---------------|
| [ADR-001](ADR-001-use-opentelemetry-for-observability.md) | Use OpenTelemetry for observability instrumentation | Accepted | 2024-03-01 | Observability | — | — |
| [ADR-002](ADR-002-kafka-over-rabbitmq-for-event-streaming.md) | Use Apache Kafka for event streaming | Accepted | 2024-03-08 | Messaging | — | — |
| [ADR-003](ADR-003-contract-first-development-with-openapi.md) | Adopt contract-first development with OpenAPI 3.x | Accepted | 2024-03-08 | API design | — | — |
| [ADR-004](ADR-004-use-postgresql-as-primary-data-store.md) | Use PostgreSQL as the primary relational data store | Accepted | 2024-03-10 | Data | — | — |
| [ADR-005](ADR-005-hashicorp-vault-for-secrets-management.md) | Use HashiCorp Vault for all secrets management | Accepted | 2024-03-12 | Security | — | — |
| [ADR-006](ADR-006-timescaledb-for-telemetry-time-series.md) | Use TimescaleDB for telemetry time-series storage | Accepted | 2024-03-15 | Data | — | — |
| [ADR-007](ADR-007-asyncio-based-ingestion-service.md) | Use Python asyncio for the ingestion service | Accepted | 2024-03-20 | Architecture | — | — |
| [ADR-008](ADR-008-circuit-breaker-with-resilience4j.md) | Implement circuit breakers using Resilience4j | Accepted | 2024-04-02 | Resilience | — | — |

---

## ADR status definitions

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion — decision not yet finalised |
| **Accepted** | Decision finalised and in effect |
| **Deprecated** | Decision is no longer valid but has not been replaced by a specific new decision |
| **Superseded** | Decision has been replaced by a newer ADR |

---

## ADR domains

| Domain | Description |
|--------|-------------|
| Architecture | Service decomposition, system structure, component boundaries |
| API design | Interface contracts, protocols, versioning |
| Data | Data stores, schemas, ownership, retention |
| Messaging | Message brokers, event patterns, async communication |
| Security | Authentication, authorisation, encryption, secrets |
| Observability | Logging, metrics, tracing, alerting |
| Resilience | Fault tolerance, circuit breakers, retry patterns |
| Infrastructure | Deployment, cloud services, hosting |
| Process | Development process, tooling, workflow |

---

## Adding a new ADR

1. Assign the next sequential number
2. Create the file: `ADR-NNN-descriptive-title.md` using `adr-template.md`
3. Add an entry to this index
4. If the new ADR supersedes an existing one, update the old ADR's status and the index row's "Superseded by" column
5. Commit both the new ADR file and the updated index in the same commit
6. Notify the Lead Architect (Company A) that a new ADR has been created

**Last updated:** [date]
**Total ADRs:** 8 | **Accepted:** 8 | **Superseded:** 0 | **Proposed:** 0
