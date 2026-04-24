---
name: chaos-engineering
description: >
  Activate when you need to validate that circuit breakers, retries, and fallbacks
  actually work under real failure conditions — not just in unit tests. Use after go-live
  to run quarterly chaos experiments against production-like environments, inject faults
  in CI to catch resilience regressions, or run a game day to rehearse incident response.
  Triggers: "do our circuit breakers actually work?", "what happens when the database is slow?",
  "prove the system handles a pod failure gracefully", "quarterly resilience check".
---

# Chaos engineering

## Purpose

Resilience patterns (circuit breakers, retries, bulkheads, fallbacks) are commonly implemented but rarely validated end-to-end under realistic failure conditions. A circuit breaker that never opens under a real dependency outage is worse than no circuit breaker — it creates false confidence. Chaos engineering is the practice of making failure hypotheses explicit, injecting failures deliberately in a controlled scope, and measuring whether the system's actual behaviour matches the hypothesis. This skill covers three related practices: automated chaos experiments (run in CI or staging), game days (quarterly rehearsed incident response), and steady-state monitoring (knowing what "normal" looks like before injecting anything). All three are operational skills — they belong post-go-live, run on a regular cadence, and feed action items back into the backlog.

---

## When to use

- **Post-go-live resilience validation**: The service is live and you want evidence that the resilience patterns you implemented actually hold under failure
- **Before a major launch**: Run the standard experiment catalogue in staging to catch resilience gaps before they become incidents
- **Quarterly cadence**: Scheduled resilience checks — the system evolves and circuit breakers break silently as dependencies change
- **Fault injection in CI**: Gate on resilience — run dependency-outage tests as part of the pipeline to catch regressions
- **Game day**: The team needs to rehearse incident response against a realistic failure scenario; runbooks need verification

---

## When NOT to use

- **Designing a new distributed protocol** — verify the design correctness with TLA+ first (`phase4/formal-verification`). Chaos tests probe operational resilience, not protocol correctness
- **Performance and load testing** — use `performance-reliability-engineering`. Chaos is about failure modes, not capacity
- **Unit and integration testing of resilience code** — use `comprehensive-test-strategy`. Chaos tests validate that the assembled system behaves correctly under failure, not that individual functions have the right logic
- **Pre-implementation validation** — chaos engineering has nothing to run against. It requires a deployed system
- **Debugging a specific known failure** — chaos is for hypothesis-driven discovery. If you already know what is broken, fix it directly

---

## Process

### 1. Define steady state (before every experiment)

Steady state is what "normal" looks like for this service. Measure it before injecting anything.

```
Service: ingestion-service
Steady state:
  - Error rate: < 0.1%
  - p99 latency: < 500ms
  - Kafka consumer lag: < 1,000 messages
  - Circuit breaker state: closed
```

If you do not have dashboards for these metrics, get them in place before running experiments. Running chaos without observability is just breaking things.

### 2. Write the hypothesis

One sentence. Falsifiable. Specifies the failure condition and the expected behaviour.

> "We hypothesise that when the device registry returns 503 for all requests, the ingestion service will reject new events within 500ms (circuit breaker opens) and Kafka consumer lag will not increase beyond 5,000 messages."

If you cannot write the hypothesis in one sentence, the experiment scope is too wide.

### 3. Scope the experiment

Start narrow. Single pod, not all pods. One dependency, not all dependencies. Short duration (2–5 minutes). Expand scope only after confirming the hypothesis holds at smaller scale.

### 4. Define abort conditions

Pre-define what stops the experiment immediately:
- Error rate exceeds X (unexpected escalation)
- Data loss detected
- Kafka consumer lag exceeds Y (unexpected queue backup)
- Any signal that the failure is spreading beyond the intended scope

Write these down before starting. Do not invent them mid-experiment when things are getting interesting.

### 5. Run the experiment

Inject the failure. Monitor the metrics. One person injects; at least one person watches the dashboards in real time. Keep the duration short.

### 6. Observe and record

Did steady state hold? Did the circuit breaker behave as expected? What was the actual recovery time? Record the result against the hypothesis — pass, fail, or unexpected finding.

### 7. Create action items for failures

Every failed hypothesis generates a ticket. Owner and sprint assigned before the session closes. Re-run the experiment after the fix is in.

---

## Standard experiment catalogue

Run these five experiments quarterly. Add custom experiments only for novel failure modes specific to your system.

### Experiment 1: Dependency outage (circuit breaker validation)

**Failure:** Key upstream dependency returns 503 for all requests for 5 minutes
**Tool:** Toxiproxy (non-Kubernetes) or Istio fault injection (Kubernetes)

```bash
# Toxiproxy: inject 100% error rate on device registry calls
toxiproxy-cli toxic add --type http_error --attribute status_code=503 \
  --upstream "device-registry-proxy" --name "registry-outage"

# Monitor for 5 minutes
sleep 300

# Remove the fault
toxiproxy-cli toxic delete --toxicName "registry-outage" "device-registry-proxy"
```

**Hypothesis confirmed if:** Circuit opens after 5 failures; subsequent requests fail fast (< 500ms); on recovery circuit closes within 30 seconds; error rate returns to < 0.1%.

### Experiment 2: Database slow query (bulkhead validation)

**Failure:** Inject 5-second latency on all database queries
**Tool:** Istio `VirtualService` fault injection

```yaml
# Apply to staging cluster
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: postgres-delay-injection
spec:
  hosts:
    - postgres.svc.cluster.local
  http:
    - fault:
        delay:
          percentage:
            value: 100
          fixedDelay: 5s
      route:
        - destination:
            host: postgres.svc.cluster.local
```

