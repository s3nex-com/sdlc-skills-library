# HIPAA audit log requirements — what to log, how to protect it, how long to keep it

HIPAA Security Rule §164.312(b) requires "hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information." §164.308(a)(1)(ii)(D) requires regular review of those records. Those two sentences are the whole legal text; everything else is how to implement them in a way that survives an OCR investigation or a breach postmortem.

The working rule: **every access to PHI — read or write — must be attributable, timestamped, immutable, retained for 6 years, and reviewable**.

---

## What must be logged

Every event where PHI is accessed, created, modified, exported, printed, or deleted. In a modern service:

- API reads of any PHI field — record pulls, patient search, report generation
- API writes, updates, deletes — any mutation to a PHI record
- Background job access — ETL reading the patients table, nightly export to a warehouse, PDF generation for billing
- Admin actions — user provisioning, role changes, break-glass access
- Authentication events — successful and failed logins, session issuance, MFA challenges
- Authorization failures — someone tried to read a record and was denied
- Export / download events — CSV export, PDF print, API bulk fetch
- Configuration changes — a user's role changed from "read-only analyst" to "full clinical"

What does **not** need a separate audit log entry: every SQL query the ORM emits (too noisy, not attributable to a user). Capture at the logical-access layer (controller / service method), not the storage layer.

---

## Required fields (minimum viable audit record)

Each log entry must answer: **who, what, when, where, how, and outcome**.

| Field | Description | Example |
|-------|-------------|---------|
| `event_id` | Unique, monotonically ordered | UUIDv7 or `sequence_id` BIGINT |
| `event_time_utc` | UTC timestamp, millisecond precision | `2026-04-21T14:23:07.412Z` |
| `actor_id` | Authenticated user or service account | `user:dr_adams@hospital.org` |
| `actor_role` | Role at time of action (not current role) | `clinician` |
| `actor_ip` | Source IP address | `10.4.2.88` |
| `actor_session` | Session or request correlation ID | `req_01HXABC…` |
| `action` | Verb | `read`, `write`, `export`, `delete`, `login`, `auth_deny` |
| `resource_type` | What kind of PHI | `patient`, `encounter`, `lab_result` |
| `resource_id` | Specific record | `patient:98213` |
| `fields_accessed` | Minimum-necessary trace: which PHI fields were returned | `["diagnosis","medications"]` |
| `purpose` | Declared purpose-of-use (treatment, payment, operations, research-IRB) | `treatment` |
| `outcome` | success / denied / error | `success` |
| `reason_code` | If denied or error | `abac_policy:not_care_team` |
| `client_app` | Which app/service emitted this | `clinician-portal@v4.12.1` |
| `prev_hash` | Hash of previous entry (tamper-evidence chain) | `sha256:…` |
| `entry_hash` | Hash of this entry including prev_hash | `sha256:…` |

If a field is not known, say so explicitly — never leave it blank. An audit log with silent nulls is evidence that can be challenged.

---

## Tamper evidence — three defences stacked

A log that can be silently edited is not an audit log. Three standard defences, use at least two:

### 1. Append-only at the database layer

Revoke UPDATE and DELETE on the audit table from every role. The application writes only INSERTs.

```sql
CREATE TABLE phi_audit_log (
    event_id      UUID PRIMARY KEY,
    event_time    TIMESTAMPTZ NOT NULL,
    actor_id      TEXT NOT NULL,
    actor_role    TEXT NOT NULL,
    actor_ip      INET,
    actor_session TEXT,
    action        TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id   TEXT NOT NULL,
    fields        JSONB,
    purpose       TEXT,
    outcome       TEXT NOT NULL,
    reason_code   TEXT,
    client_app    TEXT,
    prev_hash     BYTEA,
    entry_hash    BYTEA NOT NULL
);

-- Append-only enforcement
REVOKE UPDATE, DELETE, TRUNCATE ON phi_audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE, TRUNCATE ON phi_audit_log FROM app_write_role;

CREATE RULE phi_audit_log_no_update AS ON UPDATE TO phi_audit_log DO INSTEAD NOTHING;
CREATE RULE phi_audit_log_no_delete AS ON DELETE TO phi_audit_log DO INSTEAD NOTHING;

CREATE INDEX phi_audit_log_actor_time ON phi_audit_log (actor_id, event_time DESC);
CREATE INDEX phi_audit_log_resource_time ON phi_audit_log (resource_type, resource_id, event_time DESC);
CREATE INDEX phi_audit_log_time ON phi_audit_log (event_time DESC);
```

### 2. Cryptographic chain (hash linking)

Each entry's `entry_hash = SHA-256(serialize(entry_without_hash) || prev_hash)`. The first entry's `prev_hash` is a genesis value. Verification walks the chain and recomputes every hash. A single altered row breaks the chain from that point forward.

```python
def insert_audit(conn, entry: dict) -> None:
    with conn.transaction():
        prev_hash = conn.execute(
            "SELECT entry_hash FROM phi_audit_log ORDER BY event_time DESC LIMIT 1"
        ).fetchone() or GENESIS_HASH
        entry["prev_hash"] = prev_hash
        entry["entry_hash"] = sha256(
            canonical_json(entry).encode() + prev_hash
        ).digest()
        conn.execute(INSERT_SQL, entry)
```

Periodically (daily, nightly), a verifier job recomputes the chain and publishes a Merkle root to a write-once location. A break is a P1 incident.

### 3. WORM storage (Write-Once-Read-Many)

