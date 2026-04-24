---
name: distributed-systems-patterns
description: >
  Activate when designing or implementing multi-service, event-driven, or
  message-based systems and the engineer mentions saga pattern, orchestration
  vs choreography, compensating transaction, event sourcing, CQRS, command
  query separation, transactional outbox, dual-write problem, idempotency key,
  deduplication, exactly-once, at-least-once, distributed transaction, two-phase
  commit, eventual consistency, causal consistency, strong consistency, read
  your writes, retry with backoff, exponential backoff, jitter, or circuit
  breaker in a distributed-coordination (not perf) context. Use when choosing
  between synchronous RPC and async events, when a write must update state in
  two systems (DB + queue), when consumers must tolerate duplicate messages,
  or when service boundaries force you to give up ACID transactions.
---

# Distributed systems patterns

## Purpose

Once a system is split across services, databases, and message brokers, the ACID guarantees of a single database go away. You trade them for network partitions, duplicate messages, partial failures, and the dual-write problem. This skill is the decision kit for picking the right pattern — saga vs distributed transaction, orchestration vs choreography, sync vs async, outbox vs direct publish, event sourcing vs CRUD — and for getting the mechanics right (compensation, idempotency, retry, consistency level). Pick the weakest pattern that meets the requirement. Every stronger guarantee costs complexity, latency, or both.

---

## When to use

- Designing a feature that writes to a database AND publishes an event / message.
- A business process spans two or more services that each own their own data.
- Consumers of a queue may receive duplicates (Kafka, SQS, RabbitMQ at-least-once).
- A team is reaching for a two-phase commit or distributed transaction — almost always the wrong answer.
- Choosing the consistency level for a new read path (strong? causal? eventual?).
- Retry logic is missing, naive (fixed sleep), or causing thundering herd on recovery.
- A caller asks "what happens if step 3 of 5 fails?" and nobody has a crisp answer.
- Pitching event sourcing or CQRS — pressure-test the motivation before accepting.

---

## When NOT to use

- General service-boundary or system design review — use `architecture-review-governance`.
- Designing the API / event schema itself (field types, versioning, compatibility) — use `specification-driven-development`.
- Proving correctness of a protocol with a model checker (TLA+, Alloy) — use `formal-verification`.
- Circuit breakers for perf / latency reasons (slow dependency, cascading latency) — use `performance-reliability-engineering`. This skill covers circuit breakers as coordination primitives.
- Defining metrics, traces, SLOs for the distributed system — use `observability-sre-practice`.
- Runtime enforcement of the event contract across producer/consumer — use `api-contract-enforcer`.

---

## Process or checklist

### Step 1 — Do you actually need a distributed pattern?

Ask before designing anything:

- Can this be a single service with one database? If yes, stop. ACID is free there.
- Is the second write actually critical, or can it be a nightly batch?
- Is async necessary, or would a synchronous RPC with a timeout be clearer?

Distributed patterns are a tax. Pay it only when the benefit is real.

### Step 2 — Pick the coordination style

```
multi-service workflow
          │
          ▼
   does one service "own" the workflow end-to-end?
          │
   ┌──────┴──────┐
  yes            no
   │              │
   ▼              ▼
 orchestration   choreography
 (saga w/        (event-driven,
  coordinator)    each service reacts)
```

- **Orchestration**: a single service (the orchestrator) calls each step and decides what to do on failure. Easier to reason about, easier to debug, single point of change. Downside: the orchestrator is a coupling hub.
- **Choreography**: services publish events; other services react. No central point. Harder to trace end-to-end; reasoning about "what is the state of the workflow right now?" is painful without good observability.

Default to orchestration unless you have a clear reason. Choreography rewards mature teams with strong distributed tracing.

### Step 3 — Design the compensations

Every saga step that mutates state needs a compensating action that undoes it. Write the compensation at the same time as the forward step, not later.

- Forward: `reserveInventory(orderId, sku, qty)` → Compensation: `releaseInventoryReservation(orderId)`
- Forward: `chargeCard(orderId, amount)` → Compensation: `refundCharge(orderId)`
- Forward: `sendConfirmationEmail(orderId)` → Compensation: **none possible** (email is already sent). Move this step to the very end, after all reversible steps have committed.

