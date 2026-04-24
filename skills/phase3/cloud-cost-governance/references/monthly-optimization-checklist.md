# Monthly cloud cost optimization checklist

Run on the same day each month. Takes 30 minutes. Produces the audit output from the SKILL.md output format.

Data source for each item is noted. Pull the data before starting — do not do it line by line.

---

## Before you start: pull the data

- AWS: open Trusted Advisor → Cost Optimization + Cost Explorer with 14-day date range
- GCP: open Recommender → VM rightsizing + Billing reports
- Azure: open Advisor → Cost + Cost Management analysis

Pull metric data for the past 14 days for all production and staging instances.

---

## Section 1: Right-sizing

Goal: identify instances where CPU or RAM is chronically underutilized.

| # | Check | Threshold | Action | Data source |
|---|-------|-----------|--------|-------------|
| R1 | Average CPU utilization per instance, last 14 days | < 10% | Downsize one instance tier | CloudWatch / Stackdriver / Azure Monitor |
| R2 | Average RAM utilization per instance, last 14 days | < 20% | Downsize one instance tier | CloudWatch agent / OS metrics |
| R3 | Review cloud provider right-sizing recommendations | — | Accept any recommendation with > 30% potential saving | Trusted Advisor / Recommender / Advisor |
| R4 | Any instances running at peak capacity consistently? | CPU > 80% for > 7 of 14 days | Consider upsizing or horizontal scaling | CloudWatch / Stackdriver |

When downsizing:
1. Check the metric at the new tier size — estimate headroom
2. Schedule the change during low-traffic hours
3. Monitor for 48 hours after resize; revert immediately if error rate or latency degrades
4. Update the cost estimate in `docs/sdlc-status.md`

Tier examples (AWS EC2):
- t3.xlarge (4 vCPU, 16GB) → t3.large (2 vCPU, 8GB): saves ~50% on that instance
- m5.large (2 vCPU, 8GB) → t3.medium (2 vCPU, 4GB): saves ~30%

---

## Section 2: Reserved capacity and savings plans

Goal: commit to 1-year pricing for resources that have been running continuously.

| # | Check | Threshold | Action | Data source |
|---|-------|-----------|--------|-------------|
| C1 | Any on-demand instance running continuously? | > 6 months | Evaluate 1-year RI or savings plan | AWS Cost Explorer RI recommendations |
| C2 | Any RDS instance running continuously? | > 6 months | Evaluate RDS reserved instance | AWS RDS console → Reserved Instances |
| C3 | Any ElastiCache/Redis running continuously? | > 6 months | Evaluate ElastiCache reserved node | AWS ElastiCache console |
| C4 | Existing RIs: any expiring in next 60 days? | — | Renew or resize before expiry | AWS Cost Explorer → RI coverage report |

Decision rule for commitment:
- Confident the resource runs 12+ more months → 1-year RI (saves 30–40% vs on-demand)
- Uncertain → stay on-demand; revisit next month
- Very confident, 3+ year horizon → 3-year RI (saves up to 60%, but locks in the size)

Document RI purchases in the monthly audit output. Tag the RI with the same tags as the instance it covers.

---

## Section 3: Orphaned resources

Goal: delete resources that are no longer attached to anything or in use.

| # | Resource type | What "orphaned" means | How to find | Action |
|---|--------------|----------------------|-------------|--------|
| O1 | EBS volumes (AWS) / Persistent Disks (GCP) | Unattached (no instance) | EC2 console → Volumes → filter "available" | Delete or attach |
| O2 | Load balancers | Zero target healthy, or no traffic for 14 days | ALB / NLB metrics in CloudWatch | Delete |
| O3 | Snapshots | Older than 90 days, not covered by backup retention policy | EC2 → Snapshots, sort by date | Delete |
| O4 | Stopped instances | Stopped for > 30 days | EC2 console → filter "stopped" | Terminate, or snapshot-then-terminate |
| O5 | Unused Elastic IPs (AWS) | Not associated with a running instance | EC2 → Elastic IPs | Release |
| O6 | Unused NAT Gateways | No traffic through them | CloudWatch → NatGatewayActiveConnectionCount | Delete |
| O7 | Old AMIs / machine images | > 90 days, not used by any instance or launch template | EC2 → AMIs | Deregister |
| O8 | Sandbox resources past `expires` tag date | `expires` tag is in the past | Cost Explorer → tag filter `environment=sandbox` | Contact owner; delete if unreachable |