**Hypothesis confirmed if:** Requests requiring DB queries fail fast (bulkhead exhausted); requests not requiring DB are unaffected; connection pool does not exhaust for unrelated workloads.

### Experiment 3: Pod failure (rolling restart resilience)

**Failure:** Delete one pod every 30 seconds for 5 minutes
**Tool:** `kubectl delete pod` or kube-monkey

```bash
for i in {1..10}; do
  POD=$(kubectl get pods -n edgeflow -l app=ingestion-service \
    -o jsonpath='{.items[0].metadata.name}')
  kubectl delete pod "$POD" -n edgeflow
  sleep 30
done
```

**Hypothesis confirmed if:** Error rate remains < 1% during rolling deletion; no data loss; Kubernetes replaces pods within 30 seconds.

### Experiment 4: Kafka partition leader election

**Failure:** Kill the lead broker for the target topic partition
**Tool:** Managed Kafka admin API or direct broker restart

**Hypothesis confirmed if:** Producer retries and recovers within 30 seconds; zero message loss; consumer lag recovers to baseline within 2 minutes.

### Experiment 5: Network partition (split-brain prevention)

**Failure:** Block network traffic between availability zones for 2 minutes
**Tool:** `iptables` rules or cloud security group changes (revert immediately after)

**Hypothesis confirmed if:** Each zone serves requests independently during the partition; no data corruption; reconciliation completes within 5 minutes of reconnection with no duplicates or gaps.

---

## Game day format

Run one game day per quarter. Pick the failure scenario the team is least confident about. Two to three hours total.

1. **Pick the scenario** (30 min before the day): the failure you are least prepared for. Good candidates: primary database failover, key dependency complete outage, certificate expiry, cascading retry storm.
2. **Define success criteria**: what does "good incident response" look like? (Service restored within MTTR target; runbook was accurate; no data loss; all steps were clear.)
3. **Inject the failure**: one person plays incident injector; the rest respond as if it were a real incident. No hints. Use real runbooks.
4. **Debrief** (30 minutes after): what worked, where did the runbook fail, what was ambiguous, where did communication break down. One action item per gap. Assign owner and sprint before the room clears.

Suggested quarterly rotation:

| Quarter | Scenario | Why |
|---------|----------|-----|
| Q1 | Primary database failover | Tests failover procedure and data consistency |
| Q2 | Key upstream dependency outage | Validates circuit breakers and degraded-mode behaviour |
| Q3 | Certificate expiry (simulate TLS failure) | Cheap to run; surprisingly common real cause |
| Q4 | Cascading retry storm | Tests backpressure and rate limiting under overload |

---

## Output format with real examples

### Chaos experiment record

```markdown
## Chaos experiment: Device registry outage — 2026-04-20

**Hypothesis:** The ingestion service will reject new device events within 500ms
and Kafka consumer lag will not exceed 5,000 messages when the device registry
returns 503 for all requests for 5 minutes.

**Steady state (measured before experiment):**
- Error rate: 0.04%
- p99 latency: 312ms
- Kafka consumer lag: 220 messages
- Circuit breaker: closed

**Failure condition:** Device registry → 100% 503 via Toxiproxy for 5 minutes

**Scope:** Staging; 100% of device registry calls from ingestion-service

**Duration:** 5 minutes

**Metrics monitored:**
- Ingestion error rate
- Ingestion p99 latency
- Kafka consumer lag
- Circuit breaker state

**Abort conditions:**
- Error rate > 5%
- Kafka lag > 50,000 messages
- Any data loss detected

**Expected outcome:**
- Circuit opens within 5 failures (< 5s)
- Fail-fast responses < 500ms
- Kafka lag stable (events rejected, not queued)
- Recovery: circuit closes within 30s of registry restoration

**Result:** Pass

**Observations:**
- Circuit opened after 4 failures (3.8s)
- Fail-fast p99: 48ms (well under 500ms)
- Kafka lag peak: 340 messages (baseline noise)
- Recovery: circuit closed 22s after Toxiproxy toxic removed

**Action items:** None — hypothesis confirmed.
```

### Quarterly experiment results summary

```
## Chaos experiment results: Q2 2026

Period: 2026-04-01 to 2026-04-20
Experiments run: 5

| Experiment            | Target              | Confirmed? | Finding                              |
|-----------------------|---------------------|------------|--------------------------------------|
| Device registry 503   | Circuit breaker     | Yes        | Opened in 3.8s; recovered in 22s     |
| DB slow query (5s)    | Bulkhead            | No         | Pool exhausted at 3s — TDB-017 filed |
| Pod failure (rolling) | Deployment          | Yes        | < 0.05% errors during deletion       |
| Kafka leader election | Producer retry      | Yes        | 18s recovery; 0 messages lost        |
| Network partition     | Split-brain         | Yes        | Clean reconciliation; 0 duplicates   |

System resilience score: 4/5 hypotheses confirmed.

Action items:
- TDB-017: Add connection pool bulkhead for DB calls — Alice — Sprint 14
- Rerun DB slow query experiment after TDB-017 merges
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] chaos-engineering — [one-line description]
```

Example entries:
```
[2026-04-20] chaos-engineering — Ran 5-experiment catalogue in staging; 4/5 hypotheses confirmed; TDB-017 filed
[2026-04-20] chaos-engineering — Game day: primary database failover; runbook step 4 was ambiguous; updated
[2026-04-20] chaos-engineering — Added pod-failure fault injection to CI pipeline for ingestion-service
```

---

## Reference files

`references/chaos-experiment-template.md` contains:
- Blank experiment template with all required fields
- Abort condition guidance by failure type
- Toxiproxy command reference
- Istio fault injection YAML templates
- Kafka partition manipulation commands
- Game day debrief question set