Stream audit entries to a storage layer that physically prevents mutation. AWS S3 Object Lock (Compliance mode), Azure Blob immutable storage, or an on-prem WORM appliance. Even a root-compromised application cannot retroactively edit what is already in object-locked S3.

A production setup normally uses all three: append-only primary table + hash chain + nightly flush to object-locked S3. Two of three satisfies most auditors. One alone is brittle.

---

## Retention — 6 years minimum

HIPAA §164.316(b)(2)(i) requires retention of documentation for **6 years from the date of its creation or the date when it last was in effect, whichever is later**. Some states (notably Texas, California) require longer for clinical records themselves; check state law for the clinical record, but the 6-year federal floor applies to audit logs.

Retention implementation:

- Hot tier (current year): primary Postgres/MySQL partition, indexed, fast query.
- Warm tier (years 1–2): partitioned historical tables, less frequently queried, still online.
- Cold tier (years 2–6): compressed Parquet on object-locked S3 with a lifecycle policy that blocks deletion until 6y from write.

Never delete before 6 years. Never rely on "soft delete" — object lock is the only defensible mechanism when OCR asks for logs from 5 years ago.

---

## Access patterns — how the log is actually reviewed

An audit log nobody reads is theatre. Build these review queries into a dashboard and run them on a cadence:

### Quarterly access review — who read PHI they maybe shouldn't have

```sql
-- Top accessors in the last 90 days, to compare against expected workload
SELECT actor_id, actor_role, COUNT(*) AS reads, COUNT(DISTINCT resource_id) AS distinct_records
FROM phi_audit_log
WHERE action = 'read'
  AND event_time >= now() - INTERVAL '90 days'
GROUP BY actor_id, actor_role
ORDER BY reads DESC
LIMIT 50;
```

### VIP / same-last-name check — common insider-threat pattern

```sql
-- Users who accessed records whose patient last name matches the user's last name
SELECT a.actor_id, a.resource_id, a.event_time
FROM phi_audit_log a
JOIN users u ON u.id = a.actor_id
JOIN patients p ON p.id = a.resource_id
WHERE a.action = 'read'
  AND lower(u.last_name) = lower(p.last_name)
  AND a.event_time >= now() - INTERVAL '30 days';
```

### Break-glass usage — should be rare and always reviewed

```sql
SELECT actor_id, resource_id, reason_code, event_time
FROM phi_audit_log
WHERE purpose = 'break_glass'
  AND event_time >= now() - INTERVAL '7 days';
```

### Failed-access spikes — credential stuffing or probing

```sql
SELECT actor_ip, COUNT(*) AS denies
FROM phi_audit_log
WHERE outcome = 'denied'
  AND event_time >= now() - INTERVAL '1 hour'
GROUP BY actor_ip
HAVING COUNT(*) > 20;
```

### Chain integrity — runs nightly, alerts on break

```sql
-- Pseudocode: the verifier job reads in event_time order,
-- recomputes each entry_hash, and asserts continuity.
-- A broken chain is a P1 incident.
```

### Patient access request — "who has seen my record"

HIPAA §164.528 gives patients the right to an accounting of disclosures. Support this query:

```sql
SELECT event_time, actor_id, actor_role, action, purpose, client_app
FROM phi_audit_log
WHERE resource_type = 'patient'
  AND resource_id = :patient_id
  AND action IN ('read', 'export')
ORDER BY event_time DESC;
```

---

## Worked example — writing an audit entry on a PHI read

```python
# clinician-portal, endpoint GET /patients/{id}
@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, user: User = Depends(auth), req: Request):
    authorized, reason = abac.evaluate(user, "read", "patient", patient_id)
    if not authorized:
        await audit.record({
            "actor_id": user.id,
            "actor_role": user.active_role,
            "actor_ip": req.client.host,
            "actor_session": req.state.request_id,
            "action": "read",
            "resource_type": "patient",
            "resource_id": patient_id,
            "outcome": "denied",
            "reason_code": reason,
            "purpose": req.headers.get("X-Purpose-Of-Use", "unspecified"),
            "client_app": "clinician-portal@" + VERSION,
        })
        raise HTTPException(403)

    patient = await repo.get_patient(patient_id)
    await audit.record({
        "actor_id": user.id,
        "actor_role": user.active_role,
        "actor_ip": req.client.host,
        "actor_session": req.state.request_id,
        "action": "read",
        "resource_type": "patient",
        "resource_id": patient_id,
        "fields": PATIENT_RESPONSE_FIELDS,
        "outcome": "success",
        "purpose": req.headers.get("X-Purpose-Of-Use", "treatment"),
        "client_app": "clinician-portal@" + VERSION,
    })
    return patient
```

The audit write is not fire-and-forget. If the audit write fails, the PHI read must fail — a returned record without a recorded access is worse than a 500 to the user. Either use the same transaction, or use a durable outbox and fail-closed on outbox saturation.

---

## Checklist — before merging any PHI-reading code path

- [ ] Audit write happens on every path out of the handler (success and denial).
- [ ] Audit write failure aborts the read (no silent successes).
- [ ] `fields_accessed` is populated — we know which PHI fields were returned.
- [ ] `purpose` is populated — the caller declared why.
- [ ] The audit table is append-only (tested by attempting UPDATE and DELETE).
- [ ] Entry_hash chains to prev_hash — chain verifier test passes.
- [ ] Log entries flow to WORM storage within the retention SLA.
- [ ] Reviewer dashboards surface this event type.
- [ ] Quarterly review procedure references these queries.
