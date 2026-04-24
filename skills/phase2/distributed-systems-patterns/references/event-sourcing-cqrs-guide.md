# Event sourcing and CQRS — when they earn their complexity

Event sourcing and CQRS are two patterns that often appear together but are independent. Both are powerful and both carry significant complexity cost. This guide is written to help you decide honestly whether they are justified.

---

## Event sourcing in one paragraph

Instead of storing the current state of an entity, store the sequence of events that led to that state. `Account.balance = 50` is derived by replaying `AccountOpened → Deposited(100) → Withdrew(50)`. The event log is the source of truth; current state is a projection.

## CQRS in one paragraph

Command Query Responsibility Segregation — split write operations (commands) from read operations (queries) into different models, potentially different databases. Writes go to a normalized model optimized for consistency. Reads come from denormalized views optimized for query patterns.

CQRS does **not** require event sourcing. Event sourcing often pairs with CQRS because the event log is natural input for building read models.

---

## When event sourcing earns its complexity

Use event sourcing when at least one of these is true:

- **Audit is a first-class requirement.** Regulators require knowing every state change, who made it, and when. "Why is this account in state X?" must be answerable by replaying history.
- **Time-travel debugging is valuable.** "Show me the system state as of 2 PM last Tuesday." Accounting, trading, compliance domains.
- **Multiple read models evolve independently.** The same write stream feeds analytics, search index, notifications, reporting dashboards. Each is a projection.
- **Domain is inherently event-driven.** Workflow engines, real-time collaboration, IoT telemetry — the business talks in events, not rows.
- **Retroactive correction matters.** "Reprocess all events from last month with the new fee-calculation rule." Possible with event sourcing; painful with mutable state.

## When NOT to use event sourcing

- **CRUD domain.** User profiles, product catalogs, simple configuration. Event sourcing adds complexity with no return.
- **Small team without experience.** The failure modes (projection bugs, schema evolution, snapshot correctness) are subtle and have bitten every team that adopted it casually.
- **Ad-hoc queries over current state are common.** "Show me all users in California" is cheap on a normalized DB, expensive on a raw event log without projections.
- **No audit/replay/time-travel requirement.** If you never need history beyond "what does it look like now," you are paying for infrastructure you do not use.

**Rule of thumb:** if you cannot name three concrete scenarios where replaying history from scratch is valuable, you do not need event sourcing.

---

## Event sourcing mechanics

### Event log

Append-only store of immutable events:

```sql
CREATE TABLE events (
  id             BIGSERIAL   PRIMARY KEY,
  aggregate_id   TEXT        NOT NULL,
  aggregate_type TEXT        NOT NULL,   -- 'Account', 'Order', ...
  sequence_no    BIGINT      NOT NULL,   -- per-aggregate monotonic
  event_type     TEXT        NOT NULL,   -- 'Deposited', 'Withdrawn', ...
  event_version  INT         NOT NULL DEFAULT 1,
  payload        JSONB       NOT NULL,
  metadata       JSONB       NOT NULL,   -- actor, correlation_id, timestamp
  recorded_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (aggregate_id, sequence_no)
);

CREATE INDEX idx_events_by_aggregate
  ON events (aggregate_id, sequence_no);
```

### Loading an aggregate

```python
def load_account(aggregate_id: str) -> Account:
    events = db.fetch_all(
        "SELECT event_type, payload FROM events "
        "WHERE aggregate_id = %s ORDER BY sequence_no",
        (aggregate_id,),
    )
    account = Account()
    for e in events:
        account.apply(e)   # pure function: (state, event) -> state
    return account
```

### Writing an event — optimistic concurrency

```python
def deposit(aggregate_id: str, amount: Money) -> None:
    account = load_account(aggregate_id)
    account.check_deposit_allowed(amount)

    event = Deposited(amount=amount, at=now())
    next_seq = account.sequence_no + 1

    # UNIQUE(aggregate_id, sequence_no) catches concurrent writes
    try:
        db.execute(
            "INSERT INTO events(aggregate_id, aggregate_type, sequence_no, "
            "event_type, payload, metadata) VALUES (%s, %s, %s, %s, %s, %s)",
            (aggregate_id, "Account", next_seq, "Deposited",
             event.payload, event.metadata),
        )
    except UniqueViolation:
        # Another writer won; reload and retry (or surface conflict)
        raise ConcurrencyConflict(aggregate_id)
```

### Snapshots

Replaying thousands of events on every load is slow. Snapshot periodically.

```sql
CREATE TABLE aggregate_snapshots (
  aggregate_id   TEXT        NOT NULL,
  aggregate_type TEXT        NOT NULL,
  sequence_no    BIGINT      NOT NULL,   -- snapshot up to this event
  state          JSONB       NOT NULL,   -- serialized aggregate state
  taken_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (aggregate_id, sequence_no)
);
```

