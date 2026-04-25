# Cloud carbon measurement — tools and methodology

## How carbon is calculated

Cloud providers measure carbon as **CO₂e (carbon dioxide equivalent)**, which bundles all greenhouse gases (CO₂, CH₄, N₂O, etc.) into a single metric. The formula:

```
CO₂e = Energy consumed (kWh) × Carbon intensity (kg CO₂e/kWh)
```

**Energy consumed** comes from server utilisation, cooling, and networking.  
**Carbon intensity** varies by electricity grid — a server in Iowa (high renewables) emits far less per kWh than one in a coal-heavy region.

---

## Provider tooling

### AWS — Customer Carbon Footprint Tool

- Location: Console → Billing → Carbon Footprint
- Data: monthly CO₂e by service and region, 3-month lag
- Granularity: account-level; limited per-service breakdown
- Export: CSV download or Cost and Usage Report integration
- Notes: AWS uses a market-based methodology (counts purchased renewable energy certificates)

### GCP — Carbon Footprint

- Location: Console → Carbon Footprint (standalone page)
- Data: monthly gross CO₂e and net (after Google's renewable matching), by project and region
- Granularity: per-project, per-service, per-region
- Export: BigQuery dataset (recommended for trend tracking)
- Notes: GCP matches 100% renewables on a market basis; net carbon is often near zero but gross is the honest baseline

### Azure — Emissions Impact Dashboard

- Location: Microsoft Sustainability Manager or Azure Carbon Optimization (preview)
- Data: monthly CO₂e by subscription, resource group, and region
- Export: Power BI integration or CSV
- Notes: Azure uses a location-based methodology by default (grid carbon intensity, not renewable certificates)

### Multi-cloud — Cloud Carbon Footprint (open source)

- Install: `npm install -g @cloud-carbon-footprint/cli`
- Supports: AWS, GCP, Azure simultaneously
- Methodology: consistent location-based calculation across all providers — useful for fair multi-cloud comparison
- Output: interactive dashboard or CSV
- Docs: `cloudcarbonfootprint.org`

---

## Region carbon intensity reference

Region selection is the highest-leverage lever for workloads without latency or data-residency constraints. The values below are representative averages — actual values vary by hour and season.

| Cloud region | Approx. carbon intensity (kg CO₂e/kWh) | Rating |
|-------------|----------------------------------------|--------|
| AWS us-west-2 (Oregon) | 0.10–0.15 | Low (high hydro + wind) |
| AWS eu-west-1 (Ireland) | 0.23–0.30 | Medium-low |
| AWS ap-southeast-1 (Singapore) | 0.40–0.49 | Medium-high |
| AWS ap-southeast-2 (Sydney) | 0.56–0.65 | High |
| AWS us-east-1 (N. Virginia) | 0.28–0.38 | Medium |
| GCP us-west1 (Oregon) | 0.08–0.12 | Very low |
| GCP europe-west1 (Belgium) | 0.15–0.24 | Low |
| GCP asia-southeast1 (Singapore) | 0.37–0.46 | Medium-high |
| Azure westus2 (Washington) | 0.12–0.18 | Low |
| Azure northeurope (Ireland) | 0.24–0.31 | Medium-low |
| Azure australiaeast (Sydney) | 0.55–0.63 | High |

**Rule of thumb:** moving from a high-carbon to a low-carbon region of the same provider for the same workload typically reduces emissions by 50–80% with no code changes.

---

## What to collect per audit

Minimum required data (90-day window):

- [ ] Total CO₂e for the period (metric tonnes)
- [ ] Breakdown by service (top 5 by emission share)
- [ ] Breakdown by region (all active regions)
- [ ] Month-over-month trend (3 months minimum)
- [ ] Compute-specific: vCPU-hours consumed, average utilisation
- [ ] Storage-specific: TB stored by tier (SSD / HDD / archive)
- [ ] Data transfer: GB transferred cross-region and to internet
