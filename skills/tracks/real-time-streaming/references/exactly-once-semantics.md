# Exactly-once semantics

Exactly-once is the most misunderstood guarantee in distributed systems. Most teams who say they need it either already have it via idempotency, or pay the transactional cost and still do not have it end-to-end because the side effects are non-transactional. Before you pay the price, be precise about what you are buying.

---

## What exactly-once actually means

**Broker-side exactly-once**: the broker and its producers cooperate so a single logical message, even if retried by the producer, appears exactly once in the log. Kafka's idempotent producer plus transactions provide this.

**End-to-end exactly-once**: the full chain producer → broker → consumer → downstream side effect (database write, external API call, emit to another topic) happens exactly once per logical input message.

These are different. Broker-side exactly-once is a necessary but wildly insufficient condition for end-to-end. The moment a consumer writes to a database that is not part of the broker transaction, you are back to at-least-once at the system level unless the write is idempotent.

The three honest positions:

1. **At-least-once + idempotent consumers** — the default for almost all systems. Cheap, simple, correct if consumers are idempotent.
2. **Kafka transactions (read-process-write within Kafka only)** — exactly-once when the consumer reads from Kafka, processes, and writes back to Kafka. Still at-least-once the moment you touch anything outside Kafka.
3. **Outbox pattern + idempotent consumers** — exactly-once-semantically for database-backed services publishing to a broker. The pragmatic answer for most non-trivial streaming systems.

At-most-once is rarely what anyone wants and does not need a strategy — it is what you get when you disable retries.

---

## Kafka transactions in detail

Kafka provides read-process-write transactions spanning consumer offset commits and producer writes to multiple topic-partitions. The guarantee: either all writes commit and the input offset advances, or none do.

### Producer configuration

```properties
# Producer — Kafka 3.x+
enable.idempotence=true
acks=all
retries=2147483647
max.in.flight.requests.per.connection=5
transactional.id=payments-processor-1
```

`transactional.id` must be stable per producer instance. Using a random ID on every restart defeats the zombie-fencing mechanism.

### Producer loop (Java, outline)

```java
producer.initTransactions();
while (true) {
    ConsumerRecords<String, Event> records = consumer.poll(Duration.ofMillis(200));
    producer.beginTransaction();
    try {
        for (ConsumerRecord<String, Event> r : records) producer.send(process(r));
        producer.sendOffsetsToTransaction(offsetsFor(records), consumer.groupMetadata());
        producer.commitTransaction();
    } catch (ProducerFencedException e) { producer.close(); throw e; }
      catch (KafkaException e)          { producer.abortTransaction(); }
}
```

### Consumer configuration

Any consumer reading the output topic must set:

```properties
isolation.level=read_committed
```

Otherwise aborted transaction writes are visible and you lose the guarantee on the read side.

### Throughput cost

Transactions commit via control messages and coordinator round-trips. Measured overhead vs plain idempotent producer:

- Small messages (< 1 KB), transaction batch of ~100: 20–30% throughput reduction.
- Larger batch (1000+ messages per transaction): 5–15% reduction.
- Transaction commit latency adds 5–15 ms to end-to-end p99.

Do not use transactions for single-message commits; the fixed per-transaction overhead crushes throughput. Batch or do not use them.

### When Kafka transactions are correct

- Stream processor pipelines entirely within Kafka (topic → Streams/Flink → topic).
- Exactly-once is a hard product requirement that cannot be met by idempotency.
- The consumer already reads only from Kafka topics, not from other sources.

### When Kafka transactions are wrong

- Any write outside Kafka (database, HTTP call, S3) — the transaction does not cover it.
- Extreme throughput systems where the 20–30% penalty is unacceptable.
- Systems where idempotency is cheaper to implement than the operational cost of transactions.

---

## The outbox pattern

The outbox is the right answer for services that own a database and publish events. Instead of writing to the DB and then publishing to the broker (two operations, atomic only by luck), you write the event to an outbox table in the same transaction as the business write. A separate publisher reads the outbox and publishes to the broker at-least-once. Downstream consumers deduplicate by event ID.

### Outbox table and business write (PostgreSQL)

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ
);
CREATE INDEX outbox_unpublished_idx ON outbox (created_at) WHERE published_at IS NULL;

-- Business write in one transaction:
BEGIN;
UPDATE orders SET status = 'shipped' WHERE id = $1;
INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
  VALUES ('order', $1, 'order.shipped',
          jsonb_build_object('order_id', $1, 'shipped_at', now()));
