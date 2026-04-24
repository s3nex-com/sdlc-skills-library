---
name: observability-sre-practice
description: >
  Activate when designing or reviewing observability strategies, defining SLOs and error budgets,
  evaluating monitoring and alerting configurations, reviewing logging and tracing implementations,
  investigating production incidents through metrics and logs, designing on-call runbooks,
  assessing whether a service is production-ready from an operational perspective, defining
  DORA metrics collection, planning reliability engineering work, or evaluating partner company
  observability implementations against agreed NFRs. Use for everything from setting up the
  three pillars (metrics, logs, traces) to running error budget reviews and reliability
  retrospectives.
---

# Observability and SRE practice

## Purpose

Observability is the ability to understand what is happening inside a system by examining its external outputs. Without observability, production incidents are investigated by guesswork.

---

## When to use

- A new service is being built and the three pillars (metrics, logs, traces) need to be instrumented from day one
- SLOs need to be defined for a service before it goes to production
- Alerting needs to be configured — either from scratch or because existing alerts are noisy, non-actionable, or missing
- An on-call engineer is struggling to diagnose production issues due to insufficient observability
- An error budget review is due and the SLO status needs to be reported
- DORA metrics are needed at the service level (lead time, MTTR, deployment frequency)
- Production behaviour needs to be investigated and the existing telemetry needs to be evaluated for sufficiency

## When NOT to use

- Defining performance NFRs and running load/stress/soak tests against them — use `performance-reliability-engineering`.
- Running a postmortem and tracking corrective actions after an incident — use `incident-postmortem`.
- Designing fault-injection experiments to validate resilience — use `chaos-engineering`.
- Tracking DORA delivery metrics at the team level (lead time, change failure rate) — use `delivery-metrics-dora`.
- Writing runbooks and operational handover docs — use `documentation-system-design`.
- Cloud cost dashboards and budget alerts — use `cloud-cost-governance`.

---

## Process

### Instrumenting a new service

1. Add RED metrics (Rate, Errors, Duration) for every service entry point. Use the Prometheus counter + histogram pattern.
2. Add structured logging (JSON) with required fields: timestamp, level, service, trace_id, message. No sensitive data in logs.
3. Add OpenTelemetry trace instrumentation. Propagate W3C Trace Context headers. Instrument all outbound calls as spans.
4. Emit business metrics (events processed, users active, API calls per customer) — these are often as important as technical metrics.

### Defining SLOs

5. Identify the user-facing operations for the service. Each gets an availability SLO.
6. Write each SLO in the template format: metric, target percentage, window, success criteria, exclusions.
7. Compute the error budget: (1 - SLO target) × total request volume over the window.
8. Define the four error budget consumption thresholds and their corresponding team actions.
9. Write the Prometheus alert rule for SLO breach notification.

### Configuring alerts

10. For each alert, confirm it is actionable (what does the on-call engineer do?). Remove or convert to notification any alert that is not actionable.
11. For each alert, add a runbook URL to the annotation. The alert and the runbook are paired — one cannot exist without the other.
12. Apply the standard alert set for backend services as the baseline.

### SLO review

13. At the monthly review: run the SLO review report query, populate the report template, note error budget consumed, and identify any incidents.
14. Decide whether to adjust velocity based on error budget remaining.

### All sub-tasks

15. Append the execution log entry.

## The three pillars

### 1. Metrics

Metrics are numeric measurements of system behaviour over time. They answer "how much" and "how fast."

**What to instrument:**
- Request rate, error rate, and latency (the RED method: Rate, Errors, Duration)
- Resource utilisation (CPU, memory, disk, network)
- Queue depth and consumer lag (for async systems)
- Business metrics (events ingested, devices active, API calls per customer)
- Dependency health (database connection pool, upstream API latency)

**Prometheus metrics example:**

```go
// Define metrics at service initialisation
var (
    ingestRequests = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "edgeflow_ingest_requests_total",
        Help: "Total number of telemetry ingest requests by status",
    }, []string{"status", "device_type"})

    ingestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Name:    "edgeflow_ingest_duration_seconds",
        Help:    "Duration of telemetry ingest requests",
        Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5},
    }, []string{"device_type"})

    kafkaPublishLag = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "edgeflow_kafka_publish_lag_seconds",
        Help: "Time between event receipt and Kafka publish",
    })
)

// Record in handler
func (h *IngestionHandler) HandleEvent(ctx context.Context, req *IngestEventRequest) (*IngestEventResponse, error) {
    timer := prometheus.NewTimer(ingestDuration.WithLabelValues(req.DeviceType))
    defer timer.ObserveDuration()

    resp, err := h.service.Ingest(ctx, req)
    if err != nil {
        ingestRequests.WithLabelValues("error", req.DeviceType).Inc()
        return nil, err
    }

    ingestRequests.WithLabelValues("success", req.DeviceType).Inc()
    return resp, nil
}
```