Compensations must be idempotent — they may be retried on failure.

### Step 4 — Solve the dual-write problem with the outbox

If a handler writes to the DB *and* publishes to Kafka, the two writes can diverge (DB commits, Kafka publish fails → event lost; or Kafka publishes, DB rollback → phantom event). Never publish directly from handler code.

Use the **transactional outbox**:
1. In the same DB transaction as the business write, insert a row into an `outbox` table.
2. A separate relay process reads unpublished outbox rows and publishes to the broker.
3. Relay marks the row published only after broker ack.

Details and schema in `references/idempotency-and-outbox.md`.

### Step 5 — Make every consumer idempotent

At-least-once delivery is the norm. Consumers will see duplicates. Two approaches:

- **Idempotency key + dedup table**: producer or caller supplies a unique key; consumer checks a dedup table before processing. Works for external API endpoints (`Idempotency-Key` header convention).
- **Natural idempotency**: design the operation so replay is a no-op (`SET balance = 100` is idempotent; `balance = balance + 50` is not).

See `references/idempotency-and-outbox.md` for the dedup table schema.

### Step 6 — Pick the consistency model explicitly

| Model | Example requirement | Cost |
|-------|---------------------|------|
| Strong (linearizable) | "Balance must never show negative" | Latency, availability hit during partition |
| Causal | "User sees their own comment immediately after posting" | Needs session / version vectors |
| Read-your-writes | Same user, same session only | Sticky routing or write-through cache |
| Eventual | "Analytics dashboard refreshes every minute" | None — cheapest |

Write the chosen level in the design doc. Do not leave it implicit.

### Step 7 — Retry with exponential backoff + full jitter

Naive fixed-interval retry creates thundering herds when a dependency recovers. Use exponential backoff with full jitter:

```
delay = random(0, min(cap, base * 2^attempt))
```

Cap attempts. After the cap, move the message to a dead-letter queue — do not retry forever.

### Step 8 — Wrap cross-service calls in a circuit breaker

In a distributed-coordination context, the circuit breaker is about stopping a failing service from corrupting shared state via half-completed workflows. Open circuit → route new work elsewhere (or fail fast and compensate upstream). Contrast with the perf-reliability use: there, circuit breaker is about avoiding latency pile-up.

### Step 9 — Consider event sourcing / CQRS only if justified

These are not defaults. See `references/event-sourcing-cqrs-guide.md` for the decision criteria. If the domain is CRUD with modest read/write ratio, stay with a traditional DB model.

### Step 10 — Log the decision

Append a line to `docs/skill-log.md`. If the pattern choice is architecturally significant, also write an ADR (invoke `architecture-decision-records`).

---

## Anti-patterns

- **Dual write without outbox** — "DB commit then Kafka publish" in the same handler. Inconsistent state under failure.
- **Distributed two-phase commit across services** — fragile, blocks on coordinator failure, vendor-specific. Use a saga instead.
- **Saga without compensations** — if step 4 fails, there is no story for undoing steps 1–3. Half-completed workflow becomes a ticket.
- **Non-idempotent consumer** — "it usually works" until the first retry storm creates duplicate charges.
- **Fixed-interval retry** — creates thundering herd on recovery.
- **Event sourcing for CRUD** — complexity tax with no return. Use it for audit-heavy domains or time-travel debugging, not for a user-profile service.
- **Choreography with no tracing** — nobody can answer "where is order 42 right now?" Orchestration or strong distributed tracing is mandatory.
- **Strong consistency everywhere** — over-serializes the system and destroys availability during partitions. Pick per read path.

---

## Output format with real examples

### Saga orchestrator (pseudo-code)

