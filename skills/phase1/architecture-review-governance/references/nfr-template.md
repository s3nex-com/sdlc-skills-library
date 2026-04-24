# Non-functional requirements template

## Purpose

Non-functional requirements (NFRs) define HOW the system behaves under load, stress, and failure — not what it does. They are the most frequently underspecified requirements and the most catastrophically discovered in production. Every NFR must be specific, measurable, and tied to an acceptance test before development begins.

**Rule:** If you cannot write an automated test that passes or fails based on the NFR, the NFR is not specific enough.

---

## NFR specification format

For each NFR:

| Field | Description |
|-------|-------------|
| **ID** | NFR-NNN |
| **Category** | Latency / Throughput / Availability / Reliability / Security / Scalability / Maintainability |
| **Component** | Which service, API, or system component this applies to |
| **User journey or operation** | The specific operation being measured |
| **Metric** | What is being measured (p50 latency, requests/sec, uptime %) |
| **Target** | The measurable target value |
| **Measurement method** | How this is measured (load test, monitoring, unit test) |
| **Load condition** | What traffic level this target must be met under |
| **Acceptance test** | The specific test or verification method that proves compliance |
| **Priority** | Critical / High / Medium |

---

## Worked examples

---

**NFR-001**
**Category:** Latency
**Component:** Telemetry Ingestion API (`POST /v1/telemetry/events`)
**User journey:** Single device submitting a telemetry event batch
**Metric:** HTTP response time (p99)
**Target:** ≤ 500ms
**Measurement method:** Load test with k6 at the specified load condition
**Load condition:** 1,000 concurrent device connections, sustained for 10 minutes
**Acceptance test:** k6 load test passes with p99 latency < 500ms, 0% error rate, sustained for 10 minutes at 1,000 concurrent connections
**Priority:** Critical

---

**NFR-002**
**Category:** Latency
**Component:** Telemetry Ingestion API (`POST /v1/telemetry/events`)
**User journey:** Single device submitting a telemetry event batch
**Metric:** HTTP response time (p50)
**Target:** ≤ 100ms
**Measurement method:** Load test with k6
**Load condition:** Normal load (500 concurrent connections)
**Acceptance test:** k6 load test at 500 concurrent connections shows p50 latency < 100ms
**Priority:** High

---

**NFR-003**
**Category:** Throughput
**Component:** Telemetry Ingestion API
**User journey:** Peak event ingestion
**Metric:** Events processed per second (sustained)
**Target:** ≥ 50,000 events/second
**Measurement method:** Load test with a 10-second sustained burst at target throughput
**Load condition:** Peak traffic simulation
**Acceptance test:** Load test achieving 50,000 events/second shows 0% error rate and all events durably stored in Kafka within 5 seconds
**Priority:** Critical

---

**NFR-004**
**Category:** Availability
**Component:** Telemetry Ingestion API (production)
**User journey:** All ingestion requests
**Metric:** Service availability (successful responses / total requests)
**Target:** ≥ 99.9% over any 30-day rolling window
**Measurement method:** Uptime monitoring (Prometheus/Grafana SLO dashboard)
**Load condition:** Normal production load
**Acceptance test:** SLO compliance report shows ≥ 99.9% availability over the 30-day post-launch period. Error budget consumed ≤ 100% in any 30-day window.
**Priority:** Critical

---

**NFR-005**
**Category:** Reliability
**Component:** Telemetry pipeline (Kafka → processing → storage)
**User journey:** Event from ingestion to persistent storage
**Metric:** End-to-end event processing lag (event ingestion timestamp to storage write timestamp)
**Target:** ≤ 30 seconds at p99 under normal load
**Measurement method:** Events include ingestion timestamp; storage records write timestamp; lag calculated from Kafka consumer group lag metrics
**Load condition:** Normal load (10,000 events/second sustained)
**Acceptance test:** During a 30-minute sustained load test, consumer lag metric p99 stays below 30 seconds with no message loss
**Priority:** High

---

**NFR-006**
**Category:** Availability — Recovery
**Component:** Telemetry Ingestion API
**User journey:** Service restart after crash
**Metric:** Recovery time objective (RTO) — time from crash to accepting traffic
**Target:** ≤ 60 seconds
**Measurement method:** Chaos test — kill the service process; measure time until health check passes and load balancer routes traffic
**Load condition:** Kubernetes pod restart (not a node failure)
**Acceptance test:** Chaos test (kill pod) shows service healthy and accepting traffic within 60 seconds in 5 consecutive test runs
**Priority:** High

---

**NFR-007**
**Category:** Reliability — Data durability
**Component:** Telemetry storage layer (TimescaleDB)
**User journey:** Events written during a primary database failure
**Metric:** Recovery point objective (RPO) — maximum data loss during a primary failure
**Target:** ≤ 5 minutes of data loss
**Measurement method:** Chaos test — simulate primary database failure; measure data loss from last replication checkpoint to failover
**Load condition:** Normal write load
**Acceptance test:** Chaos test shows replica lag ≤ 5 minutes under normal load in 3 consecutive tests. Failover to replica completes within 2 minutes.
**Priority:** High

---

**NFR-008**
**Category:** Scalability
**Component:** Telemetry Ingestion API
**User journey:** Horizontal scaling under load growth
**Metric:** Linear throughput scaling (doubling pods doubles throughput)
**Target:** ≥ 80% scaling efficiency (2 pods = 1.6× throughput of 1 pod)
**Measurement method:** Measure throughput at 1, 2, 4 pods under identical load; calculate efficiency ratio
**Load condition:** Each pod at ~80% CPU utilisation
**Acceptance test:** Scaling test shows ≥ 80% efficiency at 2× and 4× pod count vs single-pod baseline
**Priority:** Medium

---

## NFR coverage checklist

Before milestone acceptance, verify that NFRs are defined for:
- [ ] All user-facing API latency targets (p50, p99)
- [ ] Peak throughput target
- [ ] Availability target (monthly uptime %)
- [ ] Recovery time objective (RTO) for service restart
- [ ] Recovery point objective (RPO) for data durability
- [ ] Data processing lag (if applicable)
- [ ] Horizontal scaling efficiency
- [ ] Maximum acceptable error rate under load

Every NFR must have an acceptance test before development of the relevant component begins.
