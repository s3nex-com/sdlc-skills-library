# Model versioning

A production model is code + weights + preprocessing + input-distribution assumptions. All four change over time. Without versioning, you cannot roll back, reproduce yesterday's predictions, or tell a challenger's wins from random noise. This document covers the model registry, versioning rules, rollout patterns (champion/challenger, canary, shadow), rollback, and offline vs online evaluation, with MLflow and Vertex AI examples.

---

## The model registry

A model registry stores every version of every trained model along with its metadata, metrics, artifacts, and stage (dev / staging / production / archived). Three mainstream options:

| Registry | Best for | Strengths | Weaknesses |
|----------|----------|-----------|------------|
| **MLflow Model Registry** | Open-source, cloud-agnostic | Simple, widely adopted, integrates with any training framework | Self-hosted or Databricks-managed; no built-in serving |
| **Vertex AI Model Registry** | GCP-native stacks | Integrates with Vertex endpoints, monitoring, pipelines | GCP-only |
| **SageMaker Model Registry** | AWS-native stacks | Integrates with SageMaker endpoints, pipelines, monitoring | AWS-only |

For a team already on a cloud, use the cloud registry — serving and monitoring integration is worth it. For cloud-agnostic or multi-cloud, MLflow (self-hosted or Databricks).

Every registered version carries: **artifacts** (weights, serialized preprocessor, feature schema, requirements), **lineage** (training dataset hash/version, code commit, hyperparameters), **metrics** (offline eval at registration time), **stage** (None / Staging / Production / Archived), and **description** (owner, purpose, known limitations). If you cannot reproduce the artifact from the lineage in six months, the registration is incomplete.

---

## Versioning rules

Versions are monotonic integers per model name (MLflow convention). Tags move on top: `champion` (serving 100%), `challenger` (evaluated against champion), `canary` (rolling out), `archived` (retired — never delete, you may need it to reproduce past predictions).

Promotion flow:

```
v5 (registered)
  → staging   (offline eval passes)
  → challenger (online/shadow eval passes vs champion)
  → canary    (5% → 25% → 50% → 100%)
  → champion  (full rollout; previous v4 → archived)
```

A regression bounces the version back a stage. Rollback runs the flow in reverse.

---

## Champion/challenger pattern

The champion serves 100% of traffic; the challenger runs on the same requests but its predictions are only logged (shadow). After a defined window, a challenger wins if the primary metric improves by at least the minimum detectable effect with statistical significance, and no guardrail metric (latency, fairness, error rate) degrades beyond tolerance.

Worked example:

```
Champion: recommender-v12, precision@10 = 0.214, latency p99 = 85ms
Challenger: recommender-v13, shadow-deployed 14 days on 100% of traffic

Results:
  precision@10: v13 = 0.229 vs v12 = 0.213 (Δ=+0.016, p<0.001)
  latency p99:  v13 = 92ms vs v12 = 85ms (Δ=+7ms, within +10% tolerance)
  fairness (demographic parity): within ±1% across cohorts

Decision: promote v13 to canary.
```

A challenger that loses or is inconclusive goes back to staging or is abandoned.

---

## Canary rollout

After shadow wins, the challenger receives a fraction of live traffic. Standard schedule:

```
Day 1: 1%     (catch egregious errors)
Day 2-3: 5%   (statistical sample for fast-moving business metrics)
Day 4-5: 25%
Day 6-7: 50%
Day 8+: 100%  (full rollout if all checks pass)
```

Each stage requires no error-rate increase, no latency regression beyond tolerance, and online metric non-inferior to champion in the canary slice. Any failure → revert to 0% and iterate or abandon.

Traffic split assignment: request-level (hash of request ID) for stateless scoring APIs; user-level (hash of user ID) for models whose predictions accumulate into user state; cohort-level (region, tier) when the blast radius must be a cohort. Default to user-level for user-facing models.

---

## Rollback mechanics

Rollback must be faster than rollout — minutes, not hours. Primitives: traffic flip (endpoint points back to the previous version), feature freeze (pause feature pipelines the new model depended on), cache purge (if predictions are cached).

Rollback contract: the previous artifact is retained (tagged `archived`, never deleted); rollback is a single command; it is tested at least once per quarter; it does not require retraining.

MLflow rollback from v13 back to v12:

```python
from mlflow.tracking import MlflowClient
client = MlflowClient()
client.transition_model_version_stage(name="recommender", version=13, stage="Archived")
client.transition_model_version_stage(name="recommender", version=12, stage="Production")
```