```python
# Orchestrated saga — single coordinator drives the workflow
class PlaceOrderSaga:
    def run(self, cmd: PlaceOrder) -> SagaResult:
        completed = []  # stack of compensations

        try:
            reservation = self.inventory.reserve(cmd.order_id, cmd.items)
            completed.append(lambda: self.inventory.release(cmd.order_id))

            charge = self.payments.charge(cmd.order_id, cmd.amount, cmd.idem_key)
            completed.append(lambda: self.payments.refund(charge.id))

            shipment = self.shipping.create(cmd.order_id, cmd.address)
            completed.append(lambda: self.shipping.cancel(shipment.id))

            # Irreversible step LAST
            self.notifier.send_confirmation(cmd.order_id)
            return SagaResult.ok(cmd.order_id)

        except SagaStepError as e:
            # Compensate in reverse order; each compensation is idempotent
            for compensate in reversed(completed):
                self._run_with_retry(compensate)
            return SagaResult.failed(cmd.order_id, reason=str(e))
```

### Transactional outbox — table DDL

```sql
CREATE TABLE outbox (
  id            BIGSERIAL PRIMARY KEY,
  aggregate_id  TEXT        NOT NULL,        -- e.g. order_id
  event_type    TEXT        NOT NULL,        -- e.g. 'OrderPlaced'
  payload       JSONB       NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at  TIMESTAMPTZ NULL,            -- set by the relay after broker ack
  headers       JSONB       NULL             -- trace context, tenant, etc.
);

CREATE INDEX idx_outbox_unpublished
  ON outbox (created_at)
  WHERE published_at IS NULL;
```

Writer commits the business row and the outbox row in the same transaction. A relay polls `WHERE published_at IS NULL`, publishes to the broker, then updates `published_at`.

### Idempotency-Key handling (HTTP endpoint)

```python
# Client supplies: Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
@app.post("/v1/payments")
def charge_payment(req, headers):
    idem_key = headers.get("Idempotency-Key")
    if not idem_key:
        raise HTTPError(400, "Idempotency-Key header required")

    # Atomic insert; rely on unique constraint to detect replay
    try:
        db.execute(
            "INSERT INTO idempotency_keys(key, request_hash, status, created_at) "
            "VALUES (%s, %s, 'in_progress', now())",
            (idem_key, hash_request(req)),
        )
    except UniqueViolation:
        existing = db.fetch_one(
            "SELECT status, response_body FROM idempotency_keys WHERE key = %s",
            (idem_key,),
        )
        if existing.status == "completed":
            return existing.response_body  # safe replay
        raise HTTPError(409, "Request with this Idempotency-Key is still processing")

    result = process_payment(req)
    db.execute(
        "UPDATE idempotency_keys SET status='completed', response_body=%s WHERE key=%s",
        (result.to_json(), idem_key),
    )
    return result
```

Keys are kept for 24h (configurable TTL) and then purged — see `references/idempotency-and-outbox.md` for the full schema and retention policy.

---

## Skill execution log

Every firing appends one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] distributed-systems-patterns | outcome: OK|BLOCKED|PARTIAL | next: <skill> | note: <brief>
```

Example entries:
```
[2026-04-20] distributed-systems-patterns | outcome: OK | next: code-implementer | note: chose orchestrated saga for order placement; compensations defined for all 3 reversible steps
[2026-04-20] distributed-systems-patterns | outcome: OK | next: database-migration | note: added outbox table to payment service schema
[2026-04-20] distributed-systems-patterns | outcome: PARTIAL | next: architecture-decision-records | note: event sourcing proposed but trade-offs not justified; writing ADR to force the decision
```

If `docs/skill-log.md` does not exist, create it with the header defined by `sdlc-orchestrator`.

---

## Reference files

Load these on demand when the corresponding decision arises:

- `references/saga-patterns.md` — orchestration vs choreography decision matrix, worked example of each, compensation design rules, when a saga is overkill.
- `references/event-sourcing-cqrs-guide.md` — when event sourcing earns its complexity, projection and snapshot mechanics, CQRS with and without event sourcing, read-model rebuild procedure.
- `references/idempotency-and-outbox.md` — outbox table DDL and relay loop, idempotency key dedup schema, `Idempotency-Key` header convention, TTL / retention, natural vs keyed idempotency.
