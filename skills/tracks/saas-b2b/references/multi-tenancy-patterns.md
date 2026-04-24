# Multi-tenancy patterns

Tenant isolation is the load-bearing invariant of B2B SaaS. Getting it wrong once is a breach; getting it wrong repeatedly is the end of the company. This reference covers the three tenancy models, how to enforce them at the database and application layers, and how tenant context is propagated through the request lifecycle.

---

## The three tenancy models

| Model | Shape | Cost | Isolation | Noisy neighbour | When to use |
|-------|-------|------|-----------|-----------------|-------------|
| Pool | One DB, one schema, tenant_id column on every row | Lowest | Weakest (app bugs leak across tenants) | Highest — one tenant can burn shared resources | Default for most products; long tail of small customers |
| Silo | One DB per tenant (or one schema per tenant in one DB) | Highest | Strongest (physical separation) | None | Enterprise tier with contractual isolation; regulated data |
| Bridge | Pool by default, silo for named customers | Mixed | Per-customer | Controllable | Product with a small number of enterprise customers and a long tail |

Most B2B SaaS products start pool. Move to bridge when the first enterprise contract demands dedicated resources. Do not start silo — operational cost scales per tenant and kills agility before product-market fit.

---

## Pool model with Postgres row-level security

RLS moves tenant enforcement from application code (where any missed `WHERE tenant_id = ?` is a leak) to the database (where forgetting the filter returns zero rows instead of everyone's data).

Schema:

```sql
CREATE TABLE customers (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  name text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX customers_tenant_id_idx ON customers (tenant_id);

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers FORCE ROW LEVEL SECURITY;  -- applies to table owners too

CREATE POLICY tenant_isolation ON customers
  USING (tenant_id = current_setting('app.tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

Setting the tenant context for a connection (typically in a middleware or connection checkout hook):

```sql
SET LOCAL app.tenant_id = '3f2504e0-4f89-11d3-9a0c-0305e82c3301';
```

`SET LOCAL` is scoped to the current transaction — it resets when the transaction ends, which means a connection returned to the pool does not leak context to the next request. Use `SET LOCAL` exclusively; plain `SET` leaks.

Critical rules:

- `FORCE ROW LEVEL SECURITY` is mandatory. Without it, table owners bypass the policy, and your migration user is usually the table owner.
- Every table with tenant data needs both `USING` (read) and `WITH CHECK` (write) clauses. Without `WITH CHECK`, an application bug can insert a row with someone else's tenant_id.
- The RLS policy and the application `WHERE tenant_id = ?` filter should both exist. Defence in depth. If one fails, the other catches it.
- Connection poolers (PgBouncer in transaction mode) need care. `SET LOCAL` inside a transaction is safe; `SET` is not.

---

## Silo model — database-per-tenant

```python
# Connection routing by tenant
def get_connection_for_tenant(tenant_id: str) -> Connection:
    config = tenant_registry.lookup(tenant_id)
    return connection_pool.acquire(
        host=config.db_host,
        database=f"tenant_{tenant_id}",
        user=config.db_user,
    )
```

Operational reality of silo:

- Migrations now run N times. Build a migration runner that iterates the tenant registry, runs the migration per tenant, and reports per-tenant status. Budget for partial-success states.
- Monitoring must be per-tenant. A single dashboard showing aggregate numbers hides the sick tenant.
- Backups are per-tenant. Restore tests must cover restoring one tenant without touching the others.
- Cost scales per tenant. Run silos only when a contract pays for it.

Silo is strongest at isolating data, but application bugs can still leak if the code ever holds two tenants' data in memory at once (batch jobs, reporting, admin tools). The database boundary does not save a poorly written cross-tenant analytics query.

---

## Bridge model — pool by default, silo for named tenants

A tenant registry maps tenant_id to placement:

```python
class TenantPlacement:
    tenant_id: UUID
    placement: Literal["pool", "silo"]
    db_host: str | None      # None means "shared pool"
    db_name: str | None

def get_db(tenant_id: UUID) -> Database:
    placement = tenant_registry.lookup(tenant_id)
    if placement.placement == "silo":
        return silo_pools.for_tenant(tenant_id)
    return shared_pool
```

Migration of a tenant from pool to silo is a one-way doorway — plan it. Typical trigger: enterprise contract requires dedicated infrastructure, or a noisy tenant is impacting others. Build the tooling once; run it rarely.

---

## Tenant context propagation

Tenant context must reach every layer: HTTP handler, service, database, background job, cache key, log line, metric tag, outbound webhook. Any layer where context can be dropped is a leak waiting to happen.

Middleware pattern (Python / FastAPI):

```python
from contextvars import ContextVar

_tenant_id: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)

def current_tenant() -> UUID:
    tid = _tenant_id.get()
    if tid is None:
        raise TenantContextMissing("no tenant_id in context")
    return tid

class TenantMiddleware:
    async def __call__(self, request, call_next):
        tenant = resolve_tenant_from_auth(request)
        token = _tenant_id.set(tenant)
        try:
            async with db.transaction() as tx:
                await tx.execute(
                    "SET LOCAL app.tenant_id = $1", str(tenant)
                )
                return await call_next(request)
        finally:
            _tenant_id.reset(token)
```

Rules:

- Every async boundary (task spawn, queue enqueue, webhook dispatch) must explicitly pass tenant_id. ContextVar does not cross process boundaries.
- Cache keys must include tenant_id. `user:{user_id}` is wrong; `tenant:{tenant_id}:user:{user_id}` is right.
- Log lines must include tenant_id as a structured field so operators can filter a production incident to one tenant in seconds.
- Background jobs re-establish tenant context at start; do not rely on it being inherited from the scheduler.

---

## Enforcement checklist

Before a design passes Stage 2:

- Every table with tenant data has `tenant_id NOT NULL` and an index on it.
- RLS is enabled and forced on every tenant-scoped table (pool or bridge models).
- The tenant resolution path from authenticated request to `app.tenant_id` setting is documented.
- Shared infrastructure (queues, caches, search indexes, blob storage) has a tenant-scoping strategy written down.
- At least one negative test plan exists for cross-tenant reads and writes.

Before code passes Stage 4:

- A test attempts to read tenant B's data while authenticated as tenant A and expects zero rows or a 403.
- A test attempts to write a row with `tenant_id` = B while authenticated as tenant A and expects the write to fail.
- Background job tests exercise the context-propagation path, not just in-process calls.