Serving polls the registry (< 60s interval) or uses push notifications to swap promptly.

---

## Model registry — MLflow example

Train, register, promote in one run:

```python
import mlflow, mlflow.sklearn
from sklearn.ensemble import GradientBoostingClassifier

mlflow.set_experiment("recommender")
with mlflow.start_run() as run:
    model = GradientBoostingClassifier(n_estimators=200, max_depth=5)
    model.fit(X_train, y_train)

    mlflow.log_metric("precision_at_10", 0.229)
    mlflow.log_metric("latency_p99_ms", 92)
    mlflow.log_param("training_data_version", "s3://data/recommender/v42")
    mlflow.log_param("training_data_hash", "sha256:abc123...")
    mlflow.log_param("code_commit", "4a7b2e1")

    mlflow.sklearn.log_model(model, artifact_path="model")
    result = mlflow.register_model(
        model_uri=f"runs:/{run.info.run_id}/model",
        name="recommender",
    )

# Promote once offline + shadow eval pass
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="recommender", version=result.version,
    stage="Production", archive_existing_versions=True,
)
```

Serving layer queries `mlflow.pyfunc.load_model("models:/recommender/Production")` and caches the artifact until the registry signals a change.

---

## Model registry — Vertex AI example

```python
from google.cloud import aiplatform
aiplatform.init(project="my-project", location="us-central1")

model = aiplatform.Model.upload(
    display_name="recommender",
    artifact_uri="gs://my-bucket/models/recommender/v13/",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-3:latest",
    labels={"version": "v13", "owner": "ml-team"},
)

endpoint = aiplatform.Endpoint(endpoint_name="recommender-endpoint")
endpoint.deploy(model=model, traffic_percentage=5,
                machine_type="n1-standard-4",
                min_replica_count=2, max_replica_count=10)
# The existing v12 deployment is auto-adjusted to 95%

# Promote to 100%
endpoint.update_traffic_split({"recommender-v13": 100, "recommender-v12": 0})

# Rollback — flip traffic back
endpoint.update_traffic_split({"recommender-v13": 0, "recommender-v12": 100})
```

Vertex natively supports the traffic split; no feature-flag shim required. SageMaker's `UpdateEndpoint` with production variants offers the equivalent on AWS.

---

## Offline eval vs online eval

Both required; neither is sufficient alone.

**Offline eval** runs against a held-out dataset. Fast, cheap, repeatable; gates promotion from staging to challenger. Primary metric + guardrails (latency, fairness, calibration), compared against the current champion on the same **stable evaluation set** that does not change between runs.

**Online eval** runs against live traffic. Same primary metric but measured from actual user interactions. Shadow deployment or A/B canary. Statistical power calculated in advance.

When they disagree (offline says v13 is better, online says worse), suspect: distribution shift (stale offline data), selection bias in the offline labels, feedback loops (the live model's outputs shape training data), or latency sensitivity (users abandon slower responses). Trust online; use the disagreement to fix offline for next time.

---

## Shadow deployment

The challenger receives every production request and produces a prediction, but only the champion's output reaches the user. Zero user risk, full statistical power. Log the request features (hashed if PII), both predictions, timing, and any challenger errors. Shadow doubles inference cost — run it for the evaluation window (1-2 weeks) and tear down after decision.

---

## Monitoring in production — beyond accuracy

- **Input drift**: distribution of input features vs training distribution. KS test or PSI per feature, per cohort.
- **Prediction drift**: distribution of predictions over time. Sudden shifts signal upstream changes.
- **Performance**: where ground truth is available, track the primary metric with a lag.
- **Latency and error rate**: standard service SLOs.
- **Feature freshness**: features used at inference must themselves be fresh (see `feature-store-patterns.md`).

When drift exceeds threshold: trigger retraining, investigate upstream, or page if severe. Drift monitoring is part of the Rigorous elevation of `observability-sre-practice` in this track.

---

## Quick checklist per production model

- [ ] Registered with lineage (data version, code commit, hyperparameters).
- [ ] Offline eval passes against champion on a stable eval set.
- [ ] Shadow deployed for defined window; decision documented.
- [ ] Canary schedule + guardrail metrics wired; rollback command tested.
- [ ] Drift monitoring live before promotion to champion.
- [ ] Previous champion retained (archived, never deleted).
- [ ] Eval suite runs weekly with trend reporting.
