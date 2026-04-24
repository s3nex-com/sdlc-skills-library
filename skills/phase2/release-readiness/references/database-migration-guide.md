# Database migration guide

## Why migrations are the highest-risk part of a deployment

Code can be rolled back in seconds — deploy the previous image and the new code is gone. Schema changes are not that simple. Once a migration runs against a production database, the schema has changed. Rolling back the application code does not undo the schema change; the old code is now running against a schema it may not understand.

This asymmetry is what makes migrations dangerous. A poorly written migration can:

- Lock a table for minutes, blocking all reads and writes
- Run a data transformation that corrupts records in ways not immediately obvious
- Leave the schema in a state the old application code cannot handle, making a code rollback impossible without a compensating migration
- On large tables, run so long that it causes replication lag, connection pool exhaustion, or OOM on the database server

The solution is not to avoid migrations — schema evolution is unavoidable. The solution is to write migrations that are **backward-compatible**, **lock-free where possible**, and **reversible**. The expand-contract pattern is the primary technique for achieving this.

---

## Zero-downtime migration: the expand-contract pattern

The expand-contract pattern (also called parallel change) ensures that at no point during a deployment is there a schema state that breaks either the old or new application code. It works by splitting what feels like one change into three deployment phases.

### Worked example: renaming a column (`device_name` → `device_label`)

A naive approach — `ALTER TABLE devices RENAME COLUMN device_name TO device_label` — would break old application code the moment it runs. The expand-contract approach takes three deploys:

---

**Phase 1: Expand**

Add the new column alongside the old one. The old column still exists; old application code continues to work unchanged.

```sql
-- Migration: add device_label as nullable (no constraint yet)
ALTER TABLE devices ADD COLUMN device_label TEXT;
```

Deploy old application code — it only reads and writes `device_name`. This deploy is safe and fully reversible (just `DROP COLUMN device_label`).

---

**Phase 2: Migrate (dual-write)**

Deploy new application code that writes to **both** `device_name` and `device_label` on every write, and reads from `device_label` (falling back to `device_name` if null). Separately, run a backfill job to populate `device_label` for all existing rows.

```sql
-- Backfill: copy existing data to new column (run as a background job, batched)
UPDATE devices SET device_label = device_name WHERE device_label IS NULL;
```

At this point:
- New writes go to both columns
- Old rows have been backfilled
- Both old and new code versions work against this schema

If you need to roll back, redeploy the Phase 1 code — it only reads `device_name`, which still exists.

---

**Phase 3: Contract**

Once all application instances are running Phase 2 code and the backfill is complete, drop the old column.

```sql
-- Migration: drop the old column
ALTER TABLE devices DROP COLUMN device_name;
```

Deploy application code that only reads and writes `device_label`.

Rolling back after Phase 3 requires a compensating migration to add `device_name` back. At this point, rolling back should be unnecessary — the migration is complete and the risk window has passed.

---

### Expand-contract summary

| Phase | Schema state | Application code | Rollback risk |
|-------|-------------|-----------------|---------------|
| 1 — Expand | Old + new column (new is nullable) | Old code only | Low — just drop new column |
| 2 — Migrate | Old + new column (both populated) | Dual-write code | Low — redeploy Phase 1 code |
| 3 — Contract | New column only | New code only | Very low — migration complete |

---

## Tooling

### Alembic (Python / SQLAlchemy)

**Key features:** Python-native; auto-generates migration scripts from model diff; supports both `upgrade` and `downgrade` functions; integrates tightly with SQLAlchemy models.

```bash
# Generate a new migration from model changes
alembic revision --autogenerate -m "add_device_label_column"

# Run all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade abc123
```

**Down migration example:**
```python
def downgrade() -> None:
    op.drop_column("devices", "device_label")
```

---

### golang-migrate

**Key features:** Language-agnostic (plain SQL files); supports many database drivers; works well in Go services and Docker-based deployments; simple numbered file convention.

```bash
# Apply all up migrations
migrate -path ./migrations -database "postgres://..." up

# Roll back one step
migrate -path ./migrations -database "postgres://..." down 1

# Apply up to a specific version
migrate -path ./migrations -database "postgres://..." goto 5
```

Migration files are named `000001_add_device_label.up.sql` and `000001_add_device_label.down.sql`.

---

### Flyway (Java / JVM)

**Key features:** Convention-based versioned migrations; supports Java and SQL; integrates with Maven/Gradle; strong enterprise adoption; built-in baseline support for brownfield databases.

```bash
# Run pending migrations
flyway migrate

# Validate applied migrations match the filesystem
flyway validate

# Roll back (Flyway Teams only — undo scripts)
flyway undo
```

Migration files: `V1__Add_device_label_column.sql`, `U1__Add_device_label_column.sql` (undo).

---

### Liquibase

**Key features:** Database-agnostic changelogs in SQL, XML, YAML, or JSON; strong rollback support; diff and snapshot tooling; good for multi-database targets.

```bash
# Apply pending changesets
liquibase update

# Roll back last N changesets
liquibase rollbackCount 1

# Generate rollback SQL without running it
liquibase rollbackCountSQL 1
```

---

