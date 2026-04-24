---
name: real-time-streaming
description: >
  Activates when the user mentions Kafka, Kinesis, Google Pub/Sub, NATS JetStream,
  Pulsar, RabbitMQ Streams, event streaming, real-time pipeline, stream processing,
  low latency or sub-100ms budgets, exactly-once / at-least-once / at-most-once
  semantics, backpressure, consumer lag, windowing, watermarks, Flink, Spark
  Streaming, Kafka Streams, or ksqlDB. Also triggers on explicit declaration:
  "Real-time track" or "Streaming track".
---

# Real-time / streaming track

## Purpose

This track covers systems where data arrives as an unbounded stream and must be processed with low latency, high throughput, and strong delivery guarantees — event-driven architectures on Kafka, Kinesis, Pub/Sub, NATS JetStream, Pulsar, or RabbitMQ Streams, plus the stream processors that sit on top (Flink, Kafka Streams, Spark Streaming, ksqlDB). These systems fail in ways that request-response services do not. A producer retry silently duplicates a financial event. A consumer falls behind by six hours before anyone sees the dashboard. A broker partition leader change triggers a rebalance storm that takes the whole consumer group down. A schema change rolled out on the producer deserializes to garbage on an old consumer. The standard 41 skills plus a mode setting do not enforce delivery-semantics discipline, consumer lag SLOs, backpressure strategy, or broker failure testing. This track elevates those from advisory to load-bearing and tightens stage gates so a streaming build cannot ship without them.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "Kafka", "Kinesis", "Google Pub/Sub", "NATS JetStream", "Pulsar", "RabbitMQ Streams"
- "event streaming", "streaming pipeline", "real-time pipeline", "event-driven architecture"
- "low latency", "sub-100ms", "p99 latency budget", "tail latency"
- "exactly-once", "at-least-once", "at-most-once", "delivery semantics"
- "backpressure", "consumer lag", "rebalance", "dead letter queue", "DLQ"
- "windowing", "tumbling window", "sliding window", "session window", "watermarks", "late data"
- "Flink", "Spark Streaming", "Kafka Streams", "ksqlDB", "Beam"
- "AsyncAPI", "schema registry" (in streaming context), "Avro on the wire"

Or when the system under discussion has these properties:

- A producer emits events continuously and at least one consumer processes them with a latency target measured in milliseconds or seconds.
- A topic/stream is retained long enough that replay is a legitimate recovery strategy.
- Consumer lag is a product concern — a user-visible or SLA-affecting signal.
- Throughput requirements exceed what a synchronous API would sustain, or the system is inherently asynchronous by design.
- Broker infrastructure (self-managed Kafka, MSK, Confluent Cloud, Kinesis, PubSub, NATS) is on the bill of materials.
- A stream processor (Flink, Kafka Streams, Spark Structured Streaming, ksqlDB, Beam) computes windowed aggregates, joins, or materialized views over one or more topics.
- CDC (Debezium, Maxwell, Kinesis DMS) feeds a downstream topic and any consumer treats it as an authoritative event source.

---

## When NOT to activate

Do NOT activate this track when:

- The work is a periodic batch job (hourly, daily, weekly) with no continuous stream — use the Data platform / ML ops track instead.
- The "streaming" is just a request-response API that happens to use WebSockets or SSE with no broker and no stream processor behind it — standard mode is sufficient.
- A message broker is used for one-off notifications (send-an-email, fan-out-to-two-services) with no retention, no replay, no consumer lag concern — that is a queue, not a stream; no track needed.
- You are building a data pipeline that batches and loads to a warehouse and never reads from a broker under a latency SLO — that is the Data platform track.
- You are designing an internal pub/sub to decouple two microservices and the traffic is low (hundreds of events per day) — `distributed-systems-patterns` as a standalone skill is sufficient.

If you are unsure, answer this: does consumer lag (offset behind head) appear on a dashboard that someone is paid to watch? If yes, activate. If no, don't.

