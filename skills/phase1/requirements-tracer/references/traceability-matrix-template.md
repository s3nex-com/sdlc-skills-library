# Requirements traceability matrix template

## Purpose

The traceability matrix links every requirement to its implementation (code modules) and verification (tests). It serves three purposes:
1. **Completeness** — ensure every requirement has been implemented and tested
2. **Orphan detection** — identify code and tests with no requirement, and requirements with no implementation
3. **Impact analysis** — when a requirement changes, identify all code and tests that must change

## Matrix format

| Req ID | Requirement summary | Epic | Feature | User Story | Code module(s) | Test ID(s) | Status | Owner |
|--------|-------------------|------|---------|-----------|----------------|------------|--------|-------|
| REQ-001 | Register a new device via the management API | EP-002 | EP-002-F01 | EP-002-F01-S01 | `services/device-registry/api/devices.py` | TC-001, TC-002, TC-003 | Implemented | TL-B |
| REQ-002 | Reject device registration with missing required fields | EP-002 | EP-002-F01 | EP-002-F01-S02 | `services/device-registry/api/devices.py`, `services/device-registry/validators.py` | TC-004, TC-005 | Implemented | TL-B |
| REQ-003 | Rate limit device registration to 100 req/min per API key | EP-002 | EP-002-F01 | EP-002-F01-S03 | `services/device-registry/middleware/rate_limiter.py` | TC-006 | In progress | TL-B |
| REQ-004 | Send registration confirmation event to Kafka | EP-002 | EP-002-F01 | EP-002-F01-S04 | `services/device-registry/events/publisher.py` | TC-007, TC-008, IT-001 | Planned | TL-B |
| REQ-005 | Ingest telemetry events at 50,000 events/sec | EP-003 | EP-003-F01 | EP-003-F01-S01 | `services/telemetry-ingestor/main.py`, `services/telemetry-ingestor/kafka_producer.py` | TC-010, TC-011, PT-001 | Implemented | TL-B |
| REQ-006 | Reject telemetry events with invalid device_id | EP-003 | EP-003-F01 | EP-003-F01-S02 | `services/telemetry-ingestor/validators.py` | TC-012, TC-013 | Implemented | TL-B |
| REQ-007 | Store processed events in TimescaleDB within 30 seconds | EP-003 | EP-003-F02 | EP-003-F02-S01 | `services/event-processor/storage/timescale.py` | IT-002, IT-003 | Implemented | TL-B |
| REQ-008 | Alert when device has not sent telemetry for 5 minutes | EP-004 | EP-004-F01 | EP-004-F01-S01 | `services/alert-engine/rules/staleness.py` | TC-020, IT-005 | Planned | TL-B |

## Status values

| Status | Meaning |
|--------|---------|
| **Planned** | Requirement agreed; not yet implemented |
| **In progress** | Implementation underway in current sprint |
| **Implemented** | Code complete; tests written |
| **Verified** | All tests passing in CI/CD |
| **Accepted** | Formally accepted by Company A |

## Test ID prefix conventions

| Prefix | Test type | Location |
|--------|-----------|---------|
| TC-NNN | Unit test | `tests/unit/` |
| IT-NNN | Integration test | `tests/integration/` |
| CT-NNN | Contract test (Pact) | `tests/contract/` |
| PT-NNN | Performance test | `tests/performance/` |
| E2E-NNN | End-to-end test | `tests/e2e/` |

## Traceability review checklist

Run before every milestone acceptance review:

- [ ] All requirements with status "Planned" or "In progress" have a completion sprint assigned
- [ ] All requirements in the milestone scope have status "Implemented" or "Verified"
- [ ] No requirements have zero test IDs linked (every requirement must have at least one test)
- [ ] `scripts/check_orphans.py` run and output reviewed — no unexplained orphans
- [ ] All orphaned code modules are either linked to requirements or removed
- [ ] Matrix updated in the same PR as the implementation code

**Last reviewed:** [date]
**Reviewed by:** [Name, Company A] + [Name, Company B]
