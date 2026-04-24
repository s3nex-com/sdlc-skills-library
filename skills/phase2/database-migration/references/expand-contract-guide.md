# Expand-contract pattern

The expand-contract pattern (also called parallel change) is the primary technique for making breaking schema changes without downtime. It works by splitting what looks like one change into three separate deployments, ensuring that at no point is there a schema state that breaks either the old or new application code.

Use this pattern for any change that removes or renames something the running application currently reads or writes.

---

## The three stages

| Stage | What changes | Application code | Schema state | Rollback cost |
|-------|-------------|-----------------|--------------|---------------|
| **1 — Expand** | Add new structure alongside old | Old code only; reads/writes old structure | Old + new (new is nullable or unused) | Drop the new thing — fully reversible |
| **2 — Migrate** | Backfill data; deploy dual-write code | Writes to both; reads from new (falls back to old) | Old + new (both populated) | Redeploy Stage 1 code — old structure still intact |
| **3 — Contract** | Remove old structure; deploy code that only uses new | New code only | New structure only | Requires a compensating migration |

Never combine Stage 1 and Stage 3 in one deployment. The intermediate state in Stage 2 is where each version of the application code can safely run. Remove that safety net too early and a rollback becomes impossible without a compensating migration.

---

## Worked example: renaming a column

### Scenario

`devices.device_name` is used throughout the application. The new name is `device_label`. A direct `RENAME COLUMN` breaks running application instances the moment it executes.

---

### Stage 1 — Expand

**Migration file:** `0012_add_device_label_column.up.sql`

```sql
-- Add new column alongside old column; nullable so no constraint violation on existing rows
ALTER TABLE devices
  ADD COLUMN IF NOT EXISTS device_label TEXT;
```

**Down migration:** `0012_add_device_label_column.down.sql`

```sql
ALTER TABLE devices
  DROP COLUMN IF EXISTS device_label;
```

**Application code:** no change. Old code continues to read and write `device_name` only. `device_label` is ignored.

**Deploy this stage and confirm the application is healthy before proceeding.**

---

### Stage 2 — Migrate

Two parallel actions, both required before Stage 3:

**Action A: backfill existing rows** (run as a background job, not inside the deployment pipeline for large tables)

```python
BATCH_SIZE = 5000
while True:
    updated = db.execute("""
        UPDATE devices
        SET device_label = device_name
        WHERE device_label IS NULL
        LIMIT :batch_size
    """, {"batch_size": BATCH_SIZE}).rowcount
    db.commit()
    if updated == 0:
        break
    time.sleep(0.05)  # Back off slightly to give the DB headroom
```

This is idempotent: `WHERE device_label IS NULL` means it is safe to stop and resume.

**Action B: deploy dual-write application code**

```python
def update_device(device_id: str, name: str) -> None:
    db.execute("""
        UPDATE devices
        SET device_name = :name,   -- keep old column populated for rollback safety
            device_label = :name
        WHERE id = :id
    """, {"name": name, "id": device_id})

def get_device_label(device: Row) -> str:
    # Read from new column; fall back to old if not yet backfilled
    return device.device_label or device.device_name
```

**At the end of Stage 2:**
- All existing rows have `device_label` populated
- All new writes go to both columns
- Rolling back to Stage 1 application code still works — `device_name` is fully current

---

### Stage 3 — Contract

Only proceed once:
- All application instances are running Stage 2 code
- The backfill is 100% complete (`SELECT COUNT(*) FROM devices WHERE device_label IS NULL` returns 0)
- Stage 2 has been stable for at least one full deployment cycle (ideally several days)

**Migration file:** `0014_drop_device_name_column.up.sql`

```sql
ALTER TABLE devices
  DROP COLUMN IF EXISTS device_name;
```

**Down migration:** `0014_drop_device_name_column.down.sql`

```sql
-- DATA LOSS: device_name values cannot be recovered after this point.
-- Compensating migration: re-add column and backfill from device_label.
ALTER TABLE devices
  ADD COLUMN IF NOT EXISTS device_name TEXT;

UPDATE devices SET device_name = device_label WHERE device_name IS NULL;
```

**Application code:** remove all references to `device_name`. Remove the dual-write logic and the fallback read.

```python
def update_device(device_id: str, name: str) -> None:
    db.execute("""
        UPDATE devices
        SET device_label = :name
        WHERE id = :id
    """, {"name": name, "id": device_id})

def get_device_label(device: Row) -> str:
    return device.device_label
```

**Deploy code first, then run the Stage 3 migration.** Confirm the application is healthy before running the migration.

---

## Worked example: adding a NOT NULL column

A direct `ALTER TABLE ADD COLUMN col TEXT NOT NULL` fails if any existing row would violate the constraint. Even with a DEFAULT, some database versions do a full table rewrite.

### Stage 1 — Expand

```sql
-- Add as nullable; no constraint, no table rewrite
ALTER TABLE events
  ADD COLUMN IF NOT EXISTS severity TEXT;
```

### Stage 2 — Migrate

Backfill with the intended default value:

```sql
-- Batched backfill (use the Python loop pattern above for large tables)
UPDATE events
SET severity = 'info'
WHERE severity IS NULL;
```

Deploy application code that always writes `severity` on new inserts.

### Stage 3 — Contract

Add the NOT NULL constraint once all rows have a value. In PostgreSQL: use `NOT VALID` + `VALIDATE CONSTRAINT` to avoid a full-table lock during validation.

```sql
-- Step 1: add the constraint without scanning existing rows (brief lock only)
ALTER TABLE events
  ALTER COLUMN severity SET NOT NULL;
```

For large tables where even the brief lock is a concern, use the two-step approach:

```sql
-- Step 1: add constraint without scanning existing rows
ALTER TABLE events
  ADD CONSTRAINT chk_severity_not_null
  CHECK (severity IS NOT NULL) NOT VALID;

-- Step 2: validate existing rows (takes ShareUpdateExclusiveLock — reads/writes continue)
ALTER TABLE events
  VALIDATE CONSTRAINT chk_severity_not_null;

-- Step 3: once validated, set the actual NOT NULL
ALTER TABLE events
  ALTER COLUMN severity SET NOT NULL;

ALTER TABLE events
  DROP CONSTRAINT chk_severity_not_null;
```

---

## When the pattern is not needed

Not every migration requires expand-contract:

- **Adding a nullable column with no default**: safe as a single migration. Old code ignores the new column.
- **Adding a new table**: safe as a single migration. Old code does not know about it.
- **Creating an index with CONCURRENTLY**: safe as a single migration. Non-blocking.
- **Adding an optional foreign key on a new table**: safe as a single migration.

Use your judgement: the test is "does the running application break the moment this migration runs?" If yes, expand-contract. If no, a single migration is fine.

---

## Common mistakes

**Combining Stage 1 and Stage 3 in one deploy.** This is the pattern you are replacing, not optimising. There is no in-between state where both old and new code work. Do not do it even if the table is small.

**Running the backfill inside the migration file.** A single `UPDATE` on a large table inside a migration holds a lock for the entire duration. Backfills go in a separate job, not in the migration file.

**Starting Stage 3 before the backfill is complete.** Always verify with `SELECT COUNT(*) FROM table WHERE new_column IS NULL` before running the Contract stage migration.

**Not testing the Down migration.** The Down migration is production code. Run it in CI. If it says "DATA LOSS", make sure the team has explicitly accepted that before the Stage 3 migration merges.