### Prisma Migrate (Node.js)

**Key features:** Tightly coupled to Prisma ORM schema; auto-generates migrations from schema diff; shadow database for safe migration generation; good developer experience for Node.js services.

```bash
# Create and apply a new migration
npx prisma migrate dev --name add_device_label

# Apply migrations in production (no interactive prompts)
npx prisma migrate deploy

# Reset database and re-apply all migrations (dev only)
npx prisma migrate reset
```

---

## Migration safety checklist

Run through this checklist before every migration that will execute against production:

- [ ] Migration tested on staging with a production-volume data snapshot
- [ ] Runtime measured — estimated impact on production understood (seconds, minutes, or longer?)
- [ ] Lock-free where possible — no table-level locks that block reads/writes on busy tables
- [ ] Backward compatible — old application code still works against the new schema
- [ ] Down migration written and tested — a `downgrade` or `.down.sql` that restores the previous state
- [ ] No irreversible data transformation without an explicit backup step taken first
- [ ] Large table migrations batched — not a single `UPDATE` on millions of rows
- [ ] Reviewed by a second engineer — migration SQL is load-bearing; treat it like production code

---

## Common dangerous patterns and how to avoid them

### Dropping columns

**Danger:** If the application code still references the column (ORM model, raw query, SELECT *), dropping the column breaks the application immediately — even if no code path actively uses the value.

**Safe approach:** Expand-contract. Remove the column from application code and deploy first. Confirm the column is no longer referenced in any running instance. Then drop the column in a separate migration.

---

### Renaming columns

**Danger:** A direct `RENAME COLUMN` breaks old code the moment it runs. Rolling back requires renaming again, which may not be possible if data has been written under the new name.

**Safe approach:** Expand-contract (see worked example above). Never rename directly.

---

### Adding NOT NULL columns

**Danger:** `ALTER TABLE ADD COLUMN col TEXT NOT NULL` with no default will fail if any existing rows would violate the constraint. Even with a default, some databases take a table rewrite for this operation.

**Safe approach:**
1. Add the column as nullable (`ALTER TABLE ADD COLUMN col TEXT`)
2. Backfill all existing rows
3. Add the `NOT NULL` constraint in a separate step once all rows have values

```sql
-- Step 1: add nullable
ALTER TABLE devices ADD COLUMN device_label TEXT;

-- Step 2: backfill (batched — see batching section)
UPDATE devices SET device_label = device_name WHERE device_label IS NULL;

-- Step 3: add constraint (PostgreSQL: use NOT VALID + VALIDATE for large tables)
ALTER TABLE devices ALTER COLUMN device_label SET NOT NULL;
```

---

### Large table rebuilds

**Danger:** `ALTER TABLE` on a table with tens of millions of rows can hold an exclusive lock for minutes while PostgreSQL rewrites the table on disk. All reads and writes block.

**Safe approach:** Use `pg-online-schema-change` (pg_osc) or `gh-ost` (MySQL) for large table DDL. These tools perform the schema change by creating a new table, copying rows in batches while keeping the old table live, then atomically swapping the tables.

---

### Index creation

**Danger:** `CREATE INDEX` takes a `ShareLock` that blocks writes for the duration of the build. On a large table, this can take hours.

**Safe approach:** Always use `CREATE INDEX CONCURRENTLY` in PostgreSQL. It takes no exclusive lock — it builds the index while the table remains fully readable and writable. It is slower and cannot run inside a transaction, but it is always the right choice for production.

```sql
-- Always use CONCURRENTLY for production index creation
CREATE INDEX CONCURRENTLY idx_devices_device_label ON devices(device_label);
```

---

### Constraint addition

**Danger:** `ALTER TABLE ADD CONSTRAINT ... CHECK (...)` scans the entire table to validate existing rows. On large tables, this holds a lock for the duration of the scan.

**Safe approach in PostgreSQL:** Add the constraint as `NOT VALID` first (no scan, no lock), then validate it in a separate step. The `VALIDATE CONSTRAINT` step only takes a `ShareUpdateExclusiveLock`, which does not block reads or writes.

```sql
-- Step 1: add constraint without scanning existing rows (fast, minimal lock)
ALTER TABLE devices ADD CONSTRAINT chk_label_not_empty 
  CHECK (device_label <> '') NOT VALID;

-- Step 2: validate existing rows (takes ShareUpdateExclusiveLock — reads/writes continue)
ALTER TABLE devices VALIDATE CONSTRAINT chk_label_not_empty;
```

---

## Batching large data migrations

Never run a single `UPDATE` against millions of rows. It holds a lock for the entire duration, generates a massive write-ahead log entry, and may time out or cause replication lag. Batch instead.

```python
# Safe: batch update instead of UPDATE all rows at once
BATCH_SIZE = 1000
offset = 0
while True:
    updated = db.execute("""
        UPDATE telemetry_events 
        SET device_label = device_name 
        WHERE device_label IS NULL 
        LIMIT :batch_size
    """, {"batch_size": BATCH_SIZE}).rowcount
    if updated == 0:
        break
    db.commit()
    time.sleep(0.1)  # Brief pause to avoid overwhelming the DB
```

