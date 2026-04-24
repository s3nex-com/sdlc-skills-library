# Threat modelling guide

## When to run a threat model

Run a threat model whenever:
- A new service or component is being designed
- A new external integration is being added (partner API, third-party SaaS)
- A new data flow crosses a trust boundary
- An existing service is modified to handle a new data classification (e.g., now handles PII)
- A significant architecture change is proposed (new data store, changed auth mechanism)
- A penetration test finding identifies a gap in the threat model

---

## DFD notation

Use a standard data flow diagram with these elements:

| Symbol | Name | Description |
|--------|------|-------------|
| Rectangle | External entity | Actor or system outside the trust boundary (mobile app, partner API, human user) |
| Rounded rectangle | Process | Software component that processes data (API service, worker, batch job) |
| Open-ended rectangle | Data store | Persistent storage (database, cache, object storage, message queue) |
| Arrow | Data flow | Data moving between elements. Label with protocol and data type. |
| Dashed line | Trust boundary | Boundary between zones of different trust levels |

### Trust boundary zones (typical)

```
[Internet / External Zone]
    │  (HTTPS/mTLS)
    ▼
[DMZ / Edge Zone]         ← API gateway, load balancer
    │  (internal HTTP/gRPC)
    ▼
[Application Zone]        ← Microservices, workers
    │  (internal protocols)
    ▼
[Data Zone]               ← Databases, caches, message queues
    │
    ▼
[Management Zone]         ← Secrets manager, observability, CI/CD
```

---

## Worked example: Telemetry ingestion API

### System description

Company B's edge devices send telemetry events to Company A's ingestion API. Events are validated, enriched, and published to a Kafka topic for downstream consumers.

### Data flow diagram (Mermaid)

```
graph TD
    ED[Edge Device\nExternal Entity]
    AG[API Gateway\nProcess]
    IS[Ingestion Service\nProcess]
    DB[(Event Store\nPostgreSQL)]
    KA[(Kafka Topic\nedgeflow.telemetry.events.v1)]
    SM[Secrets Manager\nHashiCorp Vault]
    OBS[Observability Platform\nPrometheus + Loki]

    ED -->|HTTPS POST /events\nTLS 1.3, API key auth| AG
    AG -->|gRPC IngestEvent\nmTLS| IS
    IS -->|INSERT\nTLS + credential from Vault| DB
    IS -->|Publish\nSASL/SCRAM-SHA-512| KA
    IS -->|Read DB creds at startup| SM
    IS -->|Metrics + logs| OBS

    style ED fill:#ffcccc
    style AG fill:#ffe0b2
    style IS fill:#e8f5e9
    style DB fill:#e3f2fd
    style KA fill:#e3f2fd
    style SM fill:#f3e5f5
```

Trust boundaries:
- Between Edge Device and API Gateway: **Internet boundary**
- Between API Gateway and Ingestion Service: **DMZ to Application boundary**
- Between Ingestion Service and Data Zone: **Application to Data boundary**

### Threat inventory

