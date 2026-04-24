# Migration pre-deployment checklist

Run this checklist for every migration before it runs against production. A migration that has not passed every item is not ready to deploy.

---

## 1. Classification

- [ ] Migration type identified: Additive / Subtractive / Data migration / Breaking change
- [ ] If breaking change: expand-contract pattern applied — never Stage 1 and Stage 3 in the same deployment
- [ ] If data migration: confirmed it is a separate file from the schema migration

---

## 2. File requirements

- [ ] One logical change per migration file (not bundled with unrelated changes)
- [ ] Up migration present and correct
- [ ] Down migration present — or explicitly documented as "DATA LOSS: cannot reverse" with approval obtained
- [ ] Migration is idempotent: uses `IF NOT EXISTS` / `IF EXISTS` guards, safe to run twice
- [ ] No `CREATE INDEX` without `CONCURRENTLY` on a production table
- [ ] No raw `ALTER TABLE` that causes a full table rewrite on a large table
- [ ] Data migrations use batching — no single `UPDATE` against millions of rows

---

## 3. Testing

- [ ] Tested on a production data snapshot, not a minimal dev schema
- [ ] Lock duration measured on representative data volume — result documented in the migration plan
- [ ] Up + Down cycle passes in CI against a clean database
- [ ] CI lock-duration check passes (no locks > 5 seconds)
- [ ] Data integrity verified: expected rows transformed, no unexpected NULLs or constraint violations

---

## 4. Staging run

- [ ] Migration applied in staging successfully
- [ ] Staging run time recorded (include in migration plan)
- [ ] Application is healthy in staging after migration (errors, latency, key business metrics)
- [ ] If data migration: backfill job completed or is progressing correctly in staging

---

## 5. Rollback strategy

- [ ] Rollback plan written before production deployment begins
- [ ] If rollback requires a compensating migration: compensating migration is written and tested in staging
- [ ] If Down is "data loss": explicit approval from a second engineer obtained and recorded

---

## 6. Review

- [ ] Migration SQL reviewed by a second engineer (treat as production code)
- [ ] Migration plan entry written (see SKILL.md Output format)
- [ ] If subtractive or breaking change: deployment sequence confirmed (application code deploy first, then migration)

---

## 7. Production deployment

- [ ] Deployment window confirmed (low-traffic period for risky migrations)
- [ ] Monitoring in place: error rate, latency, connection pool saturation, replication lag
- [ ] Someone is watching the dashboards for 10–15 minutes after the migration runs
- [ ] Rollback is a reachable action — team knows the command and has tested it in staging

---

## Lock duration quick reference

| Operation | Typical lock duration | Blocks reads? | Blocks writes? |
|-----------|----------------------|---------------|---------------|
| `ADD COLUMN` nullable, no default (PG 11+) | < 100ms | Briefly | Briefly |
| `ADD COLUMN` with volatile default (PG < 11) | Minutes on large tables | Yes | Yes |
| `DROP COLUMN` | < 100ms | Briefly | Briefly |
| `CREATE INDEX` (no CONCURRENTLY) | Minutes on large tables | No | Yes |
| `CREATE INDEX CONCURRENTLY` | No lock (takes longer to build) | No | No |
| `ADD CONSTRAINT NOT VALID` | < 100ms | Briefly | Briefly |
| `VALIDATE CONSTRAINT` | Duration of table scan | No | No |
| `ALTER TABLE` (full rewrite) | Minutes to hours on large tables | Yes | Yes |
| Batched `UPDATE` (1 000 rows/batch) | < 10ms per batch | No | No |

---

## Escalation criteria

Stop the migration and escalate to the team if:

- Lock duration exceeds 30 seconds in production
- Replication lag starts climbing during a data migration
- Error rate increases after the migration runs
- The Down migration fails in staging
- Connection pool saturation increases unexpectedly