### 2. Logs

Logs are timestamped records of discrete events. They answer "what happened" and "why."

**Structured logging requirements:**
- All logs must be structured (JSON), not free-form text
- Every log entry must include: `timestamp`, `level`, `service`, `trace_id`, `message`
- No sensitive data in log fields (no passwords, tokens, PII without masking)
- Log levels used consistently: ERROR (needs action), WARN (unusual but handled), INFO (normal operations), DEBUG (diagnostic, disabled in production)

```python
# Structured logging in Python with structlog
import structlog

logger = structlog.get_logger()

def ingest_event(device_id: str, event_type: str) -> str:
    log = logger.bind(device_id=device_id, event_type=event_type)

    log.info("ingest.started")

    try:
        event_id = _store_event(device_id, event_type)
        log.info("ingest.completed", event_id=event_id)
        return event_id
    except DeviceNotRegisteredError:
        log.warning("ingest.rejected", reason="device_not_registered")
        raise
    except Exception as e:
        log.error("ingest.failed", error=str(e), exc_info=True)
        raise
```

**Log retention policy:**
| Environment | Retention |
|-------------|-----------|
| Production | 90 days (hot) + 1 year (cold/archive) |
| Staging | 30 days |
| CI | 7 days |

### 3. Traces

Distributed traces follow a request across multiple services. They answer "where did the time go" in a distributed system.

**Instrumentation requirements:**
- All services must propagate the W3C Trace Context headers (`traceparent`, `tracestate`)
- Entry points (API gateways, queue consumers) generate a new trace ID if none present
- All outbound calls (HTTP, gRPC, database, queue publish) must be instrumented as spans
- Trace sampling rate: 100% in staging, 1% in production (adjust up during incidents)

```python
# OpenTelemetry trace instrumentation
from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Auto-instrument HTTP and database calls
RequestsInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument()

tracer = trace.get_tracer("ingestion-service")

def validate_device(device_id: str) -> bool:
    with tracer.start_as_current_span("validate_device") as span:
        span.set_attribute("device.id", device_id)
        result = device_registry.check_status(device_id)
        span.set_attribute("device.registered", result)
        return result
```

---

## SLOs and error budgets

### Defining SLOs

An SLO (Service Level Objective) is a target for service reliability expressed as a percentage of successful requests over a time window.

**SLO template:**

```
SLO: {Service} {Operation} availability
Metric: (successful requests / total requests) × 100%
Target: 99.9%
Window: 30 days rolling
Success criteria: HTTP status 2xx within 500ms p99
Exclusions: Planned maintenance windows (with 48 hours notice)
```

**Recommended SLOs for the telemetry platform:**

| SLO | Target | Measurement |
|-----|--------|-------------|
| Ingestion API availability | 99.9% | Requests with 2xx response |
| Ingestion latency p99 | 500ms | Histogram bucket at 500ms |
| Kafka publish lag | p95 < 5 seconds | Time from receipt to Kafka ack |
| Device registry call success | 99.5% | Successful validation responses |
| Event retrieval availability | 99.5% | Requests with 2xx response |

### Error budgets

Error budget = (1 - SLO target) × total request volume over the window.

For a 99.9% SLO over 30 days: the error budget is 0.1% of requests = ~43 minutes of full outage time (or proportionally more partial outage).

**Error budget consumption triggers:**

| Budget remaining | Action |
|-----------------|--------|
| > 50% | Normal operations. Reliability investment balanced with feature work. |
| 25–50% | Increase monitoring vigilance. Review change velocity. |
| 10–25% | Pause non-critical production changes. Prioritise reliability fixes. |
| < 10% | Freeze all production changes except reliability fixes. Incident review. |
| 0% | SLO breach. Escalation to engineering leads from both companies. RCA required. |

### Prometheus alert for SLO breach

```yaml
# Alert when 30-day error rate approaches SLO
groups:
  - name: slo.ingestion_api
    rules:
      - alert: IngestionAPIErrorBudgetBurning
        expr: |
          (
            1 - (
              sum(rate(edgeflow_ingest_requests_total{status="success"}[30d]))
              /
              sum(rate(edgeflow_ingest_requests_total[30d]))
            )
          ) > 0.001  # 0.1% = SLO breach threshold
        for: 5m
        labels:
          severity: critical
          service: ingestion-api
        annotations:
          summary: "Ingestion API SLO breach: error rate exceeds 0.1% over 30 days"
          runbook: "https://runbooks.edgeflow.example.com/ingestion-api-slo-breach"
```

---

## Alerting standards

### Alert quality principles

