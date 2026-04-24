---
name: data-platform-mlops
description: >
  Activates when the user mentions data pipeline, ETL, ELT, data warehouse, data lake,
  schema registry, Avro, Protobuf topic schema, data quality, data contract, "upstream
  broke us", ML model, model training, model versioning, MLflow, Weights & Biases,
  feature store, offline/online parity, LLM production, RAG pipeline, or prompt eval
  in CI. Also triggers on explicit declaration: "Data platform track" or "ML ops track".
---

# Data platform / ML ops track

## Purpose

This track covers products where the data itself is the deliverable: ingestion pipelines, warehouses and lakes, feature stores, ML training and serving, LLM-backed features in production, and any system where a downstream consumer depends on schema stability and freshness. These systems fail differently from request-response services. Upstream schema drift silently corrupts a week of analytics before anyone notices. A feature pipeline's offline logic diverges from its online counterpart and model accuracy collapses in production while offline metrics stay green. A model is swapped without a rollback plan and the challenger underperforms on a cohort nobody tested. An LLM prompt is tweaked, the change ships, and a class of user queries regresses for weeks because nobody ran the eval suite.

The standard 41 skills plus a mode setting do not enforce data contracts, schema evolution discipline, data-quality SLOs, model versioning, or training-serving parity. This track elevates those from optional to load-bearing and tightens stage gates so a data or ML build cannot ship without them. The core insight: in a data platform, the contract between producer and consumer is the system. Without it, every change is a guess.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "data pipeline", "ETL", "ELT", "data warehouse", "data lake", "lakehouse", "medallion architecture", "bronze/silver/gold"
- "schema registry", "Avro", "Protobuf", "topic schema", "schema evolution", "backward compatible", "forward compatible"
- "data quality", "data contract", "producer spec", "upstream broke us", "silent failure", "dbt tests", "Great Expectations", "Soda"
- "ML model", "model training", "model serving", "model versioning", "MLflow", "Vertex AI", "SageMaker", "Weights & Biases"
- "feature store", "Feast", "Tecton", "Databricks Feature Store", "offline/online parity", "training-serving skew", "point-in-time correctness"
- "LLM in production", "RAG pipeline", "prompt eval in CI", "eval regression", "model drift", "concept drift"

Or when the system under discussion has these properties:

- A producer service emits events or rows that at least one analytics consumer, ML training job, or downstream service depends on.
- A schema evolves over time and consumers need backward-compatibility guarantees.
- A model, prompt, or feature pipeline is deployed to production and its behaviour must be monitored for drift.
- The system has a feature store, a model registry, or a scheduled retraining job.
- Freshness, completeness, or uniqueness of a dataset is business-critical.
- Training data and serving data pass through different code paths — the classic training-serving skew setup.
- The team has ever said "the numbers don't match" or "the upstream broke us" in a retro.

---

## When NOT to activate

Do NOT activate this track when:

- The work is a single database query or one-off analytical report with no pipeline and no downstream consumer.
- The LLM feature is an isolated one-shot call (chat widget, single completion) with no retrieval, no eval suite, and no production SLO — `llm-app-development` as a standalone skill is sufficient.
- The "data pipeline" is an internal admin export that runs manually and no one depends on.
- You are instrumenting product analytics for growth experiments — that is the Consumer product track's event taxonomy work, not a data platform.
- You are designing a streaming broker topology with low-latency and exactly-once concerns only — use the Real-time / streaming track instead (the two compose if you are building a streaming data platform with ML inference on top).
- You are doing exploratory analysis in a notebook with no deployment target — standard mode with no track is sufficient until the work starts landing in a scheduled pipeline.

If you are unsure, answer this: if the schema of one of your outputs changes silently, does a downstream consumer break? If yes, activate. If no, don't.

If you are building both a streaming platform *and* a data/ML platform on top of it (Kafka feeding Flink feeding a feature store feeding a model), activate both the Real-time / streaming track and this track. They compose additively.

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| specification-driven-development | Standard | Mandatory (data contracts) | Mandatory (data contracts) | Mandatory + schema registry |
| comprehensive-test-strategy | Standard | Standard + data quality tests | Standard + data quality + contract tests | + ML model evaluation gates |
| llm-app-development | Conditional | Conditional | Mandatory if LLM present | Mandatory + eval regression gate |
| distributed-systems-patterns | Advisory | Mandatory (outbox, idempotency for replay) | Mandatory | Mandatory |
| observability-sre-practice | Standard | Data freshness SLOs | Data freshness + quality SLOs | + model drift detection |
| architecture-fitness | Conditional | Mandatory for module boundaries | Mandatory | Mandatory |
| cloud-cost-governance | N/A | Advisory | Mandatory (compute cost attribution per pipeline and model required) | Mandatory |

Only skills whose treatment differs from the default mode behaviour are listed. All other skills retain their mode defaults.

