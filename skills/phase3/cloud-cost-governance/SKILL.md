---
name: cloud-cost-governance
description: >
  cloud cost, AWS bill, GCP cost, FinOps, cost optimization, right-sizing,
  cost per feature, budget alert, orphaned resources, reserved instances,
  cloud spending, cost tagging, cost attribution, Azure cost, cost anomaly,
  unattached volumes, savings plans, cost per user, egress cost, cloud waste
---

## Purpose

Cloud costs are real and often invisible on small teams until the bill arrives. A runaway batch job, a forgotten dev environment, or a data transfer pattern nobody modelled can double the monthly spend in a single sprint cycle. This skill makes cost a first-class engineering concern alongside performance and reliability: attribution (who owns what cost), per-feature estimation (cost at design time, not launch time), optimization (monthly audit with concrete savings targets), and governance (budget alerts with a defined response, not just a notification). The goal is not to be cheap — it is to avoid surprises and make cost trade-offs visible when decisions are made.

---

## When to use

- **New service setup** — tag policy and cost estimate before the first resource is created
- **Every PRD (Standard or Rigorous mode)** — include a cost NFR at design time
- **Pre-release cost gate** — estimate monthly cost at expected load before production deployment
- **Monthly optimization audit** — 30 minutes, every month, same day
- **Unexpected bill spike** — immediate investigation using the anomaly response playbook

---

## When NOT to use

- **On-premise infrastructure** — different tooling, different economics. This skill is cloud-specific (AWS, GCP, Azure).
- **FinOps for organizations with 100+ services** — at that scale, dedicated FinOps tooling (CloudHealth, Spot.io, Apptio) and a FinOps team are warranted. This skill is for 3–5 engineers managing tens of services.
- **Software license costs** — SaaS subscriptions and commercial licenses are a procurement process, not a cloud cost engineering problem.
- **Cost reduction at the expense of reliability** — cost optimization that crosses an SLO boundary is a reliability trade-off, not a cost decision alone. Involve the team.
- **Technical debt (code or architecture issues)** → `technical-debt-tracker`. This skill is infrastructure cost only. A slow query that inflates RDS cost is debt; the right fix is tracking it in the debt register, not the cost audit.

---

## Process

### Step 1: Cost attribution (set up once, enforce always)

Tag every cloud resource at creation. Required tags:

| Tag | Purpose | Example values |
|-----|---------|---------------|
| `project` | Which product or project | `edgeflow`, `device-registry` |
| `feature` | Which feature within the project | `telemetry-ingest`, `device-onboarding` |
| `owner` | Who is accountable for this resource | engineer's name or team name |
| `environment` | Deployment environment | `prod`, `staging`, `dev` |

Enforce in IaC (Terraform or Pulumi): fail `plan` if any required tag is missing. No tag = no deploy.

```hcl
# Terraform: fail plan if required tags are absent
variable "required_tags" {
  default = ["project", "feature", "owner", "environment"]
}

resource "aws_instance" "example" {
  # ...
  lifecycle {
    precondition {
      condition = alltrue([
        for tag in var.required_tags : contains(keys(var.tags), tag)
      ])
      error_message = "All required tags (project, feature, owner, environment) must be set."
    }
  }
}
```

Once tagging is enforced, Cost Explorer grouped by tag gives per-feature cost automatically — no manual allocation.

### Step 2: Per-feature cost estimate in PRDs

Every PRD must include a cost NFR: estimated monthly cost at a representative load (e.g. 100k users, 10k devices).

Components to estimate:
- **Compute**: instance type × hours per month (e.g. 2 × t3.medium × 730h = ~$60)
- **Storage**: GB × rate (e.g. 500GB S3 = ~$11.50/mo)
- **Data transfer**: egress GB × rate (e.g. 1TB egress AWS = ~$90/mo)
- **Managed services**: RDS, ElastiCache, managed Kafka — price per instance per hour
- **API calls**: if using managed AI or third-party APIs — estimate call volume × per-call rate

At launch: compare actual to estimate. If actual > 2× estimate, investigate before scaling. The estimate is a commitment to understand the cost model, not a budget cap.

### Step 3: Cost gates at release

Before any new service goes to production:

1. Estimate monthly cost at expected load. Document in `docs/sdlc-status.md`.
2. If estimated cost > $500/month: require architecture review. Could the same result be achieved more cheaply? (Serverless vs always-on, caching layer, cheaper instance type.)
3. If estimated cost > $2,000/month: require explicit stakeholder acknowledgement before proceeding.
4. Baseline the actual first-month cost. If actual > 2× estimate, treat it as a P2 issue.

### Step 4: Monthly optimization audit (30 minutes)

Run on the same day each month. Produce the output format below and share in the team channel.

**Right-sizing**
- Any instance with CPU < 10% average over 14 days → downsize one tier
- Any instance with RAM < 20% average over 14 days → downsize
- Source: AWS Trusted Advisor / GCP Recommender / Azure Advisor — check the "Underutilized" report

**Reserved capacity**
- Any resource running continuously for > 6 months → evaluate reserved instances or savings plans
- 1-year RI or savings plan commitment saves 30–40% over on-demand at the same size
- Commit only if confident the resource runs 12+ more months

