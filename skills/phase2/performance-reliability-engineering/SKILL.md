---
name: performance-reliability-engineering
description: >
  Activate when investigating performance problems, capacity planning, defining performance
  NFRs, reviewing load test results, designing auto-scaling strategies, analysing query
  performance, identifying bottlenecks in distributed systems, troubleshooting latency
  regressions, evaluating partner company performance test evidence, designing chaos
  engineering experiments, reviewing reliability patterns (circuit breakers, bulkheads,
  retries, timeouts), or determining whether a system meets its performance SLOs under
  realistic production load. Use for any work where response time, throughput, or
  system resilience under stress needs to be measured, designed, or improved.
---

# Performance and reliability engineering

## Purpose

Performance is a feature. A system that is functionally correct but too slow to be useful fails its users just as surely as a system that crashes. Performance NFRs must be explicitly agreed, measurably tested, and confirmed before each production release.

---

## When to use

- Performance NFRs need to be defined (response time, throughput targets) before implementation begins
- A load test needs to be written and run to verify the system meets its NFRs before a production release
- A latency regression has been identified and the root cause needs to be diagnosed
- Reliability patterns (circuit breaker, retry, timeout, bulkhead) need to be designed or reviewed for a service
- A stress test is needed to find the system's breaking point for capacity planning
- A soak test is needed to detect resource leaks (memory, connections, disk)
- Auto-scaling strategy needs to be designed and validated
- The user asks "does this meet the NFRs?", "why is it slow?", or "can it handle the load?"

## When NOT to use

- Fault-injection and resilience experimentation (failure modes, dependency blast radius) — use `chaos-engineering`.
- Defining SLOs, error budgets, and production alerting on performance signals — use `observability-sre-practice`.
- Functional unit and integration tests, test pyramid ratios — use `comprehensive-test-strategy`.
- BDD-style functional acceptance verification — use `executable-acceptance-verification`.
- Post-incident reviews after a performance-related outage — use `incident-postmortem`.
- Cost-of-compute or cloud spend optimisation tied to scaling decisions — use `cloud-cost-governance`.

---

## Process

### Defining NFRs

1. Identify every latency-sensitive or throughput-critical path in the system.
2. Write specific, measurable NFRs for each path using the format: metric, target (p50/p95/p99), environment, load profile, success criteria. Reject vague NFRs ("the system should be fast") — rewrite until they are testable.
3. Record NFRs in the PRD or design doc. They must be agreed before any test is run against them.

### Running performance tests

4. Start with the load test (steady state) — this is the pre-release gate. Configure thresholds in k6 that match the NFR targets.
5. Instrument the load test to capture all NFR metrics. A test that passes without evidence of the specific targets is not a pass.
6. Run the load test in the staging environment against the same build that will be deployed to production.
7. If the load test fails: diagnose the bottleneck (query plan, N+1, synchronous call to slow dependency, missing cache, undersized pool). Fix it and re-run. Do not ship with a failing load test.
8. If the goal is capacity planning (not a release gate): run the stress test to find the breaking point. Document the breaking load and the failure mode.
9. If checking for resource leaks: run the soak test at 70% of peak for at least 24 hours. Monitor memory, connections, and disk continuously.

### Reliability patterns

10. For every external dependency call: ensure a timeout is configured. No call can block indefinitely.
11. For every dependency where a slow or unavailable response would cascade into user-facing failure: implement a circuit breaker with defined failure threshold and recovery timeout.
12. For retry logic: implement exponential backoff with jitter. Define which errors are retryable (transient) and which are not (permanent).
13. Produce the performance test results summary in the output format.
14. Append the execution log entry.

## Performance NFR definition

Before testing can begin, NFRs must be specific and measurable. Vague NFRs cannot be tested.

**Vague:**
> The system should be fast and responsive.

**Specific:**
```
NFR-PERF-001: Ingestion API latency
  Metric: POST /v1/events response time
  Target: p50 < 100ms, p95 < 250ms, p99 < 500ms
  Measured at: staging environment, single availability zone
  Under load: 500 concurrent users, sustained for 10 minutes
  Success criteria: all three targets met with no more than 0.1% error rate

NFR-PERF-002: Ingestion throughput
  Metric: requests per second handled with < 1% error rate
  Target: ≥ 5,000 events/second at peak
  Measured at: staging environment
  Success criteria: target sustained for 5 minutes without degradation

NFR-PERF-003: Kafka publish lag
  Metric: time from event receipt (202 returned) to Kafka message available
  Target: p95 < 5 seconds
  Measured at: production (via Kafka consumer lag metrics)
```

---

## Performance test types

### Load test (steady state)

Verify the system meets NFRs under sustained expected load. The primary pre-release gate.