Notes on the additional elevation:

- `cloud-cost-governance` at Standard+ reflects the reality that compute cost is the dominant cost driver in data platform and ML systems — training jobs, feature pipelines, and model serving can each individually dwarf the cost of every other engineering decision in the system. Without per-pipeline and per-model cost attribution, teams cannot make rational decisions about training frequency, feature freshness, or model complexity. This elevation requires that every new pipeline or model promotion includes a cost estimate and that monthly cost review is part of the platform's operational cadence.

Notes on the elevations:

- **specification-driven-development** is the foundation. A data contract *is* the spec for a pipeline, the same way an OpenAPI document is the spec for an HTTP service. In Rigorous mode, the contract is backed by a schema registry with enforced compatibility — not just a YAML file in a repo.
- **comprehensive-test-strategy** adds a new axis. The standard test pyramid (unit / integration / e2e) still applies to pipeline code. Data quality tests are orthogonal — they assert properties of the output dataset itself, not of the code that produced it. Both run in CI; the data quality tests also run in the scheduled pipeline.
- **llm-app-development** elevates from conditional to mandatory when an LLM is in the critical path. The Rigorous addition is an eval regression gate: CI runs the eval suite and blocks merge if quality regresses on the pinned eval set.
- **distributed-systems-patterns** becomes mandatory because replay safety, outbox, and idempotent consumers are the difference between a pipeline you can rerun and one you cannot.
- **observability-sre-practice** gets freshness and quality SLOs added to the standard service SLOs. Drift detection is a Rigorous-mode addition for any ML or LLM system.
- **architecture-fitness** guards the offline/online boundary in feature pipelines — the boundary where training-serving skew is born.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 2 (Design) | Data contract required: producer guarantees (schema, freshness SLA, uniqueness keys, ordering guarantees) and consumer expectations (tolerated staleness, required fields, breakage-notification window) documented in the design doc. Schema evolution plan: which compatibility mode the registry enforces (BACKWARD by default for consumers) and the policy for breaking changes. |
| Stage 3 (Build) | Data quality tests required for every published dataset or topic. Minimum coverage: uniqueness on the primary key, freshness against the stated SLA, completeness on required columns, referential integrity against upstream dimension tables. Tests run in CI and in the scheduled pipeline — not only at build time. |
| Stage 4 (Verify) | Backfill test scenario: the pipeline must be re-runnable over a historical window without producing duplicates or missing rows. For ML features, offline/online parity check: the training pipeline's feature values and the serving path's feature values must match for a pinned reference set within a defined tolerance. |
| Stage 5 (Ship) | Data breakage SLA to downstream consumers declared: how quickly you notify on breakage, how quickly you restore, what compensation you offer (credits, re-runs, or just an apology for internal consumers). Rollback plan for schema changes documented: how to revert registry compatibility, how to republish the previous contract, how to roll back the producer and consumer in the right order. |
| Phase 3 (Ongoing) | Monthly data quality report: SLO attainment per dataset, incident list, trend on freshness and completeness. Model drift monitoring: input distribution drift, prediction distribution drift, ground-truth performance where available. Eval suite run weekly with trend reporting for any LLM or ML system in production. Quarterly review of the contract list — deprecate unused contracts, flag stale consumers. |

Strictest-wins when combined with another track. A Data platform + Healthcare product at the Build gate must satisfy both data quality tests and HIPAA audit-log tests. A Data platform + Fintech product at the Verify gate must satisfy backfill scenarios and reconciliation scenarios. A Data platform + Real-time streaming product at the Design gate must document both the data contract and the exactly-once vs at-least-once decision.

The single most common gate failure in this track is a missing backfill plan at Stage 4. Pipelines that have never been re-run from history are one schema change away from an unrecoverable incident — rehearse the backfill before you ship, not after.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| specification-driven-development | `references/data-contracts.md`, `references/schema-registry-design.md` |
| llm-app-development | `references/model-versioning.md`; `references/data-quality-framework.md` — eval regression detection is a quality-gate problem; the data-quality SLO framework applies to eval results as quality signals |
| comprehensive-test-strategy | `references/data-quality-framework.md` — data quality tests are additive to the standard test pyramid, not a replacement |
| code-implementer (pipeline code paths) | `references/data-contracts.md` for producer-side contract enforcement; `references/feature-store-patterns.md` for feature pipeline code |
| observability-sre-practice | `references/data-quality-framework.md` for freshness and quality SLO definitions; `references/model-versioning.md` for drift detection metrics |
| architecture-fitness | `references/feature-store-patterns.md` for offline/online module boundary rules |
| design-doc-generator | `references/data-contracts.md` and `references/schema-registry-design.md` — design docs for data systems must include both |
| api-contract-enforcer | `references/schema-registry-design.md` — schema registry compatibility is the data-world analogue of API contract enforcement |

---

## Reference files

