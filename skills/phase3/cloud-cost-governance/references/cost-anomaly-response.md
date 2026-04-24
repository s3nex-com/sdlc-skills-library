# Cost anomaly response playbook

Use this when a budget alert fires or when the monthly audit reveals an unexpected cost spike. The goal is to identify the cause, contain it, and prevent recurrence — in that order.

---

## When to use this playbook

- Budget alert fires at 80% of monthly budget before the 20th of the month
- Budget alert fires at 100% of monthly budget at any point
- Monthly audit reveals a service with > 25% MoM cost increase without a known cause
- An engineer notices a line item in the bill that does not make sense

---

## First 15 minutes: identify the service

1. Open Cost Explorer (AWS) / Billing reports (GCP) / Cost Management (Azure)
2. Set date range: last 7 days, grouped by service
3. Find the line item that is anomalous — the largest absolute increase or the most unexpected entry
4. Narrow by tag: filter by `project` and `feature` to identify which feature or component is responsible
5. Check if the spike is:
   - A single large event (one-time charge, large data transfer job)
   - A sustained increase starting from a specific date
   - A growing trend over multiple days

If you cannot identify the service in 15 minutes: post in the team channel with what you have found so far. Do not spend 2 hours in cost explorer alone.

---

## Next hour: find the cause

For compute cost spikes:

```
□ Is there a new instance running that was not there before?
  → EC2 console: sort instances by launch time; check for unexpected instances

□ Did instance count scale up unexpectedly?
  → Auto-scaling group activity log; check target tracking metrics

□ Did instance type change?
  → Compare current instance type vs last month's

□ Is a long-running batch job consuming more than expected?
  → CloudWatch CPU metrics; check for jobs that did not terminate
```

For data transfer cost spikes:

```
□ Did egress volume increase sharply?
  → Cost Explorer → Data Transfer by Usage Type
  → Check CloudFront / CDN analytics for cache hit rate drop

□ Is cross-AZ traffic higher than expected?
  → Check if a deployment moved a service to a different AZ than its database

□ Did a new feature ship with unexpected data transfer patterns?
  → Correlate spike date with recent deployments

□ Is a backup or export job pulling large datasets?
  → Check scheduled jobs, ETL pipelines, log exports
```

For API call cost spikes:

```
□ Is a managed AI API (OpenAI, Claude, etc.) being called more than expected?
  → Check API usage dashboard; look for missing cache or retry loops

□ Is a mapping, SMS, or payment API being called in a loop?
  → Check application logs for unexpected call rates

□ Is rate limiting causing retries that drive up call volume?
  → Look for 429 responses in logs followed by rapid retries
```

For storage cost spikes:

```
□ Did data volume grow unexpectedly?
  → S3 bucket sizes in CloudWatch; check bucket lifecycle policies

□ Are log retention settings correct?
  → CloudWatch Logs: check log group retention policy; default is often "never expire"

□ Are old snapshots accumulating?
  → EC2 → Snapshots: sort by date; check if automated snapshot policy is deleting old snapshots
```

---

## Resolution: fix and prevent recurrence

### Termination fix (runaway resource)

If the cause is an unintended resource:
1. Snapshot data if needed
2. Terminate or delete the resource
3. Document what created it (deployment, manual action, automated job)
4. Add a guard to prevent recurrence (budget alert lowered, IaC change, deployment gate)

### Code fix (runaway API calls or loops)

1. Roll back the deployment that caused the spike, or deploy a hotfix to stop the calls
2. Verify the fix has taken effect by watching the cost metric for 1 hour
3. Root cause the loop or retry issue before re-releasing
4. Add a cost ceiling or rate limit in the application code if appropriate

### Configuration fix (wrong retention, wrong lifecycle)

1. Apply the correct configuration (log retention policy, S3 lifecycle rule, snapshot policy)
2. Verify it applies to existing data (some policy changes are prospective only)
3. If historical data is driving cost: assess whether it can be deleted or moved to cheaper storage tier (S3 Glacier, cold storage)

### Data transfer fix

1. If cache hit rate dropped: investigate CDN configuration, TTL settings, cache invalidation patterns
2. If cross-AZ traffic spiked: ensure services and their databases are in the same AZ, or use a VPC endpoint
3. If a new feature is generating unexpected egress: evaluate whether the data can be cached, compressed, or served via CDN

---

## Communication template

Use this when the spike is large enough to require stakeholder communication (> 20% of monthly budget in a single anomaly).

```
Subject: Cloud cost alert — [service name] [date]

Summary:
  We identified an unexpected cost spike in [service / feature].
  Estimated impact: $[X] additional spend over [time period].
  Root cause: [one-sentence description]
  Status: [contained / under investigation]

Timeline:
  [YYYY-MM-DD HH:MM] — alert fired / anomaly detected
  [YYYY-MM-DD HH:MM] — cause identified: [cause]
  [YYYY-MM-DD HH:MM] — fix deployed: [fix description]
  [YYYY-MM-DD HH:MM] — spend returned to baseline (or: under investigation)

Prevention:
  [What will prevent this from recurring:
   - guard added to IaC, or
   - rate limiting added to code, or
   - retention policy corrected, or
   - monitoring alert added at lower threshold]

No action required from you. This is for awareness.
```

Send to: the engineer who owns the service + one stakeholder if the projected monthly cost is > budget.

---

## After resolution: audit entry

Append to `docs/skill-log.md`:

```
[YYYY-MM-DD] cloud-cost-governance | outcome: OK | next: verify at next monthly audit | note: cost anomaly resolved — [cause] — [fix] — $[impact] contained
```

If not fully resolved:

```
[YYYY-MM-DD] cloud-cost-governance | outcome: PARTIAL | next: [specific next action + owner] | note: cost spike in [service] — cause identified — fix in progress — $[X] projected impact
```

---

## Common anomaly patterns and typical causes

| Pattern | Typical cause | First thing to check |
|---------|--------------|---------------------|
| Compute doubles overnight | Auto-scaling misconfiguration, or runaway batch job | ASG activity log; CloudWatch CPU of new instances |
| Data transfer spike on deploy day | Service moved AZ, CDN invalidation, or large asset added | Cross-AZ transfer cost; cache hit rate |
| Storage cost grows 10% MoM steadily | No lifecycle policy on S3 bucket or CloudWatch log group | S3 bucket lifecycle rules; log group retention policy |
| API cost spikes for one hour | Retry loop after a downstream error | Application error rate; retry backoff config |
| Orphaned cost persists after service deletion | Resource not fully cleaned up (volumes, snapshots, EIPs) | EC2 console: volumes, snapshots, Elastic IPs — filter by the deleted service's tags |
| Dev/sandbox environment cost balloons | Dev environment left running over a long break | Filter by environment=dev or environment=sandbox tag |
