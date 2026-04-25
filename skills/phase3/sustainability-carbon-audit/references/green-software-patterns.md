# Green software patterns

Ordered by typical implementation effort (low to high). Apply the low-effort patterns first — they often deliver 30–60% of the carbon reduction at 10% of the cost.

---

## 1. Region migration

**What:** Move a workload to a lower-carbon-intensity region.

**When:** Workload has no latency constraint tying it to a specific geography (batch jobs, async processing, internal tools) and no data-residency regulation requiring a specific region.

**Implementation:**
1. Confirm no data-residency constraint (GDPR, HIPAA, customer contract).
2. Measure cross-region latency impact with a canary test.
3. Update infrastructure-as-code region parameter and re-deploy.
4. Update DNS / load balancer origin.

**Effort:** 0.5–2 days  
**Typical reduction:** 40–75% for workloads moving from high- to low-carbon region

---

## 2. Right-sizing

**What:** Match instance type and size to actual workload requirements.

**When:** CPU or memory average utilisation is consistently below 20–30% over a 30-day window.

**Implementation:**
1. Pull 30-day average and p95 CPU/memory utilisation from CloudWatch / Stackdriver / Azure Monitor.
2. Target instance type where average utilisation is 40–60% (headroom for spikes without overprovisioning).
3. Consider newer-generation instance types — they deliver more performance per watt (e.g., AWS Graviton vs x86 of same size: ~20% lower energy).
4. Apply in staging first; promote to production with rollback plan.

**Effort:** 0.5–1 day per service  
**Typical reduction:** 20–40% for oversized compute

---

## 3. Data tiering

**What:** Move cold data to archive storage; delete data with no retention value.

**When:** Storage audit reveals data older than 90 days in warm/hot tiers that is never accessed.

**Implementation:**
1. Identify access patterns from storage access logs.
2. Set lifecycle policy: warm → cold after 30 days unaccessed; cold → archive after 90 days; delete at retention expiry.
3. Document retention policy in `data-governance-privacy` output for audit trail.

**Effort:** 0.5–1 day  
**Typical reduction:** 10–30% on storage emissions; storage is usually < 15% of total emissions but compounds over time

---

## 4. Spot / preemptible instances for batch

**What:** Run interrupt-tolerant batch workloads on spot (AWS) or preemptible (GCP) instances, which run on excess capacity at lower energy and cost.

**When:** Batch job tolerates interruption and restart; runtime window is flexible (overnight, weekends).

**Implementation:**
1. Ensure batch job is idempotent and checkpoints progress.
2. Use spot with interruption handling (drain queue, checkpoint, restart).
3. Set a maximum price cap to avoid running on-demand at peak pricing.

**Effort:** 0.5–1 day  
**Typical reduction:** 30–50% on batch compute emissions (spot is energy-proportional to demand)

---

## 5. Efficient data formats

**What:** Replace text-based serialisation (JSON, CSV) with binary formats (Protobuf, Parquet, Avro) for high-volume data transfer.

**When:** Service transfers > 1 GB/day of JSON or CSV data between services or to storage.

**Implementation:**
1. Benchmark compression ratio: Protobuf typically 3–5× smaller than equivalent JSON; Parquet 5–10× for columnar data.
2. Update producer and consumer; keep JSON as a compatibility fallback for external APIs.
3. Measure transfer cost and carbon reduction post-migration.

**Effort:** 1–3 days  
**Typical reduction:** 50–80% on data transfer emissions for affected paths

---

## 6. Carbon-aware scheduling

**What:** Schedule flexible batch jobs to run when the grid carbon intensity is lowest (typically off-peak hours, or when renewable generation is high).

**When:** Batch job timing is flexible by ± 4–8 hours; significant compute volume (> 100 vCPU-hours/day).

**Implementation:**
1. Use the Electricity Maps API or WattTime API to query real-time carbon intensity.
2. Build a scheduler that delays job start until intensity drops below a threshold.
3. Set a hard deadline to prevent indefinite deferral.

**Carbon-aware scheduling example (pseudo-code):**
```python
def schedule_batch(deadline_utc, threshold_kg_per_kwh=0.15):
    now = datetime.utcnow()
    for window_start in hourly_windows_until(deadline_utc):
        intensity = get_carbon_intensity(region, window_start)
        if intensity < threshold_kg_per_kwh:
            return window_start
    return deadline_utc  # hard deadline — run regardless
```

**Effort:** 1–3 days  
**Typical reduction:** 15–40% on batch compute emissions depending on grid and region

---

## 7. Demand shaping

**What:** Throttle or defer non-urgent requests during high-carbon periods; smooth traffic peaks.

**When:** Service has a mix of urgent and deferrable work; peak traffic causes autoscaling to provision high-carbon capacity.

**Implementation:**
1. Classify request types: urgent (real-time user action) vs deferrable (report generation, bulk export, notification dispatch).
2. Queue deferrable requests to a priority queue with a time window.
3. Process deferred queue during low-carbon hours (combine with carbon-aware scheduling).

**Effort:** 2–5 days  
**Typical reduction:** 10–25% on deferrable workload emissions