Key properties of this pattern:
- Each batch is a small transaction — lock is held for milliseconds, not minutes
- `WHERE device_label IS NULL` makes the query idempotent — safe to retry or resume if interrupted
- The `time.sleep(0.1)` gives the database headroom; adjust based on observed load
- `updated == 0` is the natural termination condition — no need to count rows upfront

For very large tables (hundreds of millions of rows), run this as a background job during off-peak hours, not as part of the deployment pipeline.

---

## Testing migrations

The migration SQL is production code. Test it like production code.

### Forward migration test

Apply the migration against a test database; verify the schema matches expectations:

```python
def test_add_device_label_column(migrated_db):
    """Forward migration: device_label column exists and is nullable."""
    columns = get_columns(migrated_db, "devices")
    assert "device_label" in columns
    assert columns["device_label"].nullable is True
    assert columns["device_label"].type == TEXT
```

### Backward migration test

Apply the migration, then apply the down migration; verify the schema is restored:

```python
def test_add_device_label_column_rollback(test_db):
    """Down migration restores the schema to its pre-migration state."""
    apply_migration(test_db, "add_device_label")
    assert "device_label" in get_columns(test_db, "devices")

    rollback_migration(test_db, "add_device_label")
    assert "device_label" not in get_columns(test_db, "devices")
```

### Data integrity test

Apply the migration against a database seeded with realistic data; verify data is correctly transformed:

```python
def test_backfill_device_label(seeded_db):
    """Backfill migration: device_label populated from device_name for all existing rows."""
    apply_migration(seeded_db, "backfill_device_label")
    rows_with_null_label = seeded_db.execute(
        "SELECT COUNT(*) FROM devices WHERE device_label IS NULL"
    ).scalar()
    assert rows_with_null_label == 0
```

### Performance test

Measure how long the migration takes on a production-size dataset before running it in production:

```python
def test_migration_runtime_on_large_dataset(large_db, benchmark):
    """Migration completes in under 30 seconds on 10M rows."""
    result = benchmark(apply_migration, large_db, "add_device_label")
    assert benchmark.stats["mean"] < 30.0
```

If the migration takes longer than your deployment tolerance, switch to the batched approach.

---

## PostgreSQL-specific guidance

### CREATE INDEX CONCURRENTLY

Always use `CONCURRENTLY` for production index creation. It cannot run inside a transaction, so it must be a standalone statement — not inside a `BEGIN ... COMMIT` block.

```sql
-- In a migration that creates an index: do NOT wrap in a transaction
CREATE INDEX CONCURRENTLY idx_devices_device_label ON devices(device_label);
```

Alembic note: use `postgresql_concurrently=True` and disable the transaction wrapper:
```python
def upgrade():
    with op.get_context().autocommit_block():
        op.create_index(
            "idx_devices_device_label",
            "devices",
            ["device_label"],
            postgresql_concurrently=True
        )
```

---

### Lock levels for common operations

| Operation | Lock acquired | Blocks reads? | Blocks writes? |
|-----------|--------------|---------------|---------------|
| `SELECT` | AccessShareLock | No | No |
| `INSERT / UPDATE / DELETE` | RowExclusiveLock | No | No (concurrent writes allowed) |
| `CREATE INDEX CONCURRENTLY` | ShareUpdateExclusiveLock | No | No |
| `CREATE INDEX` (without CONCURRENTLY) | ShareLock | No | **Yes** |
| `ALTER TABLE ADD COLUMN` (nullable, no default) | AccessExclusiveLock | **Yes** | **Yes** |
| `ALTER TABLE ADD COLUMN` (with default, PostgreSQL 11+) | AccessExclusiveLock | **Yes** | **Yes** (briefly — metadata-only) |
| `ALTER TABLE DROP COLUMN` | AccessExclusiveLock | **Yes** | **Yes** |
| `TRUNCATE` | AccessExclusiveLock | **Yes** | **Yes** |
| `VACUUM FULL` | AccessExclusiveLock | **Yes** | **Yes** |

PostgreSQL 11+ made adding a column with a volatile default much faster (metadata-only operation), but the lock is still briefly taken. For high-traffic tables, plan migrations during low-traffic windows even for "fast" operations.

---

### VALIDATE CONSTRAINT separately

```sql
-- Fast (no table scan; takes brief AccessExclusiveLock for the metadata change only)
ALTER TABLE devices ADD CONSTRAINT chk_label_not_empty 
  CHECK (device_label <> '') NOT VALID;

-- Slower (scans existing rows) but takes only ShareUpdateExclusiveLock
-- Reads and writes continue during this step
ALTER TABLE devices VALIDATE CONSTRAINT chk_label_not_empty;
```

---

### Monitoring migration progress with pg_stat_activity

```sql
-- See what migrations are currently running and how long they've been running
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE query NOT LIKE '%pg_stat_activity%'
  AND state = 'active'
ORDER BY duration DESC;

-- Check for blocking locks during a migration
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
    ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.cardinality(pg_blocking_pids(blocked.pid)) > 0;
```

Use these queries to confirm a migration is progressing and to detect unexpected lock contention before it becomes an incident.