| ID | Element | Threat | STRIDE | Description | P | I | Score | Mitigation | Status |
|----|---------|--------|--------|-------------|---|---|-------|------------|--------|
| T-001 | Edge Device → API Gateway | Spoofing | S | Attacker sends forged requests pretending to be a registered device | 4 | 5 | 20 | Per-device API keys; key rotation every 90 days; device registry validation on every request | Mitigated |
| T-002 | API Gateway | Tampering | T | Attacker intercepts and modifies telemetry payload in transit | 2 | 4 | 8 | TLS 1.3 enforced end-to-end; HSTS; reject non-TLS connections at gateway | Mitigated |
| T-003 | Ingestion Service | Elevation of privilege | E | Compromised service account gains access to other services' data stores | 2 | 5 | 10 | Each service has a dedicated database credential with access only to its own schema; Vault dynamic secrets with short TTL | Mitigated |
| T-004 | Event Store | Information disclosure | I | Unauthorised read of telemetry data by internal actors or compromised service | 3 | 4 | 12 | Row-level security on organisation_id; read-only replica for reporting services; all access logged | Mitigated |
| T-005 | API Gateway | Denial of service | D | High-volume request flood from compromised device fleet | 4 | 4 | 16 | Rate limiting per API key (1000 req/s); per-IP rate limiting (100 req/s); circuit breaker; auto-scaling | Mitigated |
| T-006 | Kafka Topic | Tampering | T | Malicious message injected into topic to corrupt downstream consumers | 2 | 5 | 10 | Only ingestion service has produce permissions; schema validation on consume; SASL/SCRAM auth | Mitigated |
| T-007 | Ingestion Service | Repudiation | R | No record of which device submitted which event | 3 | 3 | 9 | event_id assigned server-side; device_id logged in structured log on every ingest; immutable audit log | Mitigated |
| T-008 | Secrets Manager | Tampering | T | Rotation failure leaves expired credentials in production | 2 | 5 | 10 | Vault lease monitoring; alerting on credential age > 80% of TTL; automated rotation tested quarterly | Mitigated |
| T-009 | API Gateway | Information disclosure | I | Error responses leak internal service names or stack traces | 3 | 2 | 6 | Generic error envelope returned to clients; full error logged internally only; API contract specifies error format | Mitigated |
| T-010 | Edge Device | Spoofing | S | Device impersonation after key theft from device firmware | 3 | 5 | 15 | Device key stored in secure enclave (hardware requirement); anomaly detection on event volume per device; key revocation API | Partially mitigated |

### Residual risks

| Threat ID | Score | Residual description | Rationale for acceptance | Accepted by | Review date |
|-----------|-------|---------------------|--------------------------|-------------|-------------|
| T-010 | 15 | Device key theft from hardware without secure enclave | Not all device SKUs support secure enclave. Anomaly detection reduces impact. Hardware refresh roadmap Q3. | Alice Chen (Company A CTO), Bob Martin (Company B VP Eng) | 2025-09-01 |

---

## Worked example: Partner API integration

### System description

Company A's platform calls Company B's Device Registry REST API to validate device registration status before accepting telemetry.

### Threat inventory (abbreviated)

| ID | Element | Threat | STRIDE | Description | P | I | Score | Mitigation | Status |
|----|---------|--------|--------|-------------|---|---|-------|------------|--------|
| T-011 | Outbound call to Partner API | Spoofing | S | DNS hijack redirects calls to malicious server | 2 | 5 | 10 | Certificate pinning for partner endpoint; mutual TLS; verify server certificate against expected CA | Mitigated |
| T-012 | Partner API response | Tampering | T | Response modified in transit to incorrectly validate invalid devices | 2 | 5 | 10 | mTLS with certificate validation; response body HMAC where partner supports it | Mitigated |
| T-013 | Partner API | Denial of service | D | Partner API outage causes cascading failure in ingestion service | 3 | 4 | 12 | Circuit breaker with fallback to cached device list (TTL 5 min); retry with exponential backoff | Mitigated |
| T-014 | Cached device list | Information disclosure | I | Cache contains device metadata visible to other services | 2 | 3 | 6 | Cache scoped to ingestion service; Redis AUTH; cache entries contain only device_id + validation status | Mitigated |

---

## Threat model review checklist

Before presenting a threat model for sign-off:

- [ ] All external entities are identified and named
- [ ] All trust boundaries are drawn and labelled
- [ ] Every data flow crossing a trust boundary has a threat entry
- [ ] All data stores have threat entries
- [ ] All STRIDE categories considered for every process element
- [ ] All threats scored with Probability × Impact
- [ ] Every threat with score ≥ 9 has a documented mitigation
- [ ] Mitigations are verifiable (not "we will add security")
- [ ] Residual risks (score ≥ 9 without full mitigation) are explicitly listed
- [ ] Residual risks are accepted in writing by both companies' engineering leads
- [ ] Threat model stored in version control alongside the architecture document