Composition with other tracks is common and encouraged. A streaming data platform (CDC → Kafka → Flink → warehouse) runs Real-time + Data platform. A payments event backbone runs Real-time + Fintech. A clinical telemetry stream runs Real-time + Healthcare. Every track still applies its elevations and gates; strictest-wins on conflicts.

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| distributed-systems-patterns | Mandatory | Mandatory | Mandatory | Mandatory + protocol review |
| performance-reliability-engineering | Mandatory | Mandatory | Mandatory + capacity planning | Mandatory + soak test + chaos |
| observability-sre-practice | Mandatory (lag + throughput) | Mandatory | Mandatory + per-topic SLOs | Mandatory + per-partition SLOs |
| specification-driven-development | Standard | Mandatory (AsyncAPI) | Mandatory + schema registry | Mandatory + schema registry + compatibility modes |
| chaos-engineering | Advisory | Conditional | Mandatory (broker failure, partition loss) | Mandatory + quarterly game day |
| caching-strategy | N/A | Advisory | Mandatory (materialised-view and state-store cache design required) | Mandatory |
| formal-verification | N/A | N/A | Conditional (for custom delivery-semantics or ordering protocols) | Mandatory for any custom consensus, leader-election, or ordering protocol |
| incident-postmortem | Standard | Standard + consumer-lag incident runbook | Standard + consumer-lag analysis + root-cause for DLQ overflow | Standard + consumer-lag analysis + capacity post-mortem |

Only skills whose treatment differs from the default mode behaviour are listed. All other skills retain their mode defaults.

Notes on the additional elevations:

- `caching-strategy` at Standard+ covers materialised views, state stores (RocksDB-backed Kafka Streams, Flink state backends), and result caches for windowed aggregates. These are first-class streaming architecture concerns, not peripheral optimisations. Cache invalidation bugs here manifest as silent query-result staleness, which is a consumer-facing correctness problem.
- `formal-verification` is Conditional at Standard for teams writing custom delivery-semantics logic (custom idempotency protocols, custom offset-management schemes) and Mandatory at Rigorous for any custom consensus, leader-election, or ordering protocol. Kafka transactions and Flink checkpointing are well-specified; custom extensions are not.
- `incident-postmortem` adds streaming-specific runbook content at Lean+: consumer-lag incident, DLQ overflow, and rebalance storm. At Standard+, root-cause analysis must distinguish between throughput incidents (capacity), correctness incidents (deduplication failure, offset skip), and availability incidents (broker loss, consumer crash).

Rationale for the five elevations:

- `distributed-systems-patterns` — idempotency, outbox, partition ordering, and rebalance-safety are foundational; without them every other decision compounds into wrong answers. Rigorous adds a formal protocol review (leader election, consumer-group rebalance, transaction coordinator interaction).
- `performance-reliability-engineering` — streaming systems live or die on throughput and tail latency; capacity planning at Standard prevents the "we shipped it and it fell over at peak" outcome. Rigorous adds soak (24h+) and chaos under load.
- `observability-sre-practice` — consumer lag and throughput are the two non-negotiable signals. Per-topic SLOs catch topic-level hot-spotting that a cluster-wide SLO masks; per-partition SLOs catch key-skew problems.
- `specification-driven-development` — AsyncAPI contracts and a schema registry with an explicit compatibility mode are the only defenses against producer/consumer drift. Rigorous pins compatibility modes per topic (BACKWARD, FORWARD, FULL) with justification.
- `chaos-engineering` — broker failure and partition loss are not hypothetical; they are weekly events at scale. Default experiments and a quarterly game day keep the muscle warm.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 2 (Design) | Delivery semantics decision explicit in the design doc: exactly-once, at-least-once, or at-most-once, with justification. If at-least-once, idempotency strategy for every consumer documented (dedup key, idempotency window, storage). Backpressure strategy documented: buffer size, shed-vs-block policy, propagation mechanism. Partition key and partition count chosen with a rationale (expected throughput per partition, key cardinality, rebalance cost). If a custom protocol is being designed (custom consensus, ordering, or delivery-semantics logic not covered by Kafka transactions / Flink checkpointing), `formal-verification` begins at Stage 2 — the TLA+ spec must be committed and the TLC model check must pass before implementation of that protocol begins. |
| Stage 3 (Build) | Consumer lag alerts configured per consumer group with explicit thresholds (warn, page). Dead letter queue (or equivalent retry-then-park topic) present for every consumer with a documented replay procedure. Producer acks and idempotence settings pinned in config (`acks=all`, `enable.idempotence=true` for Kafka, or equivalent). Schema registered and compatibility mode set before the first produce. |
| Stage 4 (Verify) | Load test at 2x expected peak throughput with the target consumer topology running — measure end-to-end p99 and consumer lag under load. Broker failure scenario tested: kill the leader of the primary topic's partition and verify no data loss, no duplicates (at exactly-once) or known-bounded duplicates (at-least-once), and recovery within the SLO. Rebalance behaviour verified: a rolling consumer restart must not lose messages or trigger unbounded reprocessing. |
| Stage 5 (Ship) | Rebalance behaviour verified end-to-end in the deployment environment (not just load test). Rollback plan for schema changes documented: how to revert the registry to the previous compatibility, how to roll back the producer and consumer in the right order, how to republish the previous schema if a consumer is stuck. Runbook includes "consumer stuck / lag climbing" and "DLQ drained wrong" entries. |
| Phase 3 (Ongoing) | Weekly consumer lag trend review: lag p50/p99 per consumer group, plotted week-over-week, with an owner named for any group trending up. Monthly topic partition and retention audit: validate partition count against current throughput, retention against storage budget and replay needs, and prune topics with zero consumers. |

Strictest-wins when combined with another track. A Real-time streaming + Fintech product at the Build gate must satisfy both consumer lag alerting and PCI-scope review on the producer path.

### Gate evidence — what "done" looks like

- **Design gate**: one page in the design doc titled "Delivery semantics and backpressure" naming the posture (at-least-once / exactly-once), the idempotency key and its store, the slow-consumer posture (block / buffer / shed), and the partition key with cardinality estimate.
- **Build gate**: alert rules committed to the repo for consumer lag; DLQ topic and replay script committed; producer config with `acks=all`, idempotence, and pinned `transactional.id` (if applicable) reviewed in PR.
- **Verify gate**: load test report with p99 end-to-end and consumer lag under 2x peak; broker-kill experiment log showing no data loss (or bounded, documented duplicates); rolling-restart log showing zero reprocessing beyond the at-least-once bound.
- **Ship gate**: runbook reviewed; schema rollback procedure dry-run at least once in staging; on-call team briefed on rebalance and lag-climbing symptoms.
- **Ongoing**: weekly lag review minutes (one paragraph is fine) and monthly partition/retention audit entry in the skill log.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| distributed-systems-patterns | `references/exactly-once-semantics.md` — idempotent consumers and outbox are foundational for at-least-once; `references/backpressure-patterns.md` for slow-consumer handling |
| performance-reliability-engineering | `references/streaming-platform-selection.md` for throughput/latency ceilings by platform; `references/backpressure-patterns.md` for load-shedding design |
| observability-sre-practice | `references/streaming-platform-selection.md` for per-platform lag metric surfaces; add consumer lag (offset behind head) and throughput to the SLO template — these are non-optional signals for every streaming system |
| specification-driven-development | `references/streaming-platform-selection.md` for AsyncAPI and schema-registry context; `references/windowing-and-watermarks.md` when the contract includes windowed aggregates |
| chaos-engineering | `references/exactly-once-semantics.md` and `references/backpressure-patterns.md` — default experiments are broker failure, partition reassignment, and slow consumer |
| formal-verification | `references/exactly-once-semantics.md` — the TLA+ spec for a custom delivery-semantics protocol should encode the same invariants (no data loss, no unbounded duplicates) that exactly-once-semantics.md defines informally |
| code-implementer (producer/consumer code paths) | `references/exactly-once-semantics.md` for idempotent-consumer patterns and outbox; `references/windowing-and-watermarks.md` for stream-processing code |
| comprehensive-test-strategy | `references/exactly-once-semantics.md` for duplication tests; `references/backpressure-patterns.md` for slow-consumer test scenarios |
| database-migration | `references/exactly-once-semantics.md` for outbox table schema and dedup-store schema; migrations that add or alter these tables must be backward-compatible with in-flight consumers |
| release-readiness | `references/streaming-platform-selection.md` for rebalance and schema-rollback checks; `references/exactly-once-semantics.md` for the schema-rollback ordering |

Reference injection is additive — all applicable references load when a skill fires under this track, on top of the skill's own references and any references injected by other active tracks.

---

## Why these specific gates

The five gate modifications are each calibrated to a class of incident this track has seen teams hit and wants to prevent:

- **Stage 2 delivery-semantics and backpressure**: prevents the "we assumed exactly-once because Kafka said exactly-once" class of bug, and the "traffic spiked and the consumer OOMed because the queue was unbounded" class of outage.
- **Stage 3 lag alerts and DLQ**: prevents silent consumer stalls — a consumer dies, messages pile up, no one notices until a customer reports stale data 6 hours later.
- **Stage 4 load test at 2x and broker failure**: prevents the "shipped on Tuesday, fell over Thursday at peak" outcome and the "broker node died and we lost 40 minutes of data" outcome.
- **Stage 5 rebalance and schema rollback**: prevents the "we deployed and the consumer group rebalanced for 20 minutes" outage and the "schema change broke the old consumers and we could not roll back" outage.
- **Phase 3 lag trend and partition audit**: surfaces slow-burning problems — a consumer group that has been creeping up in lag over weeks, a topic with 10x its original traffic still running on the original 3 partitions.

None of these are theoretical. All have been the subject of a postmortem somewhere. The gates exist so the postmortem does not need to be ours.

---

## Mode-level defaults and typical use

**Nano** — a single small service publishing or consuming events; a hack-week prototype against a broker. The five elevations still apply because skipping them at Nano is how Nano projects graduate to Standard with silent correctness bugs. Nano-level effort here means: distributed-systems-patterns as a one-page idempotency note; observability as "lag is in Grafana"; platform selection as a single paragraph in the README.

**Lean** — most new streaming features on an established platform. AsyncAPI contract required. Chaos is conditional on whether the broker has been exercised in the last quarter.

**Standard** — production backbones, customer-facing streaming features, cross-team pipelines. Per-topic SLOs, capacity planning, broker-failure tests under chaos. This is the default for anything on an SLA.

**Rigorous** — critical-path event backbones, regulated streaming pipelines (payments, clinical telemetry), systems where data loss or a sustained outage has legal or revenue consequences. Soak tests, quarterly game days, per-partition SLOs, pinned schema compatibility modes.

---

## Activation examples

```
"Standard mode, Real-time track — migrate the order events to Kafka with exactly-once"
"Rigorous mode, Fintech + Real-time tracks — payment events backbone with exactly-once end-to-end"
"Lean mode, Real-time + Data platform tracks — CDC from Postgres into Kafka feeding the analytics warehouse"
"Nano mode, Real-time track — experimental Flink job over the existing topic, no production SLO yet"
```

---

## Reference files

- `references/streaming-platform-selection.md` — decision matrix across Kafka, Kinesis, Google Pub/Sub, NATS JetStream, Pulsar, and RabbitMQ Streams covering throughput ceiling, latency, retention model, ecosystem, operational burden, and consumer semantics; when to pick a log-based broker vs a traditional queue; cost profile at low/mid/high scale.
- `references/exactly-once-semantics.md` — what exactly-once actually means (end-to-end vs broker-side), Kafka transactions in detail, the outbox pattern as an alternative, idempotent consumer patterns, cost trade-offs (the throughput hit of transactional semantics), and worked examples with Kafka plus a relational outbox table.
- `references/backpressure-patterns.md` — buffering strategies, load shedding at ingress vs at the consumer, backpressure propagation in reactive systems (Project Reactor, RxJava, Akka), rate limiting vs backpressure, and slow-consumer handling patterns with config-ready examples.
- `references/windowing-and-watermarks.md` — tumbling vs sliding vs session windows, event time vs processing time, watermark generation strategies (heuristic, perfect, per-partition), late data handling (side outputs, allowed lateness), and worked Flink and Kafka Streams examples.

---

## What this track does not do

- It does not pick the broker for you. `references/streaming-platform-selection.md` gives the matrix; the team owns the decision.
- It does not replace `chaos-engineering` — it raises it from Advisory to Mandatory at Standard and names the default experiments (broker failure, partition reassignment, slow consumer). The skill runs; the track tells it what to exercise.
- It does not define SLO targets. `observability-sre-practice` owns SLO definition; this track ensures consumer lag and throughput are first-class in the SLO set and that per-topic SLOs exist at Standard, per-partition at Rigorous.

---

## Track invariants

- Consumer lag is not optional telemetry. Every streaming service ships with lag alerts or it does not ship.
- Every at-least-once consumer is idempotent. The absence of idempotency is a bug, not a tuning decision.
- Every topic with more than one producer has a schema registered in a registry with an explicit compatibility mode. "We'll coordinate on Slack" is not a schema strategy.
- Every streaming system has a documented slow-consumer posture: block, buffer, or shed. "It shouldn't happen" is not a posture.
- Rebalance behaviour is tested before production, not discovered in production.

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: real-time-streaming | mode: <Mode> | duration: project
```

Skill firings under this track append the track context:

```
[YYYY-MM-DD] distributed-systems-patterns | outcome: OK | note: idempotent consumer + outbox pattern implemented | track: real-time-streaming
[YYYY-MM-DD] chaos-engineering | outcome: OK | note: broker-kill experiment passed — no data loss | track: real-time-streaming
```
