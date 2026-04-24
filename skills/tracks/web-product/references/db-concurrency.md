# Database concurrency for web products

Multi-user web products hit concurrency problems that single-user apps never encounter. This reference covers the patterns that prevent data corruption, duplicate records, and lost updates.

---

## The concurrency problem taxonomy

| Problem | What happens | Pattern to apply |
|---------|-------------|-----------------|
| Lost update | Two users read a row, both modify it, second write overwrites the first | Optimistic locking |
| Duplicate record | User submits a form twice (double-click, network retry) | Idempotency key |
| Overselling / double-spend | Two requests both check "quantity > 0" and both decrement | Pessimistic locking or optimistic locking |
| Race on creation | Two requests both try to create the same unique resource | Unique constraint + upsert |
| Phantom read | A report query runs while rows are being inserted — inconsistent snapshot | Serializable isolation |
| Deadlock | Two transactions wait on each other's locks | Consistent lock ordering |

---

## Optimistic locking

Use when: conflicts are rare, reads vastly outnumber writes, and you want to avoid holding a lock.

**Version column approach:**

```sql
ALTER TABLE items ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
```

```typescript
// Read with version
const item = await db.item.findUnique({ where: { id }, select: { version: true, ...otherFields } });

// Update — only succeeds if version has not changed since we read it
const result = await db.item.updateMany({
  where: { id, version: item.version },    // optimistic lock check
  data: { name: newName, version: { increment: 1 } },
});

if (result.count === 0) {
  throw new ConflictError('Item was modified by another user. Please refresh and try again.');
}
```

**ORM support:**
- Prisma: `@@map` + manual version check (as above) or `prisma-optimistic-lock` package
- Drizzle ORM: manual version check
- TypeORM: `@VersionColumn()` decorator — handles it automatically

**When to use vs pessimistic:** use optimistic when you can show the user a meaningful "conflict" UI (e.g., "someone else edited this — here's what they changed"). Use pessimistic when the operation must not fail silently and retrying is complex.

---

## Pessimistic locking

Use when: conflicts are frequent, the operation is short, or the cost of a conflict is high (financial, inventory).

```sql
-- Lock the row for the duration of the transaction
BEGIN;
SELECT quantity FROM inventory WHERE product_id = $1 FOR UPDATE;
-- Now safe to check and decrement — no other transaction can touch this row
UPDATE inventory SET quantity = quantity - $2 WHERE product_id = $1 AND quantity >= $2;
COMMIT;
```

```typescript
// Prisma: use $transaction with serializable isolation for the whole unit
await db.$transaction(async (tx) => {
  const inventory = await tx.$queryRaw<[{ quantity: number }]>`
    SELECT quantity FROM inventory WHERE product_id = ${productId} FOR UPDATE
  `;
  if (inventory[0].quantity < requestedQty) throw new InsufficientInventoryError();
  await tx.inventory.update({
    where: { productId },
    data: { quantity: { decrement: requestedQty } },
  });
  await tx.order.create({ data: { ... } });
}, { isolationLevel: 'Serializable' });
```

**Advisory locks** — when you need an application-level lock that does not correspond to a row:

```sql
-- Acquire a named lock (non-blocking variant — fails immediately if unavailable)
SELECT pg_try_advisory_xact_lock(hashtext('generate-invoice-' || workspace_id::text));
-- Returns true if lock acquired, false if already held by another transaction
```

---

## Idempotency keys

Use when: a mutation endpoint could be called more than once (network retry, user double-submit, background job retry).

**Pattern:**
1. Client generates a UUID per intent (once, before the first attempt)
2. Client sends it in every attempt: `Idempotency-Key: <uuid>`
3. Server stores (key, workspaceId, result) with a TTL
4. On duplicate key → return stored result without re-executing

