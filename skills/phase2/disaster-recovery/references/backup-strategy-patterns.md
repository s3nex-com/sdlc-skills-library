# Backup strategy patterns

Concrete patterns per data store. Load when SKILL.md step 3 (pick a backup strategy) applies.

---

## The 3-2-1 rule, plus immutable

**3-2-1:** 3 copies of the data, on 2 different media / storage classes, with at least 1 off-site.

**Modern extension:** at least one of those copies is **immutable** (write-once, time-locked retention) or **air-gapped** (cannot be reached by an IAM role that can reach production).

Why: ransomware and insider threats compromise the IAM plane. A backup your production admin can delete is not a backup against those threats.

### Worked example — Postgres primary in AWS

- **Copy 1:** live primary in eu-west-1 (not counted for DR)
- **Copy 2:** automated snapshots + WAL archive in same region, 35-day retention — fast restore
- **Copy 3:** cross-region copy of snapshots in eu-central-1 — region-outage protection
- **Copy 4 (the immutable):** monthly snapshot exported to S3 in a **separate AWS account** under **Object Lock compliance mode**, 7-year retention

Total: 3 DR copies on 2+ storage classes (EBS-backed RDS snapshot, S3 Standard, S3 Object Lock), in 2 regions, with one immutable and one cross-account. That defends region outage, corruption, ransomware, and insider threat.

---

## Backup types

| Type | Contents | Pros | Cons | Use case |
|------|----------|------|------|----------|
| **Full** | Everything | Simple, single-file restore | Slow, storage-heavy | Baseline; periodic reference point |
| **Incremental** | Changes since last backup (full or incremental) | Fast, small | Long restore chain; chain breaks if any link corrupt | Daily backups of large data sets |
| **Differential** | Changes since last full | Single-chain restore (full + latest diff) | Grows until next full | Middle ground for medium-sized DBs |
| **Continuous (WAL / CDC)** | Every transaction | Tight RPO (seconds) | Infra + storage cost | Tier 1 RPO targets |

**Typical schedule for Tier 1 relational DB:** weekly full + daily incremental + continuous WAL shipping. Restore = last full + intervening incrementals + WAL replay to target time.

---

## Per-data-store patterns

### Postgres

- **Automated tooling:** RDS / Aurora snapshots; `pgbackrest` or `wal-g` for self-managed.
- **Tight RPO:** continuous WAL archive to S3 with 1-minute archive_timeout.
- **Point-in-time restore:** enabled by default with WAL archive. Test it regularly — it is the restore path for data corruption, not region outage.
- **Logical vs physical:** physical (pg_basebackup / snapshot) for DR; logical (pg_dump) for selective restore / cross-version.

```bash
# pgbackrest full backup example
pgbackrest --stanza=main --type=full backup

# Restore to point in time
pgbackrest --stanza=main --type=time \
  --target="2026-04-19 14:30:00+00" restore
```

### MySQL

- **Automated tooling:** RDS snapshots; `xtrabackup` (Percona) for self-managed.
- **Continuous:** binlog shipping.
- **Gotcha:** GTID must be enabled for reliable cross-region replication and PITR.

### DynamoDB

- **Point-in-time recovery (PITR):** 35-day rolling window; enable on every Tier 1/2 table.
- **On-demand backups:** for long-retention needs; export to S3 for immutable storage.
- **Global Tables:** multi-region active-active, but not a backup — a replica. Corruption propagates. Combine with PITR.

### S3 / object storage

- **Versioning:** on. Every write keeps prior version. Deletes become tombstones, not destruction.
- **Cross-region replication (CRR):** replicate to a second region, ideally a second account.
- **Object Lock (compliance mode):** for the immutable copy. Compliance mode means even the root user cannot shorten retention during the period. Governance mode allows privileged override — not suitable as the final ransomware defence.
- **Lifecycle:** transition older versions to Glacier / Deep Archive to control cost.

### Kafka / event logs

- **Topic replication factor ≥ 3** within a cluster is not DR — it is HA.
- **MirrorMaker 2 or Confluent Replicator** to a second region for DR.
- **Tiered storage** (Confluent Tiered Storage, Warpstream, Redpanda) offloads old segments to S3 — include that S3 in your backup scope.
- **Consumer offsets** must replicate too, or consumers will reprocess / skip after failover.

### Redis / in-memory

- **Persistence:** RDB snapshots + AOF log.
- **If used as cache only:** DR may be "rebuild from source" rather than restore.
- **If used as primary store (rare, sometimes in session stores):** treat as Tier 1 data store, replicate snapshots off-site.

### Secret stores (Vault, AWS Secrets Manager)

- Often missed in DR plans. Restoring app services without secrets is useless.
- Secrets Manager replicates across regions natively; enable it.
- Vault: snapshot the Raft backend and encrypt the snapshot with a separate root-key set.

### Git / source control

- Production source is also "data of record" for recovery. If GitHub is down and your DR needs the latest migration script, that script must exist elsewhere.
- Mirror critical repos to a second provider or self-hosted Gitea on a schedule.

---

## Immutable backup configuration

### S3 Object Lock — compliance mode

```hcl
resource "aws_s3_bucket" "backups_immutable" {
  bucket = "payments-backups-immutable"
  object_lock_enabled = true
}

resource "aws_s3_bucket_object_lock_configuration" "backups_immutable" {
  bucket = aws_s3_bucket.backups_immutable.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = 2555  # 7 years
    }
  }
}
```

Crucially: the IAM principal that writes backups must NOT have `s3:BypassGovernanceRetention`. Separate roles for write and restore.

### Azure immutable blob

Set a time-based retention policy on the container. Locked policies cannot be reduced.

### GCS bucket lock

Retention policy + `gcloud storage buckets update --lock-retention-policy`. Once locked, retention cannot be reduced or removed.

---

## Encryption and access separation

- **Encryption at rest:** always on. Prefer customer-managed keys (KMS CMK) for Tier 1.
- **Key separation:** the KMS key that encrypts backups lives in a different account / project from the one protecting production data. Compromise of one side does not compromise the other.
- **IAM separation:**
  - Backup-write role: can write, cannot delete, cannot modify retention.
  - Backup-read / restore role: can read and initiate restore, cannot write or delete.
  - Backup-admin role: can manage lifecycle — held by a small, audited group; MFA required.
- **Alerting:** CloudTrail / Cloud Audit Logs alert on any `DeleteBackup`, `DeleteObjectVersion`, or retention-modification API call in the backup account.

---

## Restore testing cadence, by copy

A backup that has never been restored is not a backup. For each copy defined above:

| Copy | Test what | Cadence |
|------|-----------|---------|
| Local snapshots (Copy 2) | Full restore into non-prod | Monthly |
| Cross-region (Copy 3) | Restore into DR region non-prod | Quarterly |
| Immutable (Copy 4) | Restore into isolated account | Semi-annual; more often after ransomware scares |

Record each test in the drill log: restore duration, issues found, integrity verification result.

---

## Common failure modes observed in real restores

- Schema drift: the backup restores, but application migrations have not been applied in the DR environment.
- Secrets missing: the app starts, cannot decrypt, fails readiness.
- Time skew: certificates invalid because the restored node clock drifted during the outage.
- IAM role mismatch: restored service tries to assume a role that only exists in primary region.
- Downstream replication lag: the restored DB is up, but consumers (search indexers, data warehouse ETL) are hours behind and emit stale results.

Each of these should appear as a check in the restore verification checklist (SKILL.md step 8).
