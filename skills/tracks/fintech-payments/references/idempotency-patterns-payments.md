# Idempotency patterns for payment APIs

A duplicate charge is worse than a failed one. Every payment mutation — create charge, create payout, capture, refund, transfer — must be idempotent against client retries, network partitions, proxy replays, and user double-clicks. This file is the canonical pattern for money-movement endpoints.

---

## The contract

Clients send an `Idempotency-Key` header on every mutating request. The server guarantees: **for the same key within the TTL window, the same request returns the same response exactly once effected on the backend.**

Two replays of the same key must produce identical visible behavior. Zero side-effects on the second call.

---

## Header naming and format

- Header name: `Idempotency-Key` (capitalization per RFC 7230; most frameworks case-insensitive anyway).
- Format: opaque string, UUID v4 recommended, 16–255 characters. Never derive from request content — that removes the client's ability to retry.
- Required on every mutating endpoint (`POST`, `PATCH`, `DELETE`). Optional but honored on safe methods.
- If missing on a mutating endpoint, return `400 Bad Request` with `{"error": "idempotency_key_required"}`. Do not generate one server-side — the client must own the key so its retries use the same one.

Client example (TypeScript):

```ts
const key = crypto.randomUUID();
await fetch("/v1/charges", {
  method: "POST",
  headers: {
    "Idempotency-Key": key,
    "Content-Type": "application/json",
  },
  body: JSON.stringify(charge),
});
// On network timeout: retry with the SAME key. Never generate a new one.
```

---

## Dedup table schema

Dedicated table, separate index, fast key lookup. Do not piggyback on the business table.

```sql
CREATE TABLE idempotency_records (
    key              TEXT       PRIMARY KEY,
    account_id       TEXT       NOT NULL,           -- scope key to account
    method           TEXT       NOT NULL,
    path             TEXT       NOT NULL,
    request_hash     BYTEA      NOT NULL,           -- sha256 of canonical body
    status           TEXT       NOT NULL,           -- 'in_flight' | 'complete'
    response_status  INT,
    response_body    JSONB,
    locked_at        TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at       TIMESTAMPTZ NOT NULL           -- created_at + TTL
);

CREATE INDEX idx_idem_expires ON idempotency_records (expires_at);
```

Scope the key per account (`(account_id, key)` effective primary key if multi-tenant) so one tenant's UUID collisions can't poison another's.

---

## TTL

24 hours is the Stripe baseline and a safe default. Choose based on your replay windows:

- Client retries in a mobile app over flaky networks: 24h
- Server-to-server integrations with exponential backoff: 24–72h
- Batch reconciliation processes that may rerun: match the batch window + a buffer

Reap expired rows with a daily job. Do not let the table grow unbounded.

---

## Request handling algorithm

```
1. Extract Idempotency-Key from request.
2. Compute request_hash = sha256(canonicalize(body)).
3. SELECT from idempotency_records WHERE key = $1 AND account_id = $2.

4. If row exists and status = 'complete':
     - If request_hash matches stored hash: return stored response.
     - If request_hash differs: return 422 Unprocessable — "Idempotency-Key reused with different request body".

5. If row exists and status = 'in_flight':
     - Another request is processing. Return 409 Conflict with Retry-After.
     - Do NOT process concurrently. Only one request per key at a time.

6. If row does not exist:
     - INSERT with status='in_flight' inside the same transaction as the business logic.
     - If the INSERT fails on unique violation, go to step 4 (race).
     - Execute the business logic.
     - UPDATE row with status='complete', response_status, response_body.
     - COMMIT.
     - Return response.
```

Pseudo-code (Python + SQLAlchemy-ish):

```python
def handle_idempotent(req, key, account_id, handler):
    body_hash = sha256(canonical(req.body))
    with db.transaction() as tx:
        row = tx.execute(
            "SELECT * FROM idempotency_records WHERE key=%s AND account_id=%s FOR UPDATE",
            (key, account_id),
        ).first()

        if row and row.status == "complete":
            if row.request_hash != body_hash:
                return 422, {"error": "idempotency_key_reused_with_different_body"}
            return row.response_status, row.response_body

        if row and row.status == "in_flight":
            return 409, {"error": "request_in_progress"}, {"Retry-After": "2"}

        tx.execute(
            "INSERT INTO idempotency_records (key, account_id, method, path, "
            "request_hash, status, expires_at) VALUES (%s, %s, %s, %s, %s, "
            "'in_flight', now() + interval '24 hours')",
            (key, account_id, req.method, req.path, body_hash),
        )

        status, body = handler(req)  # business logic (charge, payout, etc.)

        tx.execute(
            "UPDATE idempotency_records SET status='complete', "
            "response_status=%s, response_body=%s WHERE key=%s AND account_id=%s",
            (status, body, key, account_id),
        )
        return status, body
```

The business logic and the idempotency row must commit together. If they are in separate transactions, a crash between them breaks the guarantee.

---

## Retry and error semantics

| Server state | Returned on retry |
|--------------|-------------------|
| `complete`, same body | Stored response (same status, same body). Status `200` or `201` replayed as-is. |
| `complete`, different body | `422 Unprocessable`, error `idempotency_key_reused_with_different_body`. |
| `in_flight` | `409 Conflict`, `Retry-After: 2`. Client should retry same key after the interval. |
| No row, first request | Normal processing. |
| `complete`, stored response was a client error (`4xx`) | Return the same `4xx`. The error is part of the idempotent outcome — clients must not infer "try a different input" from a retry succeeding. |
| `complete`, stored response was a server error (`5xx`) | Do NOT cache `5xx`. Treat as no row and retry the business logic. (Implementation: only write status=`complete` on `2xx` or deterministic `4xx`.) |

The asymmetry on `5xx` matters: if an infrastructure hiccup caused the first request to fail, the client must be able to retry and actually succeed. If an input validation caused `422`, the client must get the same `422` on retry so the application doesn't accidentally submit a different body and succeed.

---

## Interaction with the processor

If your handler calls a downstream processor (Stripe, Adyen), pass the idempotency key through. Stripe's `Idempotency-Key` header accepts your UUID directly — do not generate a second one. This stitches end-to-end idempotency: your retry to the processor is deduped by the processor, and your retry to yourself is deduped by your table.

```python
stripe.PaymentIntent.create(
    amount=amount,
    currency="usd",
    idempotency_key=incoming_idempotency_key,  # same key, all the way down
)
```

---

## Common failures to avoid

1. **Hashing the request without canonicalization.** Two semantically identical JSON bodies with different key order produce different hashes. Use a canonical serializer (e.g., sorted keys, no trailing whitespace).
2. **Global keyspace instead of per-account.** One customer's collision becomes everyone's problem. Always scope.
3. **Reading `complete` rows without comparing the body hash.** If a client reuses a key with a new body (bug on their side), silently returning the old response is dangerous. `422` is the correct signal.
4. **TTL too short.** A 5-minute TTL means a retry after a 6-minute network blip re-charges the card. Use 24h.
5. **Processing concurrent `in_flight` requests.** Use `SELECT ... FOR UPDATE` or a unique constraint-based lock. Never "just let them both run."
6. **Caching `5xx` as complete.** Permanently poisons the key for that request; client can never retry.