- `references/data-contracts.md` — what a data contract is, its shape (producer spec, consumer spec, SLA, schema, evolution policy), tooling notes (Gable, dbt contracts, Kafka Schema Registry), versioning rules, and a worked `events.user_signup` example with schema, freshness SLA, backward-compatibility commitment, and a consumer registration. Use this when designing a new published dataset or topic, or when reviewing a proposed schema change.
- `references/schema-registry-design.md` — schema registry patterns, BACKWARD / FORWARD / FULL / NONE compatibility modes and when each is right, schema evolution plan, serialization format choice (Avro vs Protobuf vs JSON Schema) with a trade-off table, and a migration strategy when compatibility must break. Use this when picking a serialization format, choosing a compatibility mode, or planning a breaking-change migration.
- `references/data-quality-framework.md` — data quality dimensions (freshness, completeness, uniqueness, referential integrity, timeliness, conformance), tooling (Great Expectations, dbt tests, Soda), per-dataset quality SLOs, alerting on quality failures, and a worked example with a dbt test file and a GX suite. Use this when writing tests for a new dataset, designing SLO dashboards, or wiring quality alerts.
- `references/model-versioning.md` — versioning ML models in production, champion/challenger pattern, canary rollout, rollback mechanics, model registry options (MLflow, Vertex AI Model Registry, SageMaker Model Registry), offline vs online eval, shadow deployment, and concrete MLflow and Vertex examples. Use this when promoting a model to production, planning a rollout, or writing a rollback runbook.
- `references/feature-store-patterns.md` — online vs offline feature stores, tooling (Feast, Tecton, Databricks Feature Store), training-serving skew prevention, feature freshness SLOs, point-in-time correctness for training datasets, and backfill strategies. Use this when designing a feature pipeline, adding a new feature, or investigating a training-serving skew incident.

---

## Activation example

```
"Standard mode, Data platform / ML ops track — we're building a user-churn model backed by a Feast feature store, training weekly on the warehouse, serving from an online store."
```

Triggers:
- `specification-driven-development` elevates to mandatory with data contracts for the warehouse source tables and the feature views.
- `comprehensive-test-strategy` adds data quality tests at the landing zone and at the feature-view layer.
- `distributed-systems-patterns` is mandatory — idempotent writes into the online store and replay-safe training jobs.
- `observability-sre-practice` wires freshness SLOs on the feature views and drift detection on the model inputs.
- Stage 4 gate requires the backfill scenario and the offline/online parity check before shipping.
- Phase 3 schedules the monthly data-quality report and the weekly eval run.

The contract files, quality tests, model registration, and rollout plan are the artifacts produced; the stage gates check they exist before letting the pipeline advance.

---

## Anti-patterns this track exists to prevent

- **Schemas in wikis.** Documented-not-enforced schemas rot within weeks. The registry is the source of truth; the wiki is a mirror, at best.
- **Tests that only run at build time.** A data quality test that doesn't run in the scheduled pipeline is a vanity check.
- **Models without registries.** "It's in the ops/ folder on S3" is not a model registry. Lineage, metrics, and stage transitions cannot be reconstructed from a folder.
- **Offline-only eval.** Offline metrics that keep going up while online metrics stagnate or regress is the classic ML production trap.
- **One-way schema changes.** A migration plan that cannot be reversed is not a migration plan.
- **Prompts edited directly in production config.** A prompt change is a model change. Version it, eval it, roll it back just like code.
- **Feature logic duplicated across training and serving.** One definition, two consumers — not the reverse. See `references/feature-store-patterns.md`.
- **"The pipeline is the backfill."** If you've never re-run the pipeline over a historical window, you don't know that you can.

---

## Skill execution log

This track's activation appends to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: data-platform-mlops | mode: <Mode> | duration: project
```

Skill firings under this track carry the track context on the same line, e.g.:

```
[YYYY-MM-DD] specification-driven-development | outcome: OK | next: design-doc-generator | note: data contract drafted for events.user_signup | track: data-platform-mlops
```

The log is the audit trail for the track; it lets a returning engineer see which contracts were created, which quality tests were added, and which model rollouts happened without digging through commit history.

---

## Composition notes

- **Data platform + Real-time / streaming**: the streaming track's exactly-once and watermarking concerns compose with this track's contract and quality concerns. Design docs at Stage 2 must cover both axes.
- **Data platform + Fintech**: reconciliation (Fintech) and backfill (Data) share DNA — both are about making the internal ledger match an external or historical truth. At Stage 4, both scenarios must be tested.
- **Data platform + Healthcare**: PHI classification applies to every field in every contract. The data contract's schema section must mark PHI fields explicitly; quality tests must not log PHI in failure messages.
- **Data platform + Regulated / government**: evidence collection applies — every contract, every quality test result, every model promotion is evidence that feeds the audit trail under `docs/evidence/`.
