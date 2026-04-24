# RTO / RPO framework

Tier classification, target setting, and pattern selection. Use this document when the SKILL.md calls for step 1 (classify) or step 2 (set targets).

---

## Definitions, unambiguous

- **RTO — Recovery Time Objective.** The maximum acceptable duration between failure and service restored. Measured from the moment customers are impacted to the moment they are not. Includes detection, decision, and recovery execution — not just the last one.
- **RPO — Recovery Point Objective.** The maximum acceptable data loss, measured as time. RPO=5min means "we can lose at most 5 minutes of writes." Drives replication / backup frequency.
- **MTTR** is a separate concept (mean time to repair in normal ops). Do not conflate with RTO.

---

## Tier classification worksheet

Answer these for every system. One "yes" at a level pins the tier.

### Is it Tier 1?

- Does outage stop revenue flow in real time?
- Does outage breach an SLA with financial penalty?
- Does outage block a regulated workflow (e.g. payment settlement, safety reporting)?
- Does outage prevent customers from accessing any data they have entrusted to us?

### Is it Tier 2?

- Is it user-visible but not revenue-blocking?
- Would a 2–4 hour outage cause customer complaints but not contractual breach?
- Does it support Tier 1 with degraded-mode fallback available?

### Is it Tier 3?

- Internal-only?
- Engineers tolerate a business-day outage?
- No customer data involved?

### Common mis-classification

- Dashboards are often Tier 2, not Tier 1. The underlying data source is Tier 1.
- Auth is always Tier 1 for any user-facing product. Do not tier it by volume.
- "Read-only" Tier 1 systems still need DR; they just tolerate a longer RPO.
- Dev / CI infra is Tier 3, but note that a 48h dev-infra outage also halts delivery. Some teams elevate to Tier 2.

---

## RTO / RPO selection heuristics

**Start from business tolerance, not technical feasibility.** Ask the business owner: "at hour N of outage, what happens?" Work backwards.

### Tier 1

- RTO typically 1h or less. If the business accepts 4h for a Tier 1, pattern drops from active-active to active-passive and cost halves.
- RPO typically 5–15 min. Driven by replication lag of the chosen data store pattern.
- Below 5 min RPO: synchronous replication or quorum writes across regions. Very expensive. Justify.

### Tier 2

- RTO 4–12h. Enough time to scale up warm-standby or pilot-light.
- RPO 1–4h. Snapshot + WAL shipping is typically sufficient.

### Tier 3

- RTO 24–72h. The constraint is "restore + redeploy + reverify."
- RPO 24h. Nightly backup is the norm.

### Write down the reasoning

Every RTO / RPO number in the plan carries a one-line business justification. Without it, the next engineer raises or lowers the target arbitrarily.

Example:
```
payments-api: RTO=1h, RPO=5m
Reasoning: merchant SLA specifies 99.95% monthly availability (~22min/month budget).
An outage >1h exhausts the month's budget in a single event. RPO=5m matches the
async replication lag ceiling documented for our multi-region Aurora setup.
```

---

## Cost / benefit per pattern

Rough order-of-magnitude cost multipliers vs single-region baseline. Validate against your actual cloud bill.

| Pattern | Infra cost | Ops complexity | Typical RTO | Typical RPO |
|---------|-----------|---------------|-------------|-------------|
| Backup + restore only | 1.05x | Low | 4–24h | 1–24h |
| Pilot-light | 1.15x | Medium | 2–6h | 15m–1h |
| Warm-standby | 1.3–1.5x | Medium | 30m–2h | 5–30m |
| Active-passive (hot) | 1.8–2.0x | High | 5–30m | 1–15m |
| Active-active | 2.0–2.5x | Very high | near-zero | near-zero (with conflict model) |

Active-active is not strictly better. It is strictly more expensive and more complex. Use only when the RTO requires it.

---

## Cloud-specific pattern mappings

### AWS

- **Backup**: AWS Backup + cross-region copy; S3 Object Lock (compliance mode) for immutable tier.
- **Pilot-light**: Cross-region read replicas; infra as Terraform, applied on failover.
- **Warm-standby**: RDS cross-region replica + ECS / Lambda at reduced capacity; Route 53 failover record.
- **Active-passive (hot)**: Aurora Global Database or DynamoDB Global Tables in active-passive; ALBs fully provisioned in both regions.
- **Active-active**: Aurora Global with write-forwarding OR DynamoDB Global Tables (last-writer-wins caveats); Route 53 latency routing.

### GCP

- **Backup**: Cloud Storage + Object Versioning + Bucket Lock; Persistent Disk snapshots.
- **Pilot-light**: Cloud SQL cross-region read replica; infra via Terraform or Config Controller.
- **Warm-standby**: GKE in secondary region at low capacity; Cloud SQL replica; Global LB with backend buckets.
- **Active-passive / active-active**: Spanner multi-region (TrueTime-backed); Cloud Load Balancing.

### Azure

- **Backup**: Azure Backup + Geo-Redundant Storage (GRS) + immutable blob storage with time-based retention.
- **Pilot-light**: Azure Site Recovery; geo-replicated SQL DB.
- **Warm-standby**: Paired region deployment with Traffic Manager failover.
- **Active-active**: Cosmos DB multi-region writes; Front Door with multi-region origins.

---

## Failure-mode matrix

Patterns defend against different failures. A plan that only handles "region down" misses the common case.

| Failure | Backup+restore | Pilot-light | Warm | Active-passive | Active-active |
|---------|----------------|-------------|------|----------------|---------------|
| Single-AZ outage | Manual | Manual | Auto | Auto | Auto |
| Region outage | Slow restore | Slow cutover | Fast cutover | Near-instant | Transparent |
| Data corruption | Point-in-time restore | Point-in-time restore | Point-in-time restore | Point-in-time restore | **Same corruption in both** |
| Ransomware | Immutable copy | Immutable copy | Immutable copy | Immutable copy | **Replicates to DR** |
| Accidental delete | Granular restore | Granular restore | Granular restore | Granular restore | **Replicates** |

Active-active does not defend against corruption, ransomware, or accidental deletion. That is what the immutable backup is for. The two controls are complementary, not substitutes.

---

## When to re-tier

- A Tier 3 system that starts holding customer data is no longer Tier 3.
- A Tier 2 service that becomes a critical dependency of Tier 1 inherits its tier.
- A Tier 1 workflow that is fully offloaded to a third party drops in tier (the third party's DR now matters — audit theirs).

Review tiering at least annually, and on any significant architecture change.
