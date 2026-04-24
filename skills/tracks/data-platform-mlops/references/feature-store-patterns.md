# Feature store patterns

A feature store is a managed system for computing, storing, and serving features for ML — both for training (offline) and for inference (online). The core problem it solves is **training-serving skew**: the features a model saw during training must match the features it sees at inference, or the model's performance collapses. Without a feature store, the same feature logic lives in two places (a SQL transform for training, a service method for serving) and drifts. With one, feature logic has a single definition and is served consistently.

This document covers online vs offline stores, tooling, training-serving skew prevention, feature freshness SLOs, point-in-time correctness, and backfill strategies.

---

## Online vs offline stores

Every feature has two lives.

### Offline store

- **Purpose**: training datasets and batch scoring.
- **Storage**: warehouse (BigQuery, Snowflake, Redshift) or data lake (Parquet on S3 / GCS).
- **Latency**: seconds to minutes per query acceptable.
- **Volume**: full history of every feature, indexed by entity + timestamp.
- **Access pattern**: "give me feature values for 1M user_ids as of the timestamps in this training dataset."

### Online store

- **Purpose**: low-latency serving at inference time.
- **Storage**: key-value store (Redis, DynamoDB, Bigtable, Cassandra).
- **Latency**: single-digit milliseconds per lookup, p99 < 10ms.
- **Volume**: latest value per entity only (not history).
- **Access pattern**: "give me the current feature values for this single user_id."

The feature store's job is to keep both stores consistent: the same feature, computed by the same code, landed in both.

---

## Tooling

| Tool | Hosting | Strengths | Weaknesses |
|------|---------|-----------|------------|
| **Feast** | Open-source, self-hosted | Lightweight; declarative feature definitions; pluggable online/offline stores | You run it; no managed UI in OSS |
| **Tecton** | Managed | Full feature engineering platform; streaming features first-class; lineage tracking | Cost; vendor lock |
| **Databricks Feature Store** | Part of Databricks | Tight integration with Databricks / Unity Catalog / MLflow | Databricks-only |
| **SageMaker Feature Store** | AWS-managed | Tight AWS integration; offline to Parquet on S3, online to DynamoDB | AWS-only |
| **Vertex AI Feature Store** | GCP-managed | Tight GCP integration; online serving | GCP-only |

For a 3-5 person team: Feast if you're cloud-agnostic or on a mixed stack; the cloud-native store if you're all-in on one cloud; Tecton only if you need serious streaming feature infrastructure and can afford it.

---

## Training-serving skew prevention

Skew is the single largest cause of ML production bugs. It comes from five places. Prevent each.

### 1. Duplicated feature logic

Classic version: the data scientist writes a SQL query to compute `user_avg_order_value` for training. The engineer writes a Python method on the user service to compute the same feature for serving. One gets updated; the other doesn't. Model accuracy drops.

**Fix**: one definition, consumed by both paths. In Feast:

```python
from feast import Entity, Feature, FeatureView, Field
from feast.types import Float32, Int64
from datetime import timedelta

user = Entity(name="user_id", value_type=ValueType.STRING)

user_order_stats = FeatureView(
    name="user_order_stats",
    entities=["user_id"],
    ttl=timedelta(days=7),
    schema=[
        Field(name="avg_order_value_30d", dtype=Float32),
        Field(name="order_count_30d", dtype=Int64),
        Field(name="days_since_last_order", dtype=Int64),
    ],
    source=BigQuerySource(
        table="analytics.user_order_stats_daily",
        timestamp_field="as_of_date",
    ),
)
```

The same `FeatureView` definition produces training data (via `get_historical_features`) and serving data (via `get_online_features`). One source of truth.

### 2. Different time semantics

Training uses a label timestamp; serving uses "now." A feature computed from "user's last 7 days" means different rolling windows in training vs serving if the join keys aren't aligned to the prediction timestamp.

**Fix**: point-in-time correctness (see below). The feature store joins features to entities using the prediction timestamp, not the current time.

### 3. Feature freshness mismatch

At training, the feature was computed from a nightly batch that ran at 04:00. At serving, the feature is looked up and it's 10:00 — the feature is 6 hours old. If the feature changes meaningfully within 6 hours, this is skew.

**Fix**: an explicit **feature freshness SLO** per feature. If the feature must be fresh within 5 minutes, it must be computed by a streaming job, not a nightly batch. Documented, monitored, alerted.

### 4. Preprocessing drift

The training pipeline applies log-transform to a feature. The serving code forgot to apply it. Model sees raw values at inference; accuracy tanks.