Loading with snapshot:

```python
def load_account(aggregate_id: str) -> Account:
    snap = db.fetch_one(
        "SELECT state, sequence_no FROM aggregate_snapshots "
        "WHERE aggregate_id = %s ORDER BY sequence_no DESC LIMIT 1",
        (aggregate_id,),
    )
    if snap:
        account = Account.from_state(snap.state)
        start_seq = snap.sequence_no + 1
    else:
        account = Account()
        start_seq = 0

    events = db.fetch_all(
        "SELECT event_type, payload FROM events "
        "WHERE aggregate_id = %s AND sequence_no >= %s "
        "ORDER BY sequence_no",
        (aggregate_id, start_seq),
    )
    for e in events:
        account.apply(e)
    return account
```

Snapshot frequency: every N events (e.g. 100) or every T minutes. Snapshots are derived, never primary — they can always be rebuilt from the log.

### Projections

Projections are read models built by subscribing to the event stream:

```python
class AccountBalanceProjection:
    """Maintains a denormalized table of (account_id, balance) for fast reads."""

    def handle(self, event: Event) -> None:
        if event.type == "Deposited":
            db.execute(
                "UPDATE balances SET balance = balance + %s, "
                "last_event_seq = %s WHERE account_id = %s "
                "AND last_event_seq < %s",
                (event.amount, event.sequence_no,
                 event.aggregate_id, event.sequence_no),
            )
        elif event.type == "Withdrawn":
            # ... and so on
            pass
```

**Rules for projections:**
- Idempotent — track `last_event_seq` per projection to skip already-applied events on replay.
- Rebuildable — dropping and rebuilding the projection from the event log must produce the same result.
- Eventually consistent — the read model lags the write model. Communicate this to UI/API consumers.

### Event schema evolution

Events are immutable. You cannot change an event once written. Handle schema changes with:

- **Additive changes only when possible.** New fields default to null for old events.
- **Upcasting on read.** Load v1 event → upcast function → v2 in-memory representation. The log stays as it was written.
- **Never rewrite the log.** Migrations in event-sourced systems are upcast code, not SQL updates.

---

## CQRS mechanics (with or without event sourcing)

### Without event sourcing — the simpler form

```
┌──────────┐          ┌──────────┐
│ Command  │──writes──▶│ Write DB │
│ handler  │          │ (OLTP)   │
└──────────┘          └────┬─────┘
                           │
                           │ CDC / outbox / logical replication
                           ▼
                      ┌──────────┐
                      │ Read DB  │ (denormalized, query-optimized)
                      │ (Elastic,│
                      │  Redis,  │
                      │  BigQuery│
                      │  etc.)   │
                      └──────────┘
                           ▲
┌──────────┐               │
│ Query    │───reads───────┘
│ handler  │
└──────────┘
```

Write model stays normalized and transactional. Read models are denormalized per query pattern. Replication is async → eventual consistency.

### With event sourcing

The event log IS the write model. Read models are projections consuming the event stream. The two are often the same picture as above, just with the event log replacing "write DB + CDC."

### When CQRS is worth it

- Read/write ratio is very asymmetric (e.g. 100:1 reads).
- Query patterns differ wildly from the write model (reporting, search, aggregation).
- Read scaling needs outpace write scaling (common — reads scale horizontally more cheaply with a dedicated read model).

### When CQRS is overkill

- Read and write load are balanced.
- Query patterns match the write model shape.
- Team has not yet felt pain from mixing the two. Premature CQRS is premature optimization.

---

## Read-model rebuild procedure

Projections will have bugs. Plan for rebuilds from day one.

1. Version the projection code (`v1`, `v2`).
2. Stand up a new projection table/index in parallel (`balances_v2`).
3. Replay the full event log into `v2`. This may take hours — plan for it.
4. Switch read traffic to `v2` (feature flag or config switch).
5. Keep `v1` running briefly; if `v2` is correct, drop `v1`.

Without this procedure, projection bugs become permanent data corruption. With it, they become a well-understood operational task.

---

## Honest trade-offs

| Benefit claimed | Reality |
|-----------------|---------|
| "Full audit trail for free" | True — but only if event metadata captures actor, correlation, cause |
| "Time-travel debugging" | True — but requires tooling to replay against old code versions |
| "Easy to add new features" | True for features that fit projections. Adding a new invariant that conflicts with old events is painful |
| "Scales reads independently" | True with CQRS — but async replication lag surfaces as UX complexity ("I just saved it, why can't I see it?") |
| "Natural fit for microservices" | True — events cross service boundaries cleanly |
| "Simple to learn" | **False.** Projection idempotency, snapshot correctness, concurrent writes, schema evolution — each one has caught competent teams off-guard |

If you cannot explain to a new engineer why you chose event sourcing in under five minutes, the team will not maintain it correctly.
