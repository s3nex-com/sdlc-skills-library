# Chaos experiment template and reference

## Blank experiment template

Copy this for every new experiment. Fill in all fields before injecting anything.

```markdown
## Chaos experiment: {Name} — {Date}

**Hypothesis:** The {service} will {maintain steady state behaviour} when {failure condition}
for {duration}.

**Steady state (measure before starting):**
- Error rate: {current value}
- p99 latency: {current value}
- {Key business metric}: {current value}
- {Queue/lag metric}: {current value}

**Failure condition:** {Precise description of what will be injected}

**Scope:** {Environment; percentage of traffic or pods affected}

**Duration:** {How long the failure is maintained}

**Metrics to monitor during experiment:**
- {Metric 1}
- {Metric 2}
- {Metric 3}

**Abort conditions (stop immediately if):**
- Error rate > {X}%
- {Queue/lag} > {Y} messages
- Any data loss detected
- {Other unexpected condition}

**Expected outcome:**
- {Specific observable behaviour 1}
- {Specific observable behaviour 2}
- On failure removal: {recovery behaviour with timing}

**Result:** Pass / Fail / Unexpected

**Observations:** {What actually happened, with metrics}

**Action items:** {Ticket ID and owner for each failed hypothesis element}
```

---

## Abort condition guidance by failure type

| Failure type | Typical abort conditions |
|--------------|--------------------------|
| Dependency outage | Error rate > 5%; queue lag > 10× baseline |
| Database latency | Connection pool exhausted; unrelated requests degraded |
| Pod deletion | Error rate > 2%; pod replacement > 2 minutes |
| Kafka broker | Message loss detected; lag > 100,000 messages |
| Network partition | Data corruption detected; split-brain state observed |

Always add one custom abort condition specific to the business context (e.g., "any payment transaction fails").

---

## Tooling reference

### Toxiproxy (non-Kubernetes, local/staging)

```bash
# Start Toxiproxy server
toxiproxy-server &

# Create a proxy for a dependency
toxiproxy-cli create --listen 0.0.0.0:8474 --upstream device-registry:8080 device-registry-proxy

# Add a toxic: 100% HTTP 503
toxiproxy-cli toxic add --type http_error --attribute status_code=503 \
  --upstream device-registry-proxy --name outage

# Add a toxic: 5-second latency
toxiproxy-cli toxic add --type latency --attribute latency=5000 \
  --upstream device-registry-proxy --name slow-dependency

# Add a toxic: 100% connection reset (hard failure)
toxiproxy-cli toxic add --type reset_peer \
  --upstream device-registry-proxy --name connection-reset

# Remove a toxic
toxiproxy-cli toxic delete --toxicName outage device-registry-proxy

# List active toxics
toxiproxy-cli inspect device-registry-proxy
```

### Istio fault injection (Kubernetes)

```yaml
# 100% 503 for all requests to a service
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: fault-injection-503
  namespace: edgeflow
spec:
  hosts:
    - device-registry.edgeflow.svc.cluster.local
  http:
    - fault:
        abort:
          percentage:
            value: 100
          httpStatus: 503
      route:
        - destination:
            host: device-registry.edgeflow.svc.cluster.local
```

```yaml
# Fixed delay on all requests
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: fault-injection-delay
  namespace: edgeflow
spec:
  hosts:
    - postgres.edgeflow.svc.cluster.local
  http:
    - fault:
        delay:
          percentage:
            value: 100
          fixedDelay: 5s
      route:
        - destination:
            host: postgres.edgeflow.svc.cluster.local
```

```bash
# Remove the fault injection
kubectl delete virtualservice fault-injection-503 -n edgeflow
kubectl delete virtualservice fault-injection-delay -n edgeflow
```

### Pod failure (Kubernetes)

```bash
# Delete a single pod (Kubernetes replaces it automatically)
kubectl delete pod \
  $(kubectl get pods -n edgeflow -l app=ingestion-service -o jsonpath='{.items[0].metadata.name}') \
  -n edgeflow

# Rolling deletion: one pod every 30 seconds for 5 minutes
for i in {1..10}; do
  POD=$(kubectl get pods -n edgeflow -l app=ingestion-service \
    -o jsonpath='{.items[0].metadata.name}')
  echo "Deleting pod: $POD"
  kubectl delete pod "$POD" -n edgeflow
  sleep 30
done
```

### Kafka partition leader manipulation

```bash
# List partition leaders for a topic
kafka-topics.sh --describe \
  --topic edgeflow.telemetry.events.v1 \
  --bootstrap-server kafka:9092

# Trigger preferred leader election (graceful)
kafka-leader-election.sh \
  --bootstrap-server kafka:9092 \
  --election-type PREFERRED \
  --topic edgeflow.telemetry.events.v1 \
  --partition 0

# Hard broker restart (Kubernetes — restarts the pod)
kubectl rollout restart statefulset/kafka -n kafka

# Monitor consumer group lag during recovery
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --describe \
  --group ingestion-consumer-group
```

### Network partition (iptables — use with extreme care)

```bash
# Block traffic from zone A to zone B (staging only)
# ALWAYS have a timeout or auto-revert scheduled before running
iptables -I INPUT -s <zone-b-cidr> -j DROP
iptables -I OUTPUT -d <zone-b-cidr> -j DROP

# Revert immediately after the experiment duration
iptables -D INPUT -s <zone-b-cidr> -j DROP
iptables -D OUTPUT -d <zone-b-cidr> -j DROP
```

For cloud environments, prefer security group changes over iptables — they are easier to audit and revert.

---

## Game day debrief question set

Use these in the post-game-day debrief (30 minutes, immediately after the exercise):

**Detection**
- How long did it take to detect the failure?
- Was the alert actionable? Did it fire at the right time with the right context?

**Runbook**
- Did the runbook cover what happened?
- Were any steps ambiguous, outdated, or in the wrong order?
- Were there missing steps that the team had to figure out on the fly?

**Communication**
- Did the team know who owned what?
- Was the status page / incident channel updated promptly?
- Were the right people notified?

**Resolution**
- Was the MTTR within the SLO target?
- Was data integrity maintained throughout?

**Action items** (one per gap identified; owner and sprint assigned before the debrief closes):
- Runbook gap: {description} — Owner: — Sprint:
- Alert gap: {description} — Owner: — Sprint:
- Communication gap: {description} — Owner: — Sprint:
