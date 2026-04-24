# Streaming platform selection

Choose the broker first, not the stream processor. The broker decision constrains throughput, retention, delivery semantics, ecosystem, and operational burden for the life of the system. The stream processor can be swapped; the broker usually cannot.

---

## Decision matrix

| Dimension | Kafka (OSS / MSK / Confluent) | AWS Kinesis Data Streams | Google Pub/Sub | NATS JetStream | Apache Pulsar | RabbitMQ Streams |
|-----------|-------------------------------|--------------------------|----------------|----------------|---------------|------------------|
| Model | Partitioned log | Partitioned (shard) log | Queue with replay (7 days) | Subject-based log + KV | Segmented log with tiered storage | Log (stream) alongside classic queues |
| Max sustained throughput | 10s of GB/s per cluster; 10k+ MB/s per broker | 1 MB/s or 1000 rec/s write per shard; scale via shards | Effectively unlimited (managed); per-subscription quotas apply | ~1 GB/s per stream; horizontal via clustering | 10s of GB/s; BookKeeper-backed, tiered to object store | Order of 1 MB/s per stream; not designed for extreme scale |
| p99 end-to-end latency | 5–50 ms tuned; 100+ ms default | 70–200 ms typical | 50–200 ms typical | 1–10 ms tuned | 5–50 ms tuned | 5–20 ms tuned |
| Retention | Time and size; unbounded if configured; tiered storage in Confluent | 24 h default, up to 365 days | 7 days max replay | Time, size, or message count; file or in-memory | Time, size, tiered to S3/GCS indefinitely | Time and size |
| Delivery semantics | At-least-once default; exactly-once via transactions + idempotent producer | At-least-once; exactly-once requires app-level dedup | At-least-once; exactly-once for Dataflow sinks only | At-least-once; exactly-once via per-message dedup window | At-least-once; exactly-once via transactions | At-least-once; publisher confirms + consumer acks |
| Ordering | Per partition | Per shard | Per ordering key (best-effort cross-region) | Per subject/stream | Per partition (Key_Shared subscription preserves key order) | Per stream |
| Consumer model | Pull, consumer groups with partition assignment | Pull via KCL; shard-level checkpointing | Push or pull; server-managed subscription | Pull or push; consumer groups | Pull or push; Shared / Key_Shared / Failover / Exclusive | Pull with offset tracking |
| Schema / contract | Confluent Schema Registry (Avro/Protobuf/JSON) | Glue Schema Registry | Pub/Sub Schema service (Avro/Protobuf) | No native registry; app-level | Built-in schema registry (Avro/Protobuf/JSON/Keyvalue) | No native registry |
| Ecosystem | Deepest — Kafka Connect, Streams, ksqlDB, Flink, Spark, every language client | AWS-native; Kinesis Client Library + Firehose + Analytics | GCP-native; Dataflow integration is first-class | Small but growing; NATS ecosystem | Connectors, Functions, Flink integration | RabbitMQ ecosystem; limited streams tooling |
| Operational burden (self-hosted) | High — JVM, ZooKeeper or KRaft, disks, rebalance tuning | N/A (managed only) | N/A (managed only) | Low — single Go binary, clustering is simple | High — Broker + BookKeeper + ZooKeeper | Medium — Erlang, disks, clustering |
| Operational burden (managed) | Low with MSK/Confluent Cloud | Low | Lowest (fully managed, auto-scaling) | Low with Synadia Cloud | Medium with StreamNative; fewer vendors | Low with CloudAMQP |
| Consumer rebalance cost | High — stop-the-world per group unless cooperative rebalancing enabled | Low — checkpointed per shard | None — server-managed | Low | Low for Shared; medium for Key_Shared | Low |
| Multi-tenancy | Weak (ACLs only; no native namespace) | Account/stream boundary | Project boundary | Accounts + subjects | Native tenants and namespaces | vhosts |

---

## Log-based broker vs traditional queue

Pick a **log-based broker** (Kafka, Kinesis, Pulsar, NATS JetStream, Pub/Sub) when:

- Multiple independent consumer groups must read the same stream at different positions.
- Replay from an earlier offset is a legitimate recovery strategy.
- Retention is measured in hours, days, or weeks — not "until acknowledged".
- Throughput exceeds roughly 10k messages per second sustained.
- A stream processor (Flink, Kafka Streams) reads the topic and produces derived streams.
- Event sourcing, CDC, or materialized-view patterns are in play.

Pick a **traditional queue** (RabbitMQ classic, SQS, ActiveMQ) when:

- One producer, one logical consumer group, work-queue semantics (competing consumers).
- Messages are work items, not events — consumed once and then gone.
- Retention is "until acked" and dead-letter on failure.
- Throughput is modest (under 10k msg/s) and latency requirement is not sub-50 ms.
- You need per-message TTL, priority queues, or complex routing topologies.

The cost of picking wrong: a queue where a log belongs means no replay and no multi-consumer fan-out; a log where a queue belongs means retention cost and operational complexity for a problem that SQS would have solved in an afternoon.

---

## Cost profile by scale

### Low scale — under 1 MB/s sustained, under 100k msg/s

Managed offerings dominate. Self-hosting Kafka or Pulsar at this scale is almost always a mistake — operational cost exceeds service cost by 10x.

- **Pub/Sub**: ~$40/TB ingress; pay-per-message. Best for low-traffic, multi-project setups.
- **Kinesis**: on-demand mode $0.04/GB ingress + $0.04/GB egress. Simple pricing, no shard math.
- **Confluent Cloud Basic**: ~$1/hour cluster + $0.11/GB ingress. Familiar to Kafka teams.
- **NATS (Synadia Cloud)**: free tier sustains most low-scale use; paid tiers start ~$20/month.

### Mid scale — 1–100 MB/s sustained, 100k–1M msg/s

Managed is still usually right. Shard/partition planning starts to matter.

- **MSK provisioned**: ~$0.10/hr per broker + storage. 3-node m5.large cluster ~$220/month plus EBS.
- **Confluent Cloud Standard**: $1.50/hour + $0.11/GB. Includes multi-AZ, schema registry.
- **Kinesis provisioned**: $0.015/shard-hour + $0.014/million PUT. Shard count = ceil(peak MB/s). At 50 MB/s that is 50 shards = ~$540/month before PUT charges.
- **Pub/Sub**: scales linearly; cost becomes a concern above ~10 TB/month.

### High scale — 100+ MB/s sustained, 1M+ msg/s

Self-hosting Kafka or Pulsar on reserved compute becomes cost-competitive, but only if you have the operational expertise and a 24/7 on-call rotation. Otherwise stay managed and negotiate.

- **Self-hosted Kafka on EC2**: ~$0.02/GB at a fully-loaded cluster (compute + EBS + cross-AZ transfer) vs $0.11/GB on Confluent Cloud. Breakeven around 50 TB/month if you have a dedicated streaming team.
- **Pulsar with tiered storage**: cheap long-term retention by spilling to S3/GCS. Can be 30–50% cheaper than Kafka at high retention.
- **Kinesis**: cost scales linearly with shards; at 1 GB/s (~1000 shards) you are at $10k+/month in shard fees alone. Switch to on-demand if traffic is spiky; stay provisioned if steady.

Cross-AZ transfer is the hidden killer at scale. Rack-aware partition placement (Kafka) or single-AZ deployment (with cross-region DR) can cut bandwidth cost by half.

---

## Per-platform notes

### Kafka

The default choice at mid-to-high scale, with the richest ecosystem (Connect, Streams, ksqlDB, Flink integration, every language client). Strengths: unbounded retention, exactly-once via transactions, mature tooling, large operator talent pool. Weaknesses: operational complexity if self-hosted; ZooKeeper (or KRaft in modern versions) adds a coordination layer; rebalance storms are a real failure mode if cooperative rebalancing is not enabled.

Pick managed (MSK, Confluent Cloud, Aiven) by default. Self-host only with a dedicated streaming team and a clear cost justification. Rack-aware partition placement and `min.insync.replicas=2` with `replication.factor=3` are the safe defaults for durability.

### AWS Kinesis Data Streams

AWS-native, minimal ops, but shard-based capacity model requires explicit planning. Each shard caps at 1 MB/s or 1000 records/s in, 2 MB/s out; scaling means resharding, which is online but not instant. On-demand mode removes shard math at the cost of ~20% higher per-GB price. 24-hour default retention extends to 365 days at extra cost.

Kinesis Client Library (KCL) handles shard checkpointing and failover; the library is Java-first with wrappers for other languages. Firehose for S3/Redshift sinks is the path of least resistance for batch-oriented consumers.

### Google Pub/Sub

Fully managed, auto-scaling, no capacity planning, no shard or partition concept exposed to the developer. The simplest streaming platform to operate. Retention capped at 7 days; no replay beyond that. Ordering is per ordering key (opt-in) and best-effort across regions. Dataflow integration is first-class and provides exactly-once sinks.

Pub/Sub is the right default for GCP-native orgs that do not need >7-day replay and do not need the Kafka ecosystem. It is the wrong default when long retention or ecosystem richness matters.

### NATS JetStream

Lightweight (single Go binary), low latency (1–10 ms p99 tuned), subject-based routing, clustering built in. Strengths: simple ops, sub-10ms latency, polyglot clients, IoT-friendly with JWT auth per subject. Weaknesses: smaller ecosystem than Kafka; fewer connectors; fewer operators have deep experience.

Strong fit for microservice event buses with tight latency budgets, edge/IoT deployments, and teams that want log-based semantics without the Kafka operational burden.

### Apache Pulsar

Log-based with tiered storage (spills to S3/GCS for long retention), native multi-tenancy, flexible subscription models (Shared, Key_Shared, Failover, Exclusive). Strengths: cheap long-term retention, native tenants, geo-replication built in. Weaknesses: three-component architecture (Broker + BookKeeper + ZooKeeper) is operationally heavy; smaller managed-vendor ecosystem; fewer operators with deep experience.

Pick Pulsar when multi-tenancy or long tiered retention is a hard requirement. Otherwise Kafka is the safer call.

### RabbitMQ Streams

Streams alongside classic queues in the same broker — attractive for teams already on RabbitMQ who want log semantics for one or two use cases without a platform migration. Strengths: familiar ops, same broker as existing queues, Erlang reliability. Weaknesses: not designed for extreme scale (order of MB/s per stream); smaller streaming tooling ecosystem.

Pick RabbitMQ Streams for incremental adoption on an existing RabbitMQ fleet. Do not pick it as the foundation of a new high-scale streaming platform.

---

## Schema registry pairing

Broker choice constrains registry choice:

- **Kafka** — Confluent Schema Registry (OSS or Confluent Cloud), AWS Glue Schema Registry, or Apicurio. Supports Avro, Protobuf, JSON Schema with compatibility modes.
- **Kinesis** — AWS Glue Schema Registry integrates natively with KCL and KPL.
- **Pub/Sub** — Pub/Sub Schema service, Avro and Protobuf, compatibility enforced server-side at publish.
- **Pulsar** — built-in schema registry, supports Avro/Protobuf/JSON/KeyValue.
- **NATS / RabbitMQ** — no native registry; use Apicurio or an external registry with app-level enforcement.

A registry is mandatory in this track at Standard and above. Payload format without a registry is technical debt with a delivery date.

---

## Decision shortcuts

- **AWS-native org, moderate scale, want simplicity** → Kinesis Data Streams on-demand.
- **GCP-native org, any scale** → Pub/Sub unless you need replay beyond 7 days.
- **Cross-cloud or on-prem, need the richest ecosystem** → Kafka (MSK, Confluent Cloud, or self-hosted).
- **Sub-10ms p99 latency across services, modest scale** → NATS JetStream.
- **Geo-replicated multi-tenant platform with tiered storage** → Pulsar.
- **Existing RabbitMQ fleet, want streams for one new use case** → RabbitMQ Streams, but plan migration to Kafka if the streaming footprint grows.
- **Team has zero streaming experience** → managed (Pub/Sub, Kinesis on-demand, Confluent Cloud Basic). Do not self-host Kafka as your first streaming system.

---

## Operational realities that drive the decision

- **Team size and expertise**: a 3-person team cannot operate a self-hosted Kafka cluster under an SLA without one engineer effectively becoming a full-time Kafka operator. Managed is almost always correct under five engineers.
- **Existing cloud commitment**: egress costs dominate at scale. Pub/Sub in GCP, Kinesis in AWS, and Event Hubs in Azure remove cross-cloud egress from the calculus. Cross-cloud Kafka is expensive if you did not plan for it.
- **Retention as disaster recovery**: if your recovery plan is "replay the last 24 hours", Kinesis default is fine. If it is "replay the last week", pay for extended retention or use Kafka. If it is "replay the last month", use Pulsar with tiered storage or Kafka with tiered storage on Confluent.
- **Language ecosystem**: Kafka has first-class clients in every language that matters. Pulsar is solid in Java/Go/Python, thinner in Ruby/PHP. NATS is polyglot. Kinesis is Java-first with KCL; other languages work but with fewer examples and sharper edges.
- **Compliance**: HIPAA/PCI/SOC 2 posture differs by managed provider. Confluent Cloud, MSK, and Pub/Sub all have compliance attestations; self-hosted means inheriting the audit cost. This is a track-composition consideration: Real-time + Fintech or Real-time + Healthcare narrows managed options fast.

---

## Anti-patterns to reject

- "We'll use Kafka because Netflix does." Netflix operates a dedicated streaming platform team. If you do not, buy managed or pick a simpler broker.
- "We'll self-host Kafka on Kubernetes to save money." At mid scale the engineering cost exceeds the license savings. Revisit at high scale only.
- Using Kinesis with default 24-hour retention then discovering a consumer was down for 26 hours. Always set retention against your worst-case consumer outage, not your happy path.
- Picking Pub/Sub then needing 30-day replay. Pub/Sub caps at 7 days; you will be rebuilding on Kafka or BigQuery in six months.
- Using RabbitMQ classic queues for event streaming with dozens of consumer groups. RabbitMQ Streams exists for a reason; classic queues are not logs.

---

## What to document in the design doc

For every streaming system, the design doc records:

1. **Broker choice** with a one-paragraph justification against this matrix.
2. **Expected throughput** at launch, in 6 months, in 2 years — peak and sustained.
3. **Retention** target and the rationale (replay window, compliance, storage budget).
4. **Partition / shard count** at launch with a scale-up plan.
5. **Managed vs self-hosted** decision with the operational cost rationale.
6. **Cost estimate** at launch and at 10x launch.

If any of these is unknown, the design is not ready to leave Stage 2.