```typescript
// Handler
async function createInvoice(ctx: RequestContext, body: CreateInvoiceBody) {
  const idempotencyKey = ctx.headers['idempotency-key'];
  if (!idempotencyKey) throw new BadRequestError('Idempotency-Key header required');

  // Check cache
  const cached = await redis.get(`idempotency:${ctx.workspaceId}:${idempotencyKey}`);
  if (cached) return JSON.parse(cached);

  // Execute
  const invoice = await db.invoice.create({ data: { ...body, workspaceId: ctx.workspaceId } });

  // Store result (TTL: 24 hours)
  await redis.setex(
    `idempotency:${ctx.workspaceId}:${idempotencyKey}`,
    86400,
    JSON.stringify(invoice)
  );

  return invoice;
}
```

**Which endpoints need idempotency keys:**
- POST (create) — always, if there's any value to the client retrying
- PATCH/PUT — not typically needed (they are inherently idempotent if the payload is the same)
- DELETE — HTTP spec says DELETE is idempotent; return 200/204 whether or not the row existed

**Form double-submit prevention** (frontend):
```typescript
// Disable the submit button and show loading state immediately on first submit
const [submitting, setSubmitting] = useState(false);

async function handleSubmit(e: FormEvent) {
  e.preventDefault();
  if (submitting) return;  // guard
  setSubmitting(true);
  try {
    await api.createInvoice({ 'Idempotency-Key': crypto.randomUUID(), ...formData });
  } finally {
    setSubmitting(false);
  }
}
```

---

## Connection pooling

Postgres opens one OS process per connection. Web apps under load can exhaust `max_connections` (default: 100) fast.

**Application pool** (built into most ORMs):

| ORM | Pool config |
|-----|-------------|
| Prisma | `DATABASE_URL=postgresql://...?pool_timeout=10&connection_limit=10` |
| Drizzle / node-postgres | `new Pool({ max: 10, idleTimeoutMillis: 30000 })` |
| SQLAlchemy | `create_engine(url, pool_size=10, max_overflow=20)` |

**PgBouncer** (external pool, recommended for high-concurrency):
- Mode: **transaction pooling** — connection released back to pool after each transaction
- Config: `max_client_conn = 1000`, `default_pool_size = 25` (per DB user)
- Caveats: prepared statements are not compatible with transaction pooling; use `pgbouncer_prepared_statements = 0` or switch to named prepared statement mode
- Note: Postgres advisory locks and `SET LOCAL` are per-connection and do not work correctly in transaction pool mode — use `SET` (session-level) or avoid them with PgBouncer transaction mode

**Sizing the pool:**
- Start with: `pool_size = (num_cpu_cores * 2) + num_disk_spindles`
- For SSD-backed Postgres: `pool_size ≈ num_cpu_cores * 2`
- Monitor connection wait time (`pool_timeout` errors) and increase if needed
- Do not over-provision — Postgres performance degrades above ~100–200 active connections regardless

---

## Deadlock prevention

Deadlocks happen when two transactions acquire locks in opposite order. Postgres detects and terminates one automatically, but the resulting error bubbles to the user.

**Consistent lock ordering:** always acquire locks in the same order across all transactions.

```typescript
// Wrong — if another transaction does (B then A), deadlock
await lockRow(rowB);
await lockRow(rowA);

// Correct — always A then B (sort IDs before locking)
const ids = [rowA.id, rowB.id].sort();
for (const id of ids) await lockRow(id);
```

**Retry on deadlock:** if you cannot guarantee ordering, retry the transaction on `40P01` (deadlock detected):

```typescript
const MAX_RETRIES = 3;
for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
  try {
    return await db.$transaction(async (tx) => { ... });
  } catch (e) {
    if (e.code === '40P01' && attempt < MAX_RETRIES - 1) continue; // retry
    throw e;
  }
}
```

---

## Long transactions — keep them short

Every open transaction holds locks and bloat risk. Rules:

- Never hold a transaction open across a network call (API call, email send, Stripe call)
- Never hold a transaction open waiting for user input
- Wrap only the DB operations that must be atomic
- Use `NOWAIT` or `SKIP LOCKED` when a locked row means "someone else is processing it" (job queue pattern)

```sql
-- Job queue: pick an unclaimed job, skip already-locked ones
SELECT id FROM jobs WHERE status = 'pending' LIMIT 1 FOR UPDATE SKIP LOCKED;
```
