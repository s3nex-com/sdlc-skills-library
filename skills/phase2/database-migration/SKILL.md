---
name: database-migration
description: >
  database migration, schema migration, schema change, alter table, add column,
  drop column, rename column, migrate data, backfill, expand contract, forward migration,
  backward compatible schema, migration rollback, zero downtime migration, table lock,
  index concurrently, data migration, migration checklist, migration plan, alembic,
  golang-migrate, flyway, prisma migrate, liquibase, production schema change
---

## Purpose

Guides schema migrations from classification through production deployment. Migrations are the highest-risk operation a team performs: code rolls back in seconds, schema changes do not. A poorly written migration can lock a table for minutes, corrupt data silently, or strand the application in a state where rolling back the code is impossible without a compensating migration. This skill enforces forward-only discipline — migrations that are backward-compatible, lock-free where possible, and built to survive a rollback of application code without a corresponding schema rollback.

---

## When to use

- Adding, modifying, or removing any column, table, index, or constraint in a production database
- Planning a column rename or type change (both require the expand-contract pattern)
- Backfilling data into a newly added column
- Moving or transforming large volumes of existing data
- Adding an index to a table with significant production traffic
- Reviewing a migration PR for safety before it merges
- Deciding the production deployment sequence for a change that involves both a code and schema change

---

## When NOT to use

- **Seed data and reference data loads**: inserting static lookup tables or test fixtures. Use your migration tool's seed mechanism, not a schema migration file.
- **Application-level data transformations** (reformatting a field in code, normalising values in memory): these are code changes, not schema migrations.
- **Schema design decisions** (should this be a separate table? should this be normalised?): that is architecture work — use `design-doc-generator` or `architecture-decision-records`.
- **Feature flags that change query behaviour**: use `feature-flag-lifecycle`.
- **Release sequencing and go/no-go decisions**: use `release-readiness`. This skill produces the migration plan and safety gate; `release-readiness` owns the overall go/no-go.

---

## Process

### Step 1 — Classify the migration

Classify before writing any SQL. The classification determines the deployment pattern.

| Type | Examples | Default approach |
|------|----------|-----------------|
| **Additive** (safe) | Add nullable column, add table, `CREATE INDEX CONCURRENTLY` | Single-stage deploy |
| **Subtractive** (dangerous) | Drop column, drop table | Expand-contract — three separate deploys |
| **Data migration** (risky) | Backfill, transform existing rows | Separate from schema changes; run as batched job |
| **Breaking change** | Rename column, change type, remove what running code reads | Expand-contract required — no exceptions |

If the migration touches something the current application code reads or writes, it is a breaking change until proven otherwise.

---

### Step 2 — Apply expand-contract for breaking changes

Never combine the addition of a new schema object and the removal of the old one in one deployment. Split into three stages, each its own deployment:

**Stage 1 — Expand:** Add the new thing alongside the old. Old code still works unchanged. This stage is fully reversible.

**Stage 2 — Migrate:** Backfill data into the new structure. Deploy code that writes to both old and new. Old code can still be redeployed without breaking anything.

**Stage 3 — Contract:** Deploy code that only uses the new structure. Remove the old structure. Rolling back after this stage requires a compensating migration, so only do it when the change is confirmed stable.

See `references/expand-contract-guide.md` for a worked example with SQL and application code at each stage.

---

### Step 3 — Write the migration file

Every migration file must satisfy these requirements before it is reviewed:

1. **One logical change per file.** Never bundle an index creation with a column add with a backfill. Three concerns = three files.

2. **Up and Down must both be present.** If Down cannot restore the previous state (e.g. a backfill that cannot be cleanly reversed), write `-- DATA LOSS: cannot reverse. Requires manual recovery.` and flag for explicit approval.

3. **Idempotent.** Use `IF NOT EXISTS` for additions, `IF EXISTS` for removals. A migration must be safe to run twice.

4. **No table-locking operations on busy tables.**
   - Indexes: always `CREATE INDEX CONCURRENTLY` — never without `CONCURRENTLY` on a production table.
   - Large table DDL: use `pg-online-schema-change` (pg_osc) or `gh-ost` (MySQL) — not a raw `ALTER TABLE` on tens of millions of rows.
   - Constraints: add as `NOT VALID` first, then `VALIDATE CONSTRAINT` separately.