1. **Every alert must be actionable.** If the on-call engineer cannot do something specific in response, it is not an alert — it is a notification. Remove non-actionable alerts.
2. **Every alert must have a runbook.** The alert annotation must link to the runbook for that specific scenario.
3. **Alert on symptoms, not causes.** Alert on high error rate (what users experience), not "CPU > 80%" (which may or may not matter).
4. **Avoid alert storms.** When a root cause triggers 20 alerts, the on-call engineer is overwhelmed. Use alert aggregation and inhibition.

### Alert severity definitions

| Severity | Definition | Response SLA |
|----------|-----------|-------------|
| Critical / P1 | User-facing functionality broken; SLO breach in progress or imminent | Page on-call immediately; respond within 15 minutes |
| High / P2 | Degraded performance; error budget burning faster than planned | Notify on-call; respond within 1 hour |
| Warning / P3 | Anomaly that may lead to an issue; pre-emptive action recommended | Respond during business hours; resolve within 1 day |
| Info | Normal but noteworthy events (deployment completed, traffic spike handled) | No action required |

### Standard alert set for backend services

```yaml
# Required alerts for every production service
- HighErrorRate:
    condition: error_rate > 1% for 2 minutes
    severity: critical

- HighLatency:
    condition: p99_latency > 2s for 5 minutes
    severity: high

- PodCrashLooping:
    condition: pod_restart_count > 3 in 10 minutes
    severity: critical

- HighMemoryUsage:
    condition: memory_usage > 90% for 10 minutes
    severity: high

- DependencyUnreachable:
    condition: dependency_call_success_rate < 50% for 2 minutes
    severity: critical

- CertificateExpiringSoon:
    condition: certificate_expiry_days < 30
    severity: high

- KafkaConsumerLag:
    condition: consumer_lag > 100000 messages for 5 minutes
    severity: high
```

---

## DORA metrics

The four DORA (DevOps Research and Assessment) metrics measure delivery performance:

| Metric | Definition | Elite | High | Medium | Low |
|--------|-----------|-------|------|--------|-----|
| Deployment Frequency | How often code is deployed to production | Multiple times/day | Once/day to once/week | Once/week to once/month | Less than once/month |
| Lead Time for Changes | Time from commit to production | < 1 hour | 1 day to 1 week | 1 week to 1 month | > 1 month |
| Change Failure Rate | % of deployments causing production incident | < 5% | < 10% | 10–15% | > 15% |
| MTTR | Time to restore service after incident | < 1 hour | < 1 day | < 1 day | > 1 day |

### DORA metric collection queries

```sql
-- Deployment Frequency (deployments per day, last 30 days)
SELECT
  DATE(deployed_at) AS deploy_date,
  COUNT(*) AS deployments
FROM deployments
WHERE environment = 'production'
  AND deployed_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(deployed_at)
ORDER BY deploy_date;

-- Lead Time: average time from first commit in PR to production deploy
SELECT
  AVG(EXTRACT(EPOCH FROM (deployed_at - pr_first_commit_at)) / 3600) AS avg_lead_time_hours
FROM deployments d
JOIN pull_requests pr ON pr.merged_sha = d.commit_sha
WHERE d.environment = 'production'
  AND d.deployed_at > NOW() - INTERVAL '30 days';
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] observability-sre-practice — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] observability-sre-practice — SLO defined for ingestion API: p99 < 500ms, 99.9% availability
[2026-04-20] observability-sre-practice — Error budget burn rate at 60% — investigation triggered
[2026-04-20] observability-sre-practice — Monthly SLO review: all targets met
```

---

## Output format

### SLO review report

```
## SLO review: {Service name} — {Month}

**Review period:** {start} to {end}
**Attendees:** {names}

| SLO | Target | Actual | Error budget used | Status |
|-----|--------|--------|-------------------|--------|
| Ingestion API availability | 99.9% | 99.94% | 40% | ✅ On track |
| Ingestion p99 latency | 500ms | 387ms p99 | N/A | ✅ On track |
| Kafka publish lag p95 | < 5s | 1.2s | N/A | ✅ On track |

**Incidents this period:**
| Date | Duration | Impact | Budget consumed |
|------|----------|--------|----------------|
| 2024-01-08 | 23 min | 15% elevated error rate | 38% |

**Decisions:**
- Error budget in good shape; velocity maintained
- Next month: investigate p99 latency spike pattern on Monday mornings

**DORA metrics:**
| Metric | This month | Previous month | Target |
|--------|-----------|----------------|--------|
| Deployment frequency | 2.3/day | 1.8/day | ≥ 1/day |
| Lead time | 4.2 hours | 6.1 hours | < 8 hours |
| Change failure rate | 3.2% | 4.7% | < 5% |
| MTTR | 18 min | 31 min | < 60 min |
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for SLO definition templates, alert rule examples, on-call runbook starters, and error budget policy guides as they are developed.
