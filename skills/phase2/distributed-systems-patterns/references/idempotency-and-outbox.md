# Idempotency and the transactional outbox

Two patterns that make at-least-once messaging survivable in production. They are independent but almost always appear together: the outbox makes sure events are published exactly when a business write commits; idempotency makes sure consumers tolerate the duplicates that will inevitably happen.

---

## The dual-write problem

A handler that writes to a DB and publishes to a broker:

```python
# BROKEN — do not do this
def place_order(cmd):
    db.insert_order(cmd)           # (1)
    kafka.publish("OrderPlaced")   # (2)
```

Failure modes:
- (1) commits, (2) fails → DB has order, no event → downstream never sees it.
- (2) succeeds, (1) fails (rollback or crash before commit) → phantom event for an order that does not exist.
- (2) times out after succeeding → retry publishes duplicate.

You cannot fix this with ordering alone. Two different systems, no shared transaction.

---

## The transactional outbox

Insert the event into an `outbox` table **in the same transaction** as the business write. A separate relay reads the outbox and publishes. The atomicity is local to the DB; the relay handles the broker side with retries.

### Schema

```sql
CREATE TABLE outbox (
  id             BIGSERIAL   PRIMARY KEY,
  aggregate_id   TEXT        NOT NULL,   -- e.g. order_id; enables consistent partition key
  event_type     TEXT        NOT NULL,   -- e.g. 'OrderPlaced'
  payload        JSONB       NOT NULL,
  headers        JSONB       NULL,        -- trace context, tenant, content-type
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at   TIMESTAMPTZ NULL,
  attempt_count  INT         NOT NULL DEFAULT 0,
  last_error     TEXT        NULL
);

-- Only unpublished rows are scanned by the relay
CREATE INDEX idx_outbox_unpublished
  ON outbox (created_at)
  WHERE published_at IS NULL;
```

### Writer side

```python
def place_order(cmd):
    with db.transaction() as tx:
        tx.execute(
            "INSERT INTO orders(id, customer_id, total) VALUES (%s, %s, %s)",
            (cmd.order_id, cmd.customer_id, cmd.total),
        )
        tx.execute(
            "INSERT INTO outbox(aggregate_id, event_type, payload, headers) "
            "VALUES (%s, %s, %s, %s)",
            (cmd.order_id, "OrderPlaced",
             {"order_id": cmd.order_id, "customer_id": cmd.customer_id},
             {"trace_id": current_trace_id()}),
        )
    # tx commit: either both rows land or neither does.
```

### Relay loop

```python
def relay_tick():
    rows = db.fetch_all(
        "SELECT id, aggregate_id, event_type, payload, headers "
        "FROM outbox "
        "WHERE published_at IS NULL "
        "ORDER BY id "
        "LIMIT 500 "
        "FOR UPDATE SKIP LOCKED"   # allows multiple relay workers
    )
    for r in rows:
        try:
            broker.publish(
                topic=topic_for(r.event_type),
                key=r.aggregate_id,
                value=r.payload,
                headers=r.headers,
            )
            db.execute(
                "UPDATE outbox SET published_at = now() WHERE id = %s",
                (r.id,),
            )
        except BrokerError as e:
            db.execute(
                "UPDATE outbox SET attempt_count = attempt_count + 1, "
                "last_error = %s WHERE id = %s",
                (str(e), r.id),
            )
            # Leave published_at NULL → will be retried on next tick
```

**Key properties:**
- `FOR UPDATE SKIP LOCKED` lets you run multiple relay workers safely without double-publishing.
- The broker is told `key = aggregate_id` so partitioning preserves per-aggregate ordering.
- If the relay crashes between broker ack and DB update, the next tick republishes. That is why consumers **must** be idempotent — see below.

### Housekeeping

Published rows grow forever if untouched. Purge after a retention window:

```sql
DELETE FROM outbox
WHERE published_at IS NOT NULL
AND published_at < now() - INTERVAL '7 days';
```

Seven days is a pragmatic default — long enough to debug a production incident, short enough to keep the table small.

### Variants

- **Polling outbox (above)** — simple, works on any DB. Latency = poll interval (typically 100ms–1s).
- **Log-tailing** (Debezium, Postgres logical replication) — no polling, near-zero latency, but operational complexity. Use only if the latency savings matter.
- **Listen/notify** (Postgres `NOTIFY`) — wake the relay immediately when a row is inserted. Combine with polling as fallback in case notifications are missed.

---

## Idempotency for consumers

At-least-once means duplicates are a fact. Two strategies:

### Natural idempotency

Design the operation so replay is a no-op:

- `SET balance = 100` — idempotent.
- `balance = balance + 50` — NOT idempotent.
- `UPSERT customer(id, email)` — idempotent.
- `INSERT (UNIQUE key)` + swallow-unique-violation — idempotent.

Whenever possible, make operations naturally idempotent. It is cheaper than the keyed approach.