```javascript
// k6 — steady state load test
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const eventPublishLag = new Trend('kafka_publish_lag_ms');

export const options = {
  stages: [
    { duration: '2m', target: 100 },    // Warm up
    { duration: '10m', target: 500 },   // Sustained load at target
    { duration: '2m', target: 0 },      // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(50)<100', 'p(95)<250', 'p(99)<500'],
    'errors': ['rate<0.001'],  // < 0.1% error rate
    'http_req_failed': ['rate<0.001'],
  },
};

export default function () {
  const deviceId = `dev-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`;

  const res = http.post(
    `${__ENV.BASE_URL}/v1/events`,
    JSON.stringify({
      device_id: deviceId,
      event_type: 'temperature_reading',
      timestamp: new Date().toISOString(),
      payload: { temperature: (Math.random() * 50).toFixed(2) },
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': __ENV.API_KEY,
      },
    }
  );

  errorRate.add(res.status !== 202);
  check(res, {
    'status is 202': (r) => r.status === 202,
    'has event_id': (r) => r.json('event_id') !== undefined,
  });

  sleep(0.1); // 10 requests/second per VU
}
```

### Stress test (breaking point)

Find the system's breaking point. Not a release gate — used for capacity planning.

```javascript
export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '2m', target: 500 },
    { duration: '2m', target: 1000 },
    { duration: '2m', target: 2000 },
    { duration: '2m', target: 5000 },
    { duration: '5m', target: 5000 },  // Hold at stress level
    { duration: '2m', target: 0 },
  ],
  // No thresholds — we want to observe where things break
};
```

Monitor during stress test:
- At what load does error rate first exceed 1%?
- At what load does p99 exceed 1 second?
- Do errors recover when load decreases, or is there permanent degradation?
- Do any services crash (vs just slow down)?
- Does the system auto-scale successfully?

### Soak test (resource leak detection)

Run at 70% of peak load for 24–72 hours. Looking for:
- Memory leak (process memory grows continuously)
- Connection pool exhaustion (connections accumulate, not released)
- Disk fill (log or temp file accumulation)
- Performance degradation over time (latency slowly increases)

---

## Common performance anti-patterns

### N+1 query problem

```python
# BAD — N+1: one query for the list, then N queries for each item's details
devices = db.query("SELECT id FROM devices WHERE org_id = %s", (org_id,))
for device in devices:
    # Executes a query for every device in the list
    details = db.query("SELECT * FROM device_details WHERE device_id = %s", (device.id,))
    result.append({**device, **details})

# GOOD — single query with JOIN
devices = db.query("""
    SELECT d.*, dd.*
    FROM devices d
    LEFT JOIN device_details dd ON dd.device_id = d.id
    WHERE d.org_id = %s
""", (org_id,))
```

Detection: Enable slow query logging. Any query taking > 100ms in development is a candidate for investigation. Use `EXPLAIN ANALYZE` in PostgreSQL.

### Synchronous calls to slow dependencies

```python
# BAD — synchronous call to device registry on every ingest request
# If device registry is slow (100ms+), ingestion latency multiplies
def ingest(self, event: TelemetryEvent) -> str:
    # This blocks the entire request for the registry call latency
    if not self.device_registry.is_registered(event.device_id):
        raise DeviceNotRegisteredError()
    return self.store(event)

# BETTER — cached validation with TTL
def ingest(self, event: TelemetryEvent) -> str:
    cache_key = f"device:registered:{event.device_id}"
    if not self.cache.get(cache_key):
        registered = self.device_registry.is_registered(event.device_id)
        self.cache.set(cache_key, registered, ttl_seconds=300)  # 5-minute TTL
    if not self.cache.get(cache_key):
        raise DeviceNotRegisteredError()
    return self.store(event)
```

### Missing database indexes

```sql
-- Check for missing indexes causing full table scans
EXPLAIN ANALYZE
SELECT * FROM telemetry_events
WHERE device_id = 'dev-001'
AND timestamp >= '2024-01-01'
ORDER BY timestamp DESC
LIMIT 100;

-- If the plan shows "Seq Scan" on a large table, add an index:
CREATE INDEX CONCURRENTLY idx_telemetry_events_device_timestamp
ON telemetry_events(device_id, timestamp DESC);
```

---

## Reliability patterns

### Circuit breaker

Prevent cascading failures when a downstream dependency becomes unhealthy.