**Fix**: all preprocessing inside the feature definition. The feature store emits the transformed value. Serving code never transforms again.

### 5. Silent type changes

A feature was `int32` in training; an upstream schema drift made it `int64`. Serving cast it back to `int32` and silently overflowed on a small number of rows.

**Fix**: schema enforcement at the feature store boundary. Type changes are contract breaks.

---

## Feature freshness SLOs

Every feature has a freshness SLO. Features are categorized by how quickly their values must reflect reality:

| Freshness class | SLO | Computation pattern |
|-----------------|-----|---------------------|
| **Real-time** | p99 < 1 minute | Streaming (Flink, Kafka Streams, Materialize) writing to online store |
| **Near-real-time** | p99 < 15 minutes | Micro-batch (every 5 min) or CDC |
| **Hourly** | p99 < 1 hour | Scheduled hourly batch |
| **Daily** | p99 < 24 hours | Nightly batch; good enough for slow-moving features |

Match the freshness class to the model's sensitivity. A fraud model that scores a transaction needs real-time fraud signals. A content recommender based on long-term interests can tolerate daily refresh.

Monitoring:
- Max timestamp per feature vs wall clock, logged per online store lookup.
- Alert when max-lag exceeds SLO for N consecutive minutes.
- Part of `observability-sre-practice`'s elevated data-freshness SLOs in this track.

---

## Point-in-time correctness for training datasets

The canonical training-set bug: you train a model on today's user feature values labelled against last year's events. At serving time, the model sees today's features for today's events — but at training it saw today's features for last year's events. This is **label leakage through time**. The model memorizes something that isn't really predictable.

Point-in-time (PIT) correctness means: for each training example, look up the feature values **as they were at the label timestamp**. Feast and Tecton both do this natively.

### PIT join — example

Training set: `(user_id, purchase_timestamp, purchased_bool)`. Add `avg_order_value_30d`.

Naive (wrong):

```sql
SELECT t.*, f.avg_order_value_30d
FROM training_events t
LEFT JOIN user_order_stats f ON t.user_id = f.user_id
-- leaks: f.as_of_date is today, not purchase_timestamp
```

Correct (Feast PIT):

```python
training_df = feature_store.get_historical_features(
    entity_df=training_events,     # must include user_id and event_timestamp
    features=["user_order_stats:avg_order_value_30d",
              "user_order_stats:order_count_30d"],
).to_df()
```

Under the hood, the feature store issues a temporal join: for each row, fetch the feature's value at the greatest `as_of_date <= event_timestamp`. No leakage.

---

## Backfill strategies

A new feature needs historical values before it can be used in training. Two strategies:

**Backfill from existing raw data** — re-run the transformation over full history. Complete coverage; expensive. Chunk the job by date range to fit memory and resume on failure. Write to the offline store only (the online store holds current values). Ensure idempotency via `MERGE` / key-based upsert so re-runs do not double-insert.

**Start fresh** — feature begins emitting from the day it is defined; past training data uses null or a sentinel. Cheap; model cannot use the feature until enough history accrues.

Default: backfill when feasible. Start-fresh only for genuinely new features or when backfill is prohibitively expensive.

**Backfill correctness**: treat the backfill job as code — reviewed, tested, versioned. After completion, compare backfilled values against live values for the last N days of overlap; they must match within tolerance. Log in feature metadata: `backfill_completed: 2026-04-15, chunks: 18, rows: 2.4B`.

---

## Streaming features — the edge case

Features computed from streams (e.g., "number of clicks in the last 5 minutes") cannot be fully backfilled from a batch — the stream defines the feature. Two approaches:

1. **Replay the historical stream** from retained logs (Kafka compacted topic, Kinesis retention). Works if retention is long enough. Often it isn't.
2. **Approximate from batch** for historical periods; use streaming from now. Clearly label the boundary; models trained across the boundary may have drift at the cutover.

Document the approach and the cutover. `feature_store:backfill_notes` is a first-class metadata field for this reason.

---

## Quick checklist per new feature

- [ ] Defined once in the feature store, consumed by both training and serving paths.
- [ ] Freshness class assigned (real-time / near-real-time / hourly / daily) and matched to the model's sensitivity.
- [ ] PIT-correct training join verified on a sample.
- [ ] Backfill strategy chosen; if backfilled, sanity-checked against live.
- [ ] Online store freshness monitored; alert on SLO breach.
- [ ] Feature schema versioned; type changes go through the contract process.
- [ ] Offline/online parity check in the Stage 4 gate covers this feature.