COMMIT;
```

### Publisher

Prefer CDC (Debezium reading the outbox table via logical replication) over polling at any nontrivial scale — push-based, lower latency, no load on the primary database. A polling publisher (`SELECT ... FOR UPDATE SKIP LOCKED` + publish + `UPDATE published_at`) is fine for small services; switch to CDC once publisher lag or DB load matters.

### Properties

- The business write and the event insert are atomic — if the transaction aborts, neither happens.
- The publisher can crash mid-publish and resume safely — `published_at` is set only after a successful send.
- At-least-once on the broker side — the publisher may retry and duplicate. Downstream consumers deduplicate on the `event_id` header.

### Cost

- One extra insert per business operation.
- Background publisher process.
- Outbox table bloat if the pruning job falls behind — add a scheduled `DELETE FROM outbox WHERE published_at < now() - interval '7 days'`.

---

## Idempotent consumers

Every at-least-once consumer must be idempotent. The pattern: extract a stable idempotency key from the message, check it against a deduplication store, and skip if already processed.

### Pattern (pseudocode)

```python
def handle(event):
    key = event.headers['event_id']  # stable, set by producer
    with db.transaction():
        if db.exists('processed_events', key):
            return  # duplicate, skip
        apply_side_effect(event)
        db.insert('processed_events', key=key, processed_at=now())
```

### Deduplication store options

- **Relational table with unique constraint** — simplest, strongest. `INSERT ... ON CONFLICT DO NOTHING`. Scales to millions of events per day on modest hardware.
- **Redis with TTL** — faster, eventually-consistent. Use when the idempotency window is bounded (hours) and rare duplicates past the window are acceptable.
- **The natural primary key of the target table** — if your business write is `INSERT INTO payments (id, ...) VALUES (event_id, ...)` with `id` as PK, the database enforces idempotency for free. Prefer this when possible.

### Idempotency window

Dedup storage grows unbounded unless capped. Pick a window based on the maximum realistic duplicate-delivery delay:

- Broker retry storm after a partition reassignment: minutes.
- Consumer replay after a DLQ drain: hours to a day.
- Operator-triggered backfill: up to the retention window.

Size the dedup store for the largest window you will tolerate. Prune older keys on a schedule. If a duplicate arrives after its key has been pruned, it will be reprocessed — design the side effect so a late duplicate is still correct (usually: idempotent DB writes with PK collision).

---

## Cost trade-offs summary

| Approach | Correctness | Throughput cost | Implementation cost | Where it fails |
|----------|-------------|-----------------|---------------------|----------------|
| At-least-once + naive consumer | Not exactly-once | None | Lowest | Duplicate side effects on retry |
| At-least-once + idempotent consumer | Exactly-once-semantically | Low (dedup lookup) | Medium | Storage growth if not pruned; incorrect idempotency key |
| Kafka transactions (read-process-write) | Exactly-once within Kafka only | 20–30% for small batches | Medium | The moment you write outside Kafka |
| Outbox + idempotent consumers | Exactly-once-semantically, end-to-end | Low (one extra insert) | Medium — requires a publisher | Outbox bloat; publisher lag |
| Two-phase commit across broker + DB | Exactly-once, theoretical | Very high | Very high | Coordinator failure; rarely worth it in practice |

Default: **outbox pattern on the produce side, idempotent consumers on the consume side**. Reach for Kafka transactions only when the entire pipeline is inside Kafka. Do not reach for 2PC.

---

## Worked example — payments event pipeline

Requirement: a `payments` service records a successful charge, publishes a `payment.completed` event, and a `receipts` service sends an email exactly once per completed payment.

### Producer side (payments service)

```sql
BEGIN;
INSERT INTO payments (id, amount, status) VALUES ($1, $2, 'completed');
INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
  VALUES ('payment', $1, 'payment.completed',
          jsonb_build_object('payment_id', $1, 'amount', $2));
COMMIT;
```

A Debezium connector tails the outbox table via logical replication and publishes to `payment.completed.v1` on Kafka. Event key = `payment_id`. Event ID header = outbox row UUID.

### Consumer side (receipts service)

```python
def on_payment_completed(event):
    event_id = event.headers['event_id']
    payment_id = event.value['payment_id']
    with db.transaction():
        inserted = db.execute("""
            INSERT INTO sent_receipts (event_id, payment_id, sent_at)
            VALUES (%s, %s, now())
            ON CONFLICT (event_id) DO NOTHING
            RETURNING event_id
        """, event_id, payment_id)
        if not inserted:
            return  # duplicate
        send_email(payment_id)  # after insert commits
```

Actually, send the email **before** committing with a transactional outbox on the consumer side too, or accept that an email may be sent twice if the process dies between send and commit. For email this is usually acceptable; for charging a card again it is not. Choose deliberately.

End-to-end result: the payment is recorded exactly once in the database, the event is published at-least-once, and the receipt is sent exactly once per unique `event_id`. No Kafka transactions. No 2PC. This is the default pattern.