```python
# Using the circuitbreaker library
from circuitbreaker import circuit

@circuit(
    failure_threshold=5,      # Open after 5 consecutive failures
    recovery_timeout=30,      # Try recovery after 30 seconds
    expected_exception=DeviceRegistryError,
)
def validate_device(self, device_id: str) -> bool:
    return self.device_registry.is_registered(device_id)

# Handle open circuit gracefully
try:
    registered = self.validate_device(event.device_id)
except CircuitBreakerOpen:
    # Registry is unavailable — fail safe: reject the event
    # (better than accepting invalid events silently)
    logger.warning("Device registry circuit open; rejecting event for safety",
                   device_id=event.device_id)
    raise ServiceUnavailableError("Device validation temporarily unavailable")
```

### Retry with exponential backoff and jitter

```python
import random
import time
from functools import wraps

def retry_with_backoff(max_attempts=3, base_delay=0.1, max_delay=10.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (TransientError, ConnectionError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    # Exponential backoff with full jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay)
                    time.sleep(jitter)
            return None
        return wrapper
    return decorator

@retry_with_backoff(max_attempts=3, base_delay=0.2)
def publish_to_kafka(self, event: TelemetryEvent) -> None:
    self.producer.produce(topic="edgeflow.telemetry.events.v1", value=event.to_dict())
```

### Bulkhead

Isolate resource pools to prevent one component's overload from affecting others.

```python
# Separate thread pools for different operations
from concurrent.futures import ThreadPoolExecutor

class IngestionService:
    def __init__(self):
        # Each dependency gets its own bounded thread pool
        # If device registry is slow, it does not starve Kafka publish threads
        self._registry_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="registry")
        self._kafka_executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="kafka")
        self._db_executor = ThreadPoolExecutor(max_workers=15, thread_name_prefix="db")
```

### Timeout policy

```python
# Every external call must have a timeout
# No call should be able to block indefinitely

TIMEOUTS = {
    "device_registry": 500,    # ms — validation should be fast
    "kafka_produce": 5000,     # ms — allow for retry within timeout
    "database_write": 2000,    # ms — db write should be fast
    "database_read": 5000,     # ms — queries may be more expensive
}

async def validate_with_timeout(device_id: str) -> bool:
    async with asyncio.timeout(TIMEOUTS["device_registry"] / 1000):
        return await self.device_registry.is_registered(device_id)
```

---

## Capacity planning

### Capacity model

```
Input variables:
  - peak_events_per_second: 5,000 events/s
  - avg_payload_size_bytes: 512 bytes
  - p99_processing_time_ms: 500 ms
  - slo_availability: 99.9%

Derived:
  - peak_bandwidth_inbound: 5,000 × 512 = 2.5 MB/s (nominal)
  - kafka_bandwidth: × 3 (replication factor) = 7.5 MB/s
  - db_write_throughput: 5,000 rows/s

Pod sizing (ingestion service):
  - Concurrency per pod: 100 requests
  - At 500ms p99: 100 / 0.5s = 200 req/s per pod
  - For 5,000 req/s: 25 pods minimum
  - With 25% headroom: 32 pods (32 × 200 = 6,400 req/s capacity)

Auto-scaling:
  - Min replicas: 10 (handles ~2,000 req/s; provides headroom during scale-out)
  - Max replicas: 64 (handles ~12,800 req/s; 2.5× peak)
  - Scale-up trigger: CPU > 60% OR request queue > 50ms
  - Scale-down delay: 5 minutes (prevent flapping)
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] performance-reliability-engineering — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] performance-reliability-engineering — Load test run: ingestion API meets p99 < 500ms at 1000 RPS
[2026-04-20] performance-reliability-engineering — Circuit breaker implemented for device-registry client
[2026-04-20] performance-reliability-engineering — Latency regression diagnosed: N+1 query in event lookup
```

---

## Output format

### Performance test results summary

```
## Performance test results: {Service name} — {Date}

**Test type:** Load | Stress | Soak | Spike
**Environment:** {URL}
**Duration:** {total}
**Peak VUs:** {number}

### NFR compliance
| NFR | Target | Actual | Status |
|-----|--------|--------|--------|
| p50 latency | < 100ms | 72ms | ✅ PASS |
| p95 latency | < 250ms | 187ms | ✅ PASS |
| p99 latency | < 500ms | 412ms | ✅ PASS |
| Error rate | < 0.1% | 0.03% | ✅ PASS |
| Throughput | ≥ 5,000 req/s | 6,240 req/s | ✅ PASS |

**Overall result:** PASS — all NFRs met

### Observations
- P99 latency spikes to 380ms during auto-scaling events (pods spinning up)
- Database connection pool saturated at 4,800 req/s; increased pool size from 50 to 80

### Recommendations
- [ ] Investigate p99 spike during scale-out; consider pre-warming pods
- [ ] Monitor connection pool utilisation in production; current headroom is thin
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for k6 load test templates, NFR definition worksheets, circuit-breaker configuration examples, and capacity planning spreadsheets as they are developed.
