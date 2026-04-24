# Backpressure patterns

A streaming system is only as fast as its slowest consumer. When producers outpace consumers — which they will, at some point — something has to give. Backpressure is the set of strategies for deciding what gives and how the signal propagates upstream. Get this wrong and either the broker fills up and crashes, or you silently drop data, or the consumer OOMs because its in-memory buffer exploded.

Every streaming system must explicitly pick one of three postures for the slow-consumer case: **block**, **buffer**, or **shed**. Pretending the case will not happen is a fourth option and it is the one that causes outages.

---

## The three postures

### Block

The producer or upstream stage slows down when the downstream is slow. Natural in synchronous pipelines and reactive streams with demand-based pull. Pros: no data loss, no unbounded memory growth. Cons: the slowness propagates all the way to the ingress; if ingress is user-facing, users experience the lag.

Use when: data loss is unacceptable and the ingress can tolerate slowdown (internal services, batch-backed producers, event sourcing).

### Buffer

Absorb the difference between producer rate and consumer rate in an in-memory or on-disk queue. Kafka, Kinesis, Pulsar, and NATS JetStream are all large durable buffers. The broker's retention is the buffer. Application-level queues (bounded `BlockingQueue` in Java, `asyncio.Queue` in Python, reactor's `onBackpressureBuffer`) are smaller buffers inside a service.

Use when: the rate mismatch is transient. Buffers smooth bursts; they cannot absorb sustained overproduction. A bounded buffer that fills still has to pick block, shed, or fail — buffering delays the decision, it does not eliminate it.

### Shed

Drop messages when the system cannot keep up. Acceptable when the data is lossy by nature (metrics, tracing, telemetry, best-effort notifications) or when fresh data matters and stale data is worthless (real-time dashboards, live sports feeds, market data where newer quotes supersede older ones).

Use when: data loss is acceptable or the data's value decays rapidly with age.

---

## Load shedding — ingress vs consumer

Where you shed matters. The cost of a shed decision is highest near the consumer and lowest at the ingress, because every stage between ingress and consumer has already paid serialization, network, broker storage, and partition routing costs for a message that will be discarded.

### Shed at ingress

The producer or API gateway rejects load before it hits the broker. Implemented as rate limits, circuit breakers, or admission control. Fast, cheap, and surfaces the problem to the upstream caller (who can retry with backoff or fail gracefully).

Example — token bucket at ingress:

```yaml
# Envoy local rate limit
rate_limits:
  - actions:
      - generic_key: { descriptor_value: "events-ingress" }
    token_bucket:
      max_tokens: 10000
      tokens_per_fill: 10000
      fill_interval: 1s
```

Example — Kafka producer with `max.block.ms` to fail fast instead of buffering unbounded:

```properties
max.block.ms=100
buffer.memory=67108864
# When producer buffer is full and can't flush in 100ms, send() throws.
# The caller decides: retry, shed, or propagate the failure.
```

### Shed at consumer

The consumer drops messages when its internal processing queue is full. Rarely the right answer in a log-based system — the broker has already persisted the message, so "dropping" at the consumer means committing the offset without processing, which is the same as silent data loss with extra steps.

The correct form at the consumer is **do not commit** the offset and let the broker reassign the partition to a faster instance, combined with autoscaling based on lag. This is not really shedding — it is redirection.

Legitimate consumer-side shed cases:

- **Priority-based**: keep high-priority messages, drop low-priority ones when lag exceeds a threshold.
- **Sample-based**: for observability streams, drop 90% of traces above a threshold and keep the rest.
- **Freshness-based**: process only messages with timestamps in the last N seconds; skip and commit offsets for older messages that are no longer actionable.

Always log and meter every shed decision. A silent drop is indistinguishable from a bug.

---

## Buffering strategies

### Bounded in-memory queue

```java
BlockingQueue<Event> queue = new ArrayBlockingQueue<>(10_000);

// Producer thread
if (!queue.offer(event, 50, TimeUnit.MILLISECONDS)) {
    metrics.counter("queue.shed").increment();
    // Decide: shed, fail the upstream, or retry
}

// Consumer thread
Event event = queue.take();
process(event);
```

Size the queue against the worst-case burst duration × producer rate, capped by available memory. Default far too many systems: unbounded `LinkedBlockingQueue`. Unbounded queues turn memory pressure into an OOM rather than a controlled failure.

### On-disk spillover

When the expected burst exceeds reasonable RAM, spill to disk. Kafka is the canonical on-disk buffer between services. Chronicle Queue, LMDB, and local RocksDB are in-process options.

### Broker as buffer

