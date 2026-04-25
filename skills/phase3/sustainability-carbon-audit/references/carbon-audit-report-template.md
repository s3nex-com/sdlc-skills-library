# Carbon audit report — template and worked example

Copy the template section into a file at `docs/carbon-audit-[YYYY-MM].md`. Fill in the values from your cloud provider's carbon dashboard.

---

## Template

```markdown
# Carbon Audit Report

**Date:** [YYYY-MM-DD]
**Scope:** [list service names, cloud account IDs, regions]
**Period:** [start date] → [end date]
**Tool:** [AWS CCF / GCP Carbon Footprint / Azure / Cloud Carbon Footprint OSS]
**Mode:** [Lean / Standard / Rigorous]
**Auditor:** [team or person who ran the audit]

---

## Baseline

| Metric | Value |
|--------|-------|
| Total CO₂e (period) | [X.XX] metric tonnes |
| Previous period CO₂e | [X.XX] metric tonnes |
| Month-over-month change | [+/- X%] |
| Top service by emissions | [service name] ([X]%) |
| Top region by emissions | [region] ([X]%) |

---

## Breakdown by service

| Service | CO₂e (kg) | Share | Primary driver |
|---------|-----------|-------|----------------|
| [service] | [X] | [X]% | [compute / storage / transfer] |
| [service] | [X] | [X]% | ... |
| [service] | [X] | [X]% | ... |

---

## Breakdown by region

| Region | CO₂e (kg) | Share | Intensity (kg/kWh) |
|--------|-----------|-------|--------------------|
| [region] | [X] | [X]% | [X.XX] |
| [region] | [X] | [X]% | [X.XX] |

---

## Hotspots

| Rank | Service | CO₂e share | Root cause | Pattern to apply |
|------|---------|-----------|-----------|-----------------|
| 1 | [service] | [X]% | [e.g. oversized EC2, ap-southeast-2 region] | [e.g. right-sizing + region migration] |
| 2 | [service] | [X]% | ... | ... |
| 3 | [service] | [X]% | ... | ... |

---

## Optimisations

| Hotspot | Pattern | Est. reduction (kg CO₂e/month) | Est. effort | Owner | Target date | Status |
|---------|---------|-------------------------------|-------------|-------|-------------|--------|
| [service] | [pattern] | [X] | [X days] | [owner] | [YYYY-MM-DD] | Planned |
| [service] | [pattern] | [X] | [X days] | [owner] | [YYYY-MM-DD] | In progress |

---

## Targets

- **90-day reduction target:** [X]% reduction (from [baseline] to [target] metric tonnes CO₂e)
- **Next audit date:** [YYYY-MM-DD]
- **Cumulative reduction since baseline:** [X]%

---

## Actions

| # | Action | Owner | Due | CO₂e impact (kg/month) | Done? |
|---|--------|-------|-----|------------------------|-------|
| 1 | [action] | [owner] | [date] | [X] | [ ] |
| 2 | [action] | [owner] | [date] | [X] | [ ] |
```

---

## Worked example — three-service system

**System:** API service + background worker + data warehouse  
**Cloud:** AWS, two regions: us-east-1 and ap-southeast-2  
**Period:** 2026-01-01 → 2026-03-31 (90 days)

### Baseline

| Metric | Value |
|--------|-------|
| Total CO₂e (period) | 2.41 metric tonnes |
| Previous period CO₂e | 2.28 metric tonnes |
| Month-over-month change | +5.7% |
| Top service by emissions | background-worker (61%) |
| Top region by emissions | ap-southeast-2 (74%) |

### Breakdown by service

| Service | CO₂e (kg) | Share | Primary driver |
|---------|-----------|-------|----------------|
| background-worker | 1,470 | 61% | Compute — 8× c5.2xlarge, avg 12% CPU utilisation in ap-southeast-2 |
| api-service | 540 | 22% | Compute — 3× c5.large, us-east-1 |
| data-warehouse | 400 | 17% | Storage — 15 TB, ap-southeast-2 |

### Hotspots

| Rank | Service | Issue | Pattern |
|------|---------|-------|---------|
| 1 | background-worker | 8× c5.2xlarge at 12% avg CPU in ap-southeast-2 (high-carbon region) | Right-sizing + region migration |
| 2 | data-warehouse | 15 TB in ap-southeast-2; 8 TB unaccessed in 90 days | Data tiering + region migration |
| 3 | background-worker | Batch jobs run at fixed 2 PM UTC (peak carbon hours) | Carbon-aware scheduling |

### Optimisations

| Hotspot | Pattern | Est. reduction | Effort | Owner | Target | Status |
|---------|---------|----------------|--------|-------|--------|--------|
| background-worker | Right-size c5.2xlarge → c5.large (8→8, matching actual load) | 380 kg/month | 0.5 days | Ali | 2026-04-15 | Done |
| background-worker + data-warehouse | Migrate ap-southeast-2 workloads to us-west-2 | 680 kg/month | 2 days | Sam | 2026-05-01 | Planned |
| background-worker | Carbon-aware scheduler (run at 02:00–06:00 UTC, low-carbon window) | 120 kg/month | 1.5 days | Ali | 2026-04-30 | Planned |
| data-warehouse | Lifecycle policy: move 8 TB cold data to S3 Glacier | 95 kg/month | 0.5 days | Sam | 2026-04-20 | Planned |

**Total estimated reduction: 1,275 kg CO₂e/month = 53% of baseline**

### Targets

- 90-day target: reduce to 1.13 metric tonnes CO₂e (53% reduction from 2.41)
- Next audit date: 2026-06-30