5. **Data migrations must be batched.** A single `UPDATE` on millions of rows holds a lock for minutes. Batch by 1 000–10 000 rows, commit between batches, and leave a short sleep between iterations.

---

### Step 4 — Pre-deployment checklist

Run every item before the migration touches production. Full checklist in `references/migration-checklist.md`.

- [ ] Migration tested on a production data snapshot (not a toy dev database)
- [ ] Lock duration estimated — know whether it is milliseconds or minutes
- [ ] Rollback strategy written. If Down is "data loss", explicit approval obtained
- [ ] Staging run completed and timed
- [ ] Second engineer has reviewed the migration SQL — treat it as production code
- [ ] CI has run: Up + Down cycle passes against a clean database; no locks > 5 s detected

---

### Step 5 — CI validation

Every migration must pass CI before it is mergeable:

1. Apply Up migration against a clean test database — must complete without error.
2. Apply Down migration — must restore the schema cleanly.
3. Lock duration check: any migration that holds a table lock for more than 5 seconds fails the build. Instrument this with `pg_stat_activity` or equivalent.
4. For data migrations: seed the test database with representative volume (at minimum 100 000 rows) and verify the batching logic terminates correctly.

---

### Step 6 — Production deployment sequence for risky migrations

For any migration classified as subtractive, breaking, or data migration:

1. Deploy new application code that works with **both** old and new schema.
2. Run the migration against production.
3. Watch error rates, latency, and connection pool metrics for 10–15 minutes.
4. If healthy: proceed. If not: application code still works with the old schema — rollback the migration.
5. (Later sprint) Deploy code that only uses the new schema.
6. (Later still) Run the Contract stage migration to remove old schema objects.

For additive migrations with no lock risk: standard single-stage deploy is fine.

---

### Step 7 — Log the migration plan

Before the migration runs in production, write a migration plan entry (see Output format). This is the paper trail that `release-readiness` and the post-mortem skill can reference.

---

## Output format

### Migration plan entry

```
Migration: add_telemetry_partition_key
Type: Additive
Risk: Low
Lock duration estimate: < 1s (non-blocking — CREATE INDEX CONCURRENTLY)
Rollback: DROP INDEX CONCURRENTLY idx_telemetry_partition_key
Staging run: ✓ 2026-04-15 — 847ms, no locks detected
Production sequence: single-stage deploy
Approval: not required (additive, lock-free)
```

```
Migration: rename_device_name_to_device_label (Stage 1 of 3 — Expand)
Type: Breaking change — expand-contract
Risk: Medium
Lock duration estimate: < 100ms (ADD COLUMN nullable — metadata only in PG 11+)
Rollback: DROP COLUMN device_label
Staging run: ✓ 2026-04-17 — 43ms, no locks
Production sequence: expand-contract Stage 1 of 3
Approval: not required for Stage 1 — fully reversible
```

### CI output (what a passing migration run looks like)

```
[CI] migration: add_telemetry_partition_key
  ✓ Up migration applied in 847ms
  ✓ Down migration applied in 12ms
  ✓ Schema restored after Down
  ✓ Max lock duration: 0ms (CONCURRENTLY — no lock)
  ✓ All checks passed
```

---

## Skill execution log

Append one line to `docs/skill-log.md` each time this skill fires:

```
[YYYY-MM-DD] database-migration | outcome: OK|BLOCKED|PARTIAL | next: <next action> | note: <one-line summary>
```

Examples:
```
[2026-04-20] database-migration | outcome: OK | next: run in staging | note: classified add_telemetry_partition_key as additive; migration plan written
[2026-04-20] database-migration | outcome: BLOCKED | next: needs expand-contract split | note: drop_device_name rejected — app code still references column; must do Stage 1 first
[2026-04-20] database-migration | outcome: PARTIAL | next: Stage 2 in next sprint | note: Stage 1 (Expand) complete and stable; backfill job running in background
```

---

## Reference files

`skills/phase2/database-migration/references/migration-checklist.md` — pre-deployment safety checklist; run before every migration that touches production.

`skills/phase2/database-migration/references/expand-contract-guide.md` — detailed expand-contract walkthrough with SQL and application code examples at each stage, including the column rename worked example.

`skills/phase2/release-readiness/references/database-migration-guide.md` — full reference covering tooling (Alembic, golang-migrate, Flyway, Prisma Migrate, Liquibase), PostgreSQL lock levels, batching patterns, and test patterns for migration correctness and performance.
