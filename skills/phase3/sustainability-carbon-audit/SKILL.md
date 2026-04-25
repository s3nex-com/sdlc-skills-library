---
name: sustainability-carbon-audit
description: >
  carbon footprint, carbon audit, green computing, sustainable software, green software,
  environmental impact, Scope 1 emissions, Scope 2 emissions, Scope 3 emissions,
  Cloud Carbon Footprint, carbon intensity, energy efficiency, green cloud,
  carbon-aware scheduling, right-sizing for sustainability, green patterns,
  sustainability review, environmental compliance, net zero, carbon neutral,
  carbon reduction target, cloud emissions, data centre energy
---

# Sustainability and carbon audit

## Purpose

Software systems have a measurable environmental footprint: compute cycles burn energy, data transfer crosses carbon-intensive networks, and storage retains data indefinitely. For most teams this cost is invisible because no one measures it. This skill makes it visible. It produces a baseline carbon measurement, identifies the highest-impact hotspots, applies green software patterns to reduce consumption, and generates a report that anchors sustainability commitments.

This is Phase 3 work because it makes sense after go-live, when the system is running real workloads and the profile is real, not estimated. It runs on a quarterly or per-major-release cadence.

---

## When to use

- Post go-live review: system is live and consuming real cloud resources
- Cloud cost optimization cycle: carbon and cost are often correlated — audit both together
- Sustainability commitment required by a client, regulation, or investor
- New region selection: choose a low-carbon availability zone before deploying
- Architecture decision involves significant compute or data transfer trade-offs
- Pre-release for a new service: estimate the carbon cost before the first deployment

---

## When NOT to use

- System is not yet live — carbon estimation from architecture diagrams is unreliable; wait for real workload data before auditing
- No cloud infrastructure is in scope — on-premises or colocation with no cloud API for carbon data falls outside this skill's tooling
- The real goal is cost reduction, not environmental measurement — start with `cloud-cost-governance` first; come back here after the cost profile is understood; the two skills are complementary, not interchangeable
- General infrastructure right-sizing — use `cloud-cost-governance` for that; `green-software-patterns.md` here is a secondary lens applied after cost is understood

---

## Process

### Step 1 — Measure baseline carbon

Pull the last 90 days minimum from your cloud provider's carbon dashboard or the Cloud Carbon Footprint open-source tool:

| Provider | Tool |
|----------|------|
| AWS | Customer Carbon Footprint Tool — Console → Billing → Carbon Footprint |
| GCP | Carbon Footprint — Console → Active Assist → Carbon Footprint |
| Azure | Emissions Impact Dashboard — Microsoft Sustainability Manager |
| Multi-cloud / self-hosted | Cloud Carbon Footprint (open source, `www.cloudcarbonfootprint.org`) |

Collect:
- Total CO₂e (metric tonnes) for the period
- Breakdown by service (compute, storage, networking, managed services)
- Breakdown by region
- Month-over-month trend

Record in the Carbon Audit Report (see Output format section).

### Step 2 — Identify hotspots

Rank services by carbon contribution descending. Focus on the top 3–5. For each:

| Resource type | What to look for |
|---------------|-----------------|
| Compute | Oversized instances (CPU < 20% average), legacy generation types, idle dev/staging instances running 24/7 |
| Storage | Data retained beyond useful life, warm storage holding cold data (> 90 days unaccessed) |
| Network | Unnecessary cross-region traffic, large payloads transferred without compression, cross-AZ calls in a loop |
| Region | High-carbon region for a workload with no latency constraint — check the region intensity table in `references/cloud-carbon-measurement.md` |

### Step 3 — Apply green software patterns

For each hotspot, pick the relevant pattern from `references/green-software-patterns.md`:

| Pattern | When to apply |
|---------|--------------|
| Carbon-aware scheduling | Batch jobs with timing flexibility — run at low-carbon hours |
| Right-sizing | Instances with headroom > 40% average CPU or memory |
| Demand shaping | Throttle or defer non-urgent requests during peak carbon intensity windows |
| Efficient data formats | Binary (Protobuf, Parquet) over text (JSON, CSV) for large-volume transfers |
| Region migration | Workload in a high-carbon region with no latency or data-residency constraint |
| Data tiering | Move cold data to archive storage; delete what has no retention value |
| Spot/preemptible for batch | Interrupt-tolerant batch workloads that run overnight or on a schedule |

For each pattern applied, record: estimated CO₂e reduction, implementation effort, owner, and target date.

### Step 4 — Set targets and track progress

Set a 90-day carbon reduction target (absolute kg CO₂e or percentage). Record it in the report. Revisit next quarter with a new baseline measurement.

Start with operational changes (region selection, right-sizing, scheduling) that take 1–2 days to implement before recommending architectural changes.

---

## Output format

```markdown
# Carbon Audit Report

**Date:** [YYYY-MM-DD]
**Scope:** [service names, cloud account IDs, regions]
**Period:** [start date] → [end date] (90 days minimum)
**Mode:** [Lean / Standard / Rigorous]
**Tool:** [AWS CCF / GCP / Azure / Cloud Carbon Footprint]

---

## Baseline

| Metric | Value |
|--------|-------|
| Total CO₂e (period) | [X] metric tonnes |
| Top service by emissions | [service name] ([X]%) |
| Top region by emissions | [region] ([X]%) |
| Month-over-month trend | [+/-X%] |

---

## Hotspots

| Rank | Service | CO₂e share | Primary driver |
|------|---------|-----------|----------------|
| 1 | [service] | [X]% | [compute / storage / transfer / region] |
| 2 | [service] | [X]% | ... |
| 3 | [service] | [X]% | ... |

---

## Optimisations

| Hotspot | Pattern applied | Est. reduction | Est. effort | Owner | Status |
|---------|----------------|----------------|-------------|-------|--------|
| [service] | [pattern] | [X] kg CO₂e/month | [hours] | [owner] | Planned / In progress / Done |

---

## Targets

- 90-day target: reduce total CO₂e by [X]% (from [baseline] to [target] metric tonnes)
- Next audit date: [YYYY-MM-DD]

---

## Actions

| Action | Owner | Due | CO₂e impact |
|--------|-------|-----|-------------|
| [action] | [owner] | [YYYY-MM-DD] | [X] kg CO₂e/month |
```

---

## Skill execution log

Append to `docs/skill-log.md`:

```
[YYYY-MM-DD] sustainability-carbon-audit | outcome: OK | next: cloud-cost-governance (if cost reduction is a secondary goal) | note: [X] metric tonnes CO₂e baseline; top hotspot [service]; target [Y]% reduction by [date]
```

---

## Reference files

- `references/cloud-carbon-measurement.md` — how to use cloud provider carbon dashboards and the Cloud Carbon Footprint open-source tool; region carbon intensity table; measurement methodology (energy × carbon intensity factor)
- `references/green-software-patterns.md` — demand shaping, carbon-aware scheduling, right-sizing, efficient data formats, region migration, data tiering, spot/preemptible instances; when and how to apply each pattern with implementation notes
- `references/carbon-audit-report-template.md` — full editable report template with a worked example for a three-service system showing baseline, hotspots, and optimisation actions