### Keyed idempotency (dedup table)

When natural idempotency is impossible — e.g. "charge card" where you really do want to charge exactly once — use a dedup table keyed by an idempotency key.

```sql
CREATE TABLE idempotency_keys (
  key              TEXT        PRIMARY KEY,
  request_hash     TEXT        NOT NULL,    -- hash of the full request body
  status           TEXT        NOT NULL,    -- 'in_progress' | 'completed' | 'failed'
  response_body    JSONB       NULL,
  response_status  INT         NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at     TIMESTAMPTZ NULL,
  expires_at       TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '24 hours'
);

CREATE INDEX idx_idempotency_expires ON idempotency_keys (expires_at);
```

### The `Idempotency-Key` header convention

This is a widely used convention (Stripe popularized it). The client supplies `Idempotency-Key: <UUID>` on unsafe HTTP methods. The server returns the same response for the same key within the retention window.

```
POST /v1/payments HTTP/1.1
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{"amount_cents": 1000, "card_token": "tok_abc"}
```

### Server-side handler

```python
def charge_payment(req, headers):
    idem_key = headers.get("Idempotency-Key")
    if not idem_key:
        raise HTTPError(400, "Idempotency-Key header required")

    request_hash = sha256(canonical_json(req.body))

    try:
        db.execute(
            "INSERT INTO idempotency_keys(key, request_hash, status) "
            "VALUES (%s, %s, 'in_progress')",
            (idem_key, request_hash),
        )
    except UniqueViolation:
        existing = db.fetch_one(
            "SELECT status, request_hash, response_body, response_status "
            "FROM idempotency_keys WHERE key = %s",
            (idem_key,),
        )
        if existing.request_hash != request_hash:
            # Same key, different body → client bug; refuse
            raise HTTPError(422, "Idempotency-Key reused with different payload")
        if existing.status == "completed":
            return HTTPResponse(existing.response_status, existing.response_body)
        if existing.status == "in_progress":
            # Another worker is handling this request
            raise HTTPError(409, "Request still being processed; retry shortly")
        # status == "failed" → allow retry: fall through to processing below

    try:
        result = process_payment(req)
        db.execute(
            "UPDATE idempotency_keys SET status='completed', "
            "response_body=%s, response_status=%s, completed_at=now() "
            "WHERE key=%s",
            (result.body, result.status, idem_key),
        )
        return result
    except Exception:
        db.execute(
            "UPDATE idempotency_keys SET status='failed' WHERE key=%s",
            (idem_key,),
        )
        raise
```

### Key rules

- **Client-supplied, not server-generated.** The whole point is for the client to use the same key across retries.
- **Hash the request body too.** Catches clients reusing keys with different payloads.
- **TTL the keys.** 24h is a common default for HTTP endpoints; some use 7d. For internal message consumers tracked by message id, TTL should be longer than the broker's maximum retention.
- **Purge expired keys** with a scheduled job. Otherwise the table grows without bound.
- **Status transitions matter.** `in_progress` is there so two simultaneous retries do not both process; one waits or 409s.

### For Kafka / queue consumers

Same pattern, different key source. Use the broker's message id (`offset` + `partition` + `topic`, or a producer-generated `event_id` in the payload):

```python
def handle_order_placed(msg):
    event_id = msg.value["event_id"]  # producer set this
    try:
        db.execute(
            "INSERT INTO processed_events(event_id, topic, processed_at) "
            "VALUES (%s, %s, now())",
            (event_id, msg.topic),
        )
    except UniqueViolation:
        return  # already processed, skip

    # Business logic runs exactly once per event_id
    process_order(msg.value)
```

---

## Putting it together — end-to-end exactly-effectively-once

True exactly-once delivery does not exist in distributed systems. But you can get **exactly-once processing effect** by combining:

1. **Transactional outbox on the producer** — event is published iff the DB commit happened.
2. **Idempotent consumer** — duplicate deliveries are no-ops.
3. **Deterministic event IDs** — same business action → same event id on every retry.

The system is still at-least-once on the wire. The DB table on either end makes the net effect exactly-once.

---

## Anti-patterns

- **Publishing from a post-commit hook.** Hooks can fail silently; no retry; no durability. Use the outbox.
- **Outbox with no retention policy.** Table grows until DB slows to a crawl.
- **Single-worker relay with no `SKIP LOCKED`.** Becomes the bottleneck; no horizontal scaling.
- **Idempotency key TTL shorter than broker retention.** A message replayed from the broker after the key expired gets processed twice.
- **Trusting the client to generate unique keys.** Always combine key + request hash so reused keys with different payloads are caught.
- **Using a "processed events" table that is never cleaned.** Same growth problem as the outbox.
- **Hash-based dedup over message body without a stable key.** Any serialization drift (field order, whitespace) causes false non-duplicates. Use canonical JSON or an explicit event id.
