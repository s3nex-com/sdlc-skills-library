---
name: disaster-recovery
description: >
  Activate when planning disaster recovery, designing backup strategy, setting RTO or RPO targets,
  evaluating multi-region failover patterns (active-active, active-passive, warm-standby, pilot-light),
  scheduling or running DR drills, planning restore-from-backup procedures, hardening against
  ransomware (immutable / air-gapped backups), classifying systems by recovery tier, preparing a
  post-incident recovery verification, or satisfying SOC 2 availability or GDPR Article 32
  technical-measures expectations. Use for everything from pre-launch DR plans for a new
  customer-facing system to quarterly tabletop exercises and annual full-region failover drills.
---

# Disaster recovery

## Purpose

Disaster recovery is the set of procedures, infrastructure, and proof points that let you restore service after a real failure — region outage, data corruption, ransomware, accidental deletion, or a bad migration. Most teams underinvest here because nothing visible breaks while backups sit untested. Right-size DR per system tier, prove it works on a schedule, and keep the evidence — because a backup you have never restored is not a backup, and a runbook nobody has executed is a hope.

---

## When to use

- Pre-launch for any customer-facing system with an availability SLA
- Any data store of record (primary DB, object store, event log)
- Any service whose outage blocks revenue or customer workflows
- After an industry-wide ransomware scare or after a peer gets hit
- When auditing SOC 2 availability criteria or GDPR Article 32 technical-measures compliance
- When an NFR specifies RTO / RPO and needs a credible implementation
- Before and after migrations that move data stores between regions or providers
- When a recovery drill is scheduled (quarterly tabletop, semi-annual restore, annual failover)

---

## When NOT to use

- Defining SLOs, error budgets, and availability measurement — use `observability-sre-practice`.
- Injecting faults to validate resilience in normal operations — use `chaos-engineering`.
- Running a postmortem and tracking corrective actions after an actual incident — use `incident-postmortem`.
- In-normal-ops reliability patterns (circuit breakers, retries, capacity planning) — use `performance-reliability-engineering`.

---

## Process or checklist

### 1. Classify every system into a tier

Tiering is the whole game. Over-engineering DR for a Tier 3 internal tool burns money; under-engineering DR for Tier 1 loses the company. Be ruthless and write the classification down.

| Tier | Definition | Examples |
|------|-----------|----------|
| **Tier 1** | Revenue-critical or regulatory-critical. Outage stops the business or breaches an SLA with penalties. | Payments, primary customer API, auth, control plane |
| **Tier 2** | User-visible but not revenue-blocking. Degraded UX, not a stop-ship. | Dashboards, search, reporting, notifications |
| **Tier 3** | Internal-only or non-critical. Engineers tolerate a day of outage. | Internal admin tools, dev infra dashboards, non-prod envs |

Any system the team cannot agree on — default down a tier. Over-classification is the more common error.

### 2. Set RTO and RPO per tier

- **RTO (Recovery Time Objective)** — how long from failure to service restored
- **RPO (Recovery Point Objective)** — how much data loss is acceptable (measured in time)

| Tier | RTO | RPO | Pattern | Cost profile |
|------|-----|-----|---------|--------------|
| Tier 1 | 1 hour | 5 min | Multi-region active-active, continuous replication | High (2x infra baseline) |
| Tier 2 | 4 hours | 1 hour | Warm-standby in second region, hourly snapshots | Medium (~30% of primary) |
| Tier 3 | 24 hours | 24 hours | Daily backup + documented restore procedure | Low (backup storage only) |

These are starting points, not mandates. A Tier 1 system with a 4-hour business-tolerance RTO should state RTO=4h, not pretend it is 1h. Write down the business reasoning.

See `references/rto-rpo-framework.md` for tier-decision worksheets, cost/benefit analysis, and cloud-specific pattern mappings.

### 3. Pick a backup strategy

Apply the **3-2-1 rule**: 3 copies of the data, on 2 different media / storage classes, with at least 1 off-site (different region or provider).

**Modern extension for ransomware:** at least one copy must be **immutable** (S3 Object Lock in compliance mode, Azure immutable blob, GCS bucket lock) or **air-gapped**. Ransomware that reaches your backups through the same IAM plane deletes them.

Select backup type per data store:

- **Full** — everything, slow, simple to restore, storage-heavy
- **Incremental** — only changes since last backup (full or incremental), fast, chained restores
- **Differential** — only changes since last full, middle ground
- **Continuous / streaming** — WAL shipping, CDC, change streams — required for tight RPO

See `references/backup-strategy-patterns.md` for concrete patterns per data store (Postgres, DynamoDB, S3, Kafka).

### 4. Pick a failover pattern

| Pattern | Description | When to use |
|---------|-------------|-------------|
| **Active-active** | Both regions serve live traffic | Tier 1 with tight RTO; requires conflict-free data model |
| **Active-passive / hot-standby** | Second region fully provisioned, idle, ready to take traffic | Tier 1 when active-active data model is hard |
| **Warm-standby** | Second region runs at reduced capacity, scales up on failover | Tier 2 — cheaper than hot, slower RTO |
| **Pilot-light** | Core data replicated to second region, compute off, deployed on failover | Tier 2/3 — lowest DR cost above backup-only |
| **Backup + restore only** | No standby infra. Restore from backup into rebuilt region | Tier 3 — accept the RTO cost |

### 5. Write distinct playbooks for distinct failure modes

One runbook does not cover everything. At minimum, write separate playbooks for:

- **Full-region outage** — failover to secondary region
- **Data corruption / bad deploy** — restore to point-in-time; the primary region is still up
- **Ransomware / malicious deletion** — restore from the immutable copy; rotate credentials; forensics hold
- **Accidental deletion (single resource)** — granular restore, not a full DR event

Each playbook has a named owner, defined decision authority to call the DR event, a communication plan, and a rollback path if the DR action itself goes wrong.

See `references/dr-drill-runbook.md` for the runbook template and drill scripts.

### 6. Schedule drills and actually run them

| Drill type | Cadence | Scope |
|------------|---------|-------|
| Tabletop walkthrough | Quarterly | All tiers — walk the runbook, no infra changes |
| Real restore into non-prod | Semi-annual | Tier 1 and Tier 2 — prove data restores + verify integrity |
| Full-region failover | Annual | Tier 1 — cut real traffic to secondary region |
| Ransomware restore | Annual | Tier 1 data stores — restore from immutable copy specifically |

A drill with no failure signal is theatre. Record: time to detect, time to decide, time to restore, data-loss delta (vs RPO target), and at least one issue found. If a drill finds no issues, suspect it.

### 7. Harden backup security

- Encrypt backups at rest with keys in a separate KMS from the primary data
- Use a separate account / subscription / project for backup storage; least-privilege IAM between primary and backup accounts
- No single credential should both write primary data and delete backups
- Alert on unusual backup deletion / restore activity
- For immutable copies: set retention period explicitly; confirm the retention cannot be shortened by any IAM role

### 8. Verify after every real or simulated restore

Restore verification is a checklist, not a vibe:

- Row count or object count matches expected range
- Checksum / hash sample matches source (for object stores)
- Schema version matches expected
- Application health checks pass end-to-end, not just readiness probes
- At least one business-critical query returns correct results
- Replication lag (to any downstream system) has caught up

### 9. Update the DR plan after every drill and every real incident

Append-only lessons log. If the same issue appears in two drills, it is a planning failure, not a drill failure.

### 10. Compliance anchors (brief)

- **SOC 2 Availability TSC** expects documented RTO/RPO, a tested backup procedure, and evidence of recovery testing. Drill records are the evidence.
- **GDPR Article 32** requires appropriate technical measures including the ability to restore access to personal data in a timely manner after an incident. Your DR plan is part of the GDPR technical-measures story. State this in the plan.

---

## Output format with real examples

A complete DR plan has three artefacts: the **tier + targets table**, the **plan document**, and the **drill calendar**. Store in `docs/dr/` alongside the service.

### Tier + targets table (excerpt)

```
| System           | Tier | RTO   | RPO   | Pattern               | Primary region | DR region     |
|------------------|------|-------|-------|-----------------------|----------------|---------------|
| payments-api     | 1    | 1h    | 5m    | Active-active         | eu-west-1      | eu-central-1  |
| customer-portal  | 1    | 1h    | 15m   | Active-passive (hot)  | eu-west-1      | eu-central-1  |
| reports-service  | 2    | 4h    | 1h    | Warm-standby          | eu-west-1      | eu-central-1  |
| admin-console    | 3    | 24h   | 24h   | Backup-restore only   | eu-west-1      | eu-central-1  |
```

### DR plan document structure

```
# DR plan — <system name>

## 1. Classification
Tier, RTO, RPO, business reasoning.

## 2. Architecture
Data stores in scope, replication topology, failover pattern, diagram.

## 3. Backup configuration
Schedule, retention, encryption, storage location, immutability settings.

## 4. Playbooks
- Full-region outage
- Data corruption / bad deploy
- Ransomware / malicious deletion
- Accidental deletion

## 5. Roles and decision authority
Who calls the DR event, who executes, who communicates, escalation path.

## 6. Drill schedule and evidence log
Last drill date, next drill date, outcomes, issues found, links to drill reports.

## 7. Dependencies
Upstream / downstream services affected by a DR event here; their DR tier.

## 8. Compliance mapping
SOC 2 TSC clauses, GDPR Article 32 statement.
```

### Drill calendar (quarterly rhythm)

```
Q1 — Tabletop for all Tier 1 systems
Q2 — Real restore into staging for payments-api (Tier 1) + reports-service (Tier 2)
Q3 — Tabletop for all Tier 1 systems; ransomware restore drill for payments-api
Q4 — Annual full-region failover exercise: payments-api + customer-portal to eu-central-1
```

---

## Skill execution log

Every firing appends one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] disaster-recovery | outcome: OK|BLOCKED|PARTIAL | next: <skill> | note: <brief>
```

Examples:

```
[2026-04-20] disaster-recovery | outcome: OK | next: documentation-system-design | note: DR plan written for payments-api, Tier 1, active-active
[2026-04-20] disaster-recovery | outcome: PARTIAL | next: disaster-recovery | note: Q2 restore drill found 42min restore vs 1h target; schema mismatch in backup — open issue
```

---

## Reference files

Heavy material lives in `references/` and loads on demand:

- `references/rto-rpo-framework.md` — tier-decision worksheets, RTO/RPO selection heuristics, cost/benefit per pattern, cloud-specific mappings (AWS / GCP / Azure)
- `references/backup-strategy-patterns.md` — concrete backup patterns per data store (Postgres, MySQL, DynamoDB, S3, Kafka), 3-2-1 worked examples, immutable backup configuration (S3 Object Lock, Azure immutable blob, GCS bucket lock)
- `references/dr-drill-runbook.md` — runbook template, tabletop script, real-restore drill script, full-region failover script, ransomware restore script, post-drill report template