**Orphaned resources**
- Unattached storage volumes (EBS, Persistent Disk) → delete or attach
- Unused load balancers with zero traffic → delete
- Snapshots older than 90 days not covered by backup policy → delete
- Stopped instances older than 30 days → terminate, or snapshot-then-terminate

**Data transfer costs**
- Cross-AZ data transfer is often invisible until it is significant — check this line item monthly
- Review the top 5 data transfer cost sources; evaluate whether CDN caching or same-AZ routing reduces egress

**Managed service utilization**
- Any managed service (RDS, ElastiCache, OpenSearch) at < 20% utilization → downsize or consolidate
- Consider whether a shared instance covers multiple low-traffic services

### Step 5: Anomaly detection

- Set a budget alert at 80% of monthly budget. Not 100% — you need time to respond before the budget is exceeded.
- Alert destination: the engineer who owns the service + a shared team channel.
- Alert does not mean action. Define the response before an alert fires (see references/cost-anomaly-response.md).

Common causes of cost spikes:
- Runaway batch job with no cost ceiling
- Accidental loop calling a paid API (managed AI, mapping, SMS)
- Traffic spike hitting egress hard
- Dev or staging environment left running over a long weekend
- New feature with a data transfer pattern that was not estimated

### Cost efficiency metrics — track monthly

| Metric | Formula | Why it matters |
|--------|---------|---------------|
| Cost per active user | Total cloud cost ÷ monthly active users | Tracks unit economics over time |
| Cost per request | Total cost ÷ monthly API request count | Useful for API-heavy services |
| Budget consumed % | Month-to-date spend ÷ monthly budget × 100 | Early warning; drives alert thresholds |
| Top 3 services % | Sum of top 3 services ÷ total × 100 | Concentration risk |
| MoM delta % | (This month − last month) ÷ last month × 100 | Trend; catch drift before it compounds |

---

## Output format

Produce this report at the end of every monthly audit. Post to the team channel and append a summary to `docs/skill-log.md`.

```
Cloud Cost Audit — April 2026
Budget: $2,000  |  Spent to date: $1,847  |  Consumed: 92%  |  MoM: +8%

TOP SERVICES
  ECS (telemetry-ingest):  $634   +12% MoM  → investigate (above 10% threshold)
  RDS (postgres-main):     $312   stable
  S3 (device-data):        $287   +3% MoM   → normal (data growth expected)
  EKS cluster:             $244   stable
  Data transfer (egress):  $183   +18% MoM  → investigate

RIGHT-SIZING CANDIDATES
  telemetry-worker: t3.xlarge, avg CPU 8% / 14 days  → downsize to t3.large ($45/mo saving)
  staging-api: m5.large, avg CPU 6% / 14 days         → downsize to t3.medium ($38/mo saving)

ORPHANED RESOURCES
  vol-0abc123: 500GB EBS, unattached 47 days          → delete ($50/mo saving)
  snap-0def456: 200GB snapshot, 94 days, no policy    → delete ($2/mo saving)

RESERVED INSTANCE OPPORTUNITIES
  RDS postgres-main: running 8 months continuously
  → 1-year RI at current size saves ~$94/mo
  Decision needed: @alice

ANOMALY — ECS telemetry-ingest +12% MoM
  Cause under investigation. Egress also up 18%. Likely cause: new device telemetry
  volume from onboarding launch. Acceptable if correlated with user growth.
  Next: correlate against active device count before next audit.

TOTAL IDENTIFIED SAVINGS: $229/mo
ACTIONS:
  1. Downsize telemetry-worker to t3.large — @bob — by May 1
  2. Downsize staging-api to t3.medium — @alice — by May 1
  3. Delete vol-0abc123 — @bob — today
  4. Evaluate RDS RI commitment — @alice — decision by May 5
```

---

## Skill execution log

Append one line to `docs/skill-log.md` each time this skill fires:

```
[YYYY-MM-DD] cloud-cost-governance | outcome: OK|BLOCKED|PARTIAL | next: <next action> | note: <one-line summary>
```

Examples:
```
[2026-04-20] cloud-cost-governance | outcome: OK | next: implement tagging in Terraform | note: tag policy defined; enforcement not yet wired in IaC
[2026-04-20] cloud-cost-governance | outcome: OK | next: monthly audit May 20 | note: April audit complete; $229/mo savings identified; 4 action items assigned
[2026-04-20] cloud-cost-governance | outcome: BLOCKED | next: get AWS Cost Explorer access | note: cannot run audit without cost data access; requested from account owner
[2026-04-20] cloud-cost-governance | outcome: PARTIAL | next: investigate ECS cost spike | note: audit done; ECS +12% MoM cause not yet confirmed
```

---

## Reference files

`skills/phase3/cloud-cost-governance/references/cost-tagging-policy.md` — template tagging policy: required tags, allowed values, enforcement mechanism in Terraform and Pulumi, exception process.

`skills/phase3/cloud-cost-governance/references/monthly-optimization-checklist.md` — the full monthly audit checklist in printable format: right-sizing, reserved capacity, orphaned resources, data transfer, managed services. Each item has a data source and the action threshold.

`skills/phase3/cloud-cost-governance/references/cost-anomaly-response.md` — response playbook for cost spikes: first 15 minutes (identify the service), next hour (find the cause), resolution (fix and prevent recurrence), communication template.