Before deleting:
- Snapshots: verify no backup policy references the snapshot
- Instances: verify no active service depends on it (check DNS, load balancer targets, cron jobs)
- Volumes: verify the data is not needed (check last write time if possible)

When in doubt, snapshot before deleting. A snapshot costs far less than a mistake.

---

## Section 4: Data transfer costs

Goal: find and reduce unexpected egress or cross-AZ transfer costs.

| # | Check | How to find | Action |
|---|-------|-------------|--------|
| D1 | What are the top 5 data transfer cost line items? | Cost Explorer → Service: Data Transfer → group by Usage Type | Investigate any line item that is new or > 10% MoM growth |
| D2 | Cross-AZ data transfer: is it significant? | Cost Explorer → Usage Type: DataTransfer-Regional-Bytes | Ensure services in same region communicate via same AZ; check service mesh config |
| D3 | Is CDN caching reducing egress? | CloudFront / Cloud CDN hit rate | If cache hit rate < 80% for cacheable content, investigate TTL settings |
| D4 | Any service pulling large datasets repeatedly that could be cached? | Review top egress sources | Add a caching layer; use S3 Transfer Acceleration or CDN for large static assets |
| D5 | Logs and metrics export: is volume as expected? | CloudWatch Logs → Data ingested per log group | Confirm log verbosity in production is INFO, not DEBUG |

Data transfer pricing reference (approximate — verify current pricing):
- AWS: $0.09/GB egress to internet (first 10TB/month)
- AWS: $0.01/GB cross-AZ (within region)
- GCP: $0.08/GB egress to internet (first 1TB/month)
- Azure: $0.087/GB egress to internet (first 10TB/month)

---

## Section 5: Managed service utilization

Goal: downsize or consolidate managed services that are significantly underutilized.

| # | Service | Underutilization signal | Action |
|---|---------|------------------------|--------|
| M1 | RDS | CPU < 10%, connections < 20% of max, storage < 30% used | Downsize instance class; evaluate multi-tenant consolidation |
| M2 | ElastiCache / Redis | Memory < 20% used, CPU < 5% | Downsize node type; evaluate shared instance |
| M3 | OpenSearch / Elasticsearch | JVM heap < 30%, disk < 40% used | Downsize data nodes |
| M4 | EKS / GKE node pools | Node CPU < 30% across the pool | Reduce node count or use smaller node type; check Kubernetes resource requests |
| M5 | SQS / Pub/Sub | Queue depth near zero, message rate very low | Consolidate multiple low-volume queues |
| M6 | Managed Kafka / MSK | Consumer lag near zero, partition utilization low | Reduce broker count or broker type |

For each finding: quantify the saving before acting. Downsizing a managed service has a larger blast radius than an EC2 instance — verify in staging first, then apply to production.

---

## Section 6: Cost anomalies

Review the MoM delta for each service.

| Signal | Threshold | Action |
|--------|-----------|--------|
| Service cost grew | > 10% MoM | Investigate cause before next audit |
| Service cost grew | > 25% MoM | Investigate this week; document cause in audit |
| Service cost grew | > 50% MoM | Immediate investigation; treat as incident |
| New service appeared in top 10 | Any | Verify tagging is correct; confirm it is expected |

For any anomaly, determine: is it correlated with user growth? Is it a known traffic increase? Is it unexpected? Document the conclusion in the audit output.

---

## Audit output format

```
Cloud Cost Audit — [Month Year]
Date run: [YYYY-MM-DD]
Run by: [name]

Budget: $[X]  |  Spent to date: $[Y]  |  Consumed: [Z]%  |  MoM: [±%]

TOP SERVICES
  [service]: $[cost]  [±%] MoM  → [note]
  ...

RIGHT-SIZING CANDIDATES
  [instance]: [type], avg CPU [%] / 14 days  → downsize to [type] ($[saving]/mo saving)
  ...

ORPHANED RESOURCES
  [resource-id]: [description], [days] days  → [action] ($[saving]/mo saving)
  ...

RESERVED INSTANCE OPPORTUNITIES
  [service]: running [N] months continuously
  → 1-year RI saves ~$[X]/mo
  Decision needed: @[owner]

ANOMALIES
  [service]: [description of anomaly] — [status: under investigation / explained / resolved]

TOTAL IDENTIFIED SAVINGS: $[X]/mo
ACTIONS:
  1. [action] — @[owner] — by [date]
  ...
```

Post in the team channel. Archive in `docs/cost-audits/YYYY-MM.md`.