The broker is already the buffer between your producer and your consumer. Use it. Let consumers fall behind and catch up during low-traffic windows. Alert on consumer lag but do not panic at transient spikes — that is exactly what the broker retention is sized for.

Retention must exceed worst-case catch-up time. If your consumer can fall 4 hours behind during a deploy, do not run Kafka with 2-hour retention. Kinesis default is 24 hours — extend if your consumers can go down longer than that.

---

## Backpressure in reactive systems

Reactive streams (Project Reactor, RxJava, Akka Streams) implement backpressure as a demand-based protocol: the subscriber pulls (`request(n)`) and the publisher produces at most `n` items. This is structural backpressure — it cannot overproduce by design.

### Project Reactor

```java
Flux.from(source)
    .onBackpressureBuffer(1000,
        dropped -> metrics.counter("backpressure.dropped").increment(),
        BufferOverflowStrategy.DROP_OLDEST)
    .publishOn(Schedulers.parallel(), 256)  // prefetch = 256
    .flatMap(this::processAsync, 16)         // concurrency = 16
    .subscribe();
```

Backpressure operators by intent:

- `onBackpressureBuffer(n)` — buffer up to n, then overflow strategy applies
- `onBackpressureDrop()` — drop newest when downstream is not ready
- `onBackpressureLatest()` — keep only the most recent item (good for metrics/state)
- `onBackpressureError()` — fail the stream (test environments, fail-loud systems)

Default `prefetch` and `concurrency` values are almost never right for production. Tune them against measured throughput and memory.

### RxJava

Same operators as Reactor: `onBackpressureBuffer`, `onBackpressureDrop`, `onBackpressureLatest`. `Flowable` respects backpressure; `Observable` does not — do not use `Observable` for streaming.

### Akka Streams

Akka Streams has async boundaries with demand signalling built into every `GraphStage`. Configure buffering via `.buffer(size, overflowStrategy)`:

```scala
Source.fromPublisher(source)
  .buffer(1000, OverflowStrategy.dropHead)
  .mapAsync(parallelism = 16)(processAsync)
  .runWith(Sink.ignore)
```

`OverflowStrategy`: `backpressure` (signal upstream), `dropHead` (drop oldest), `dropTail` (drop newest), `dropBuffer` (clear all), `fail` (abort).

### When reactive backpressure is not enough

Reactive backpressure handles in-process demand. It does not help when:

- The source is an external broker — the broker will keep delivering regardless of internal demand unless you explicitly pause/throttle the consumer.
- The sink is an external service under its own load — HTTP 429s still need circuit breakers and retries layered on top.
- Multiple sources converge and one is faster — you need explicit merge strategies.

Use reactive operators for in-process flow control; use consumer-level pause/resume, rate limits, and circuit breakers for cross-service flow control.

---

## Rate limiting vs backpressure

Rate limiting sets a ceiling. Backpressure communicates slowness. They are complementary, not alternatives.

| | Rate limiting | Backpressure |
|--|--------------|--------------|
| Posture | "You may send at most N/s" | "I am slow; adjust" |
| Signal direction | Downstream enforces on upstream | Downstream signals; upstream adjusts |
| When it fires | Predefined limit | Actual slowness |
| Failure mode | Rejects with 429 | Slows, buffers, or sheds |
| Good for | Capacity guarantees, fairness, abuse prevention | Matching dynamic producer/consumer speeds |

Rate limit the ingress to protect against absolute overload. Apply backpressure internally to match dynamic speeds between stages. Do not replace one with the other.

Example stack:
1. **Ingress**: token bucket rate limit at the API gateway. Rejects 429 above N req/s per tenant.
2. **Producer**: bounded Kafka producer buffer with `max.block.ms` fail-fast.
3. **Broker**: retention and partition count sized for worst-case consumer lag.
4. **Consumer**: bounded in-process queue, autoscaling on consumer lag, circuit breaker on downstream calls.

Every layer picks block, buffer, or shed explicitly. There is no layer that hopes it will not matter.

---

## What to document in the design doc

For every streaming system, document:

1. **Slow-consumer posture per consumer group**: block, buffer, or shed, with justification.
2. **Buffer sizes** at each stage, with the worst-case burst calculation.
3. **Shed trigger conditions** and what gets shed (all data, low-priority only, sampled).
4. **Rate limits** at the ingress with numbers and the fairness model (per-tenant, per-key).
5. **Alerting thresholds** on consumer lag, broker buffer utilization, and in-process queue depth.
6. **Scale-out triggers**: at what lag or buffer depth do consumers autoscale.

If any of these is unspecified, the backpressure strategy is "hope" — which is the fourth option.
