# Tenant isolation for web products (without enterprise SSO)

Web products isolate data per user or per workspace/organisation. The "tenant" is typically a user (solo product) or a workspace that multiple users belong to (team product). This reference covers isolation without enterprise SSO, SAML, or formal multi-tenancy contracts.

---

## Three isolation models

| Model | What it means | When to use | Cost |
|-------|--------------|-------------|------|
| Shared schema + app-level scoping | All tenants in the same tables; `user_id`/`workspace_id` column on every row; app code filters every query | Small products (< 50k rows per tenant), low-compliance requirements | Low |
| Shared schema + Postgres RLS | Same as above but DB enforces the filter via Row Level Security policies; app cannot skip the filter accidentally | Standard choice for web products; defence-in-depth without schema complexity | Low–Medium |
| Schema-per-tenant | Each tenant gets a dedicated Postgres schema (`tenant_<id>.*`); all queries run in the tenant's schema | > 10k tenants OR strict data residency requirements OR very different schema per tenant | Medium–High |
| Database-per-tenant | Each tenant has a dedicated database instance | Regulatory isolation, very large tenants, or SaaS B2B with enterprise contracts — overkill for web products | High |

**Default recommendation for web products:** shared schema + Postgres RLS. It is simple to operate, provides defence-in-depth, and scales well beyond 10k tenants with proper indexing.

---

## Postgres RLS setup

```sql
-- 1. Enable RLS on the table
ALTER TABLE items ENABLE ROW LEVEL SECURITY;

-- 2. Create a policy — SELECT
CREATE POLICY items_tenant_select
  ON items
  FOR SELECT
  USING (workspace_id = current_setting('app.current_workspace_id')::uuid);

-- 3. Create a policy — INSERT
CREATE POLICY items_tenant_insert
  ON items
  FOR INSERT
  WITH CHECK (workspace_id = current_setting('app.current_workspace_id')::uuid);

-- 4. Same for UPDATE, DELETE
CREATE POLICY items_tenant_update
  ON items
  FOR UPDATE
  USING (workspace_id = current_setting('app.current_workspace_id')::uuid);

-- 5. Superuser / service role bypasses RLS — use a role with BYPASSRLS=false for the app
CREATE ROLE app_user LOGIN PASSWORD '...' BYPASSRLS false;
GRANT SELECT, INSERT, UPDATE, DELETE ON items TO app_user;
```

```typescript
// In your request middleware, set the workspace context before any query
await db.execute(
  sql`SELECT set_config('app.current_workspace_id', ${workspaceId}, true)`
);
```

**Important:** The `true` parameter makes the setting local to the current transaction. Use `false` only if you are confident the connection is not pooled or reused.

---

## tenant_id propagation

Propagating the workspace/user context through the entire request lifecycle is the highest-leverage defence against cross-user leaks.

**Request lifecycle:**
```
HTTP request
  → Auth middleware extracts user_id / workspace_id from JWT or session
  → Context object created: { userId, workspaceId, role }
  → Set DB session variable (if using RLS) or inject into repository layer
  → All DB calls in this request use the context — no re-lookup needed
  → Response
```

**Async jobs / background workers:**
```typescript
// When enqueuing a job, always include the workspace context
await queue.add('process-export', {
  workspaceId: ctx.workspaceId,
  userId: ctx.userId,
  exportId: newExport.id,
});

// In the worker, restore the context before any DB call
const { workspaceId, userId } = job.data;
await db.execute(sql`SELECT set_config('app.current_workspace_id', ${workspaceId}, true)`);
```

Never rely on a global variable for tenant context — it will bleed across requests under concurrent load.

---

## Code review checklist for tenant isolation

Every PR touching data-access code should verify:

- [ ] Every `SELECT` on a tenant-scoped table has `WHERE workspace_id = $ctx.workspaceId` (or RLS policy covers it)
- [ ] Every `INSERT` includes `workspace_id` in the values (or RLS WITH CHECK covers it)
- [ ] Every `UPDATE` / `DELETE` has the workspace scope in the `WHERE` clause
- [ ] No raw SQL string concatenation with user input
- [ ] Background job enqueue includes `workspaceId` in the job payload
- [ ] Cache keys include `workspaceId` (e.g., `workspace:${id}:items`)
- [ ] Any search index query scopes by workspace (e.g., Elasticsearch `must: { term: { workspace_id } }`)
- [ ] Log entries include `workspaceId` for debuggability

---

## Testing for cross-user leaks

The cross-user leak test is the most important negative test for a web product. Required at Stage 4.

```typescript
describe('cross-workspace data isolation', () => {
  let workspaceA: Workspace;
  let workspaceB: Workspace;
  let userA: User;
  let userB: User;

  beforeEach(async () => {
    workspaceA = await createTestWorkspace();
    workspaceB = await createTestWorkspace();
    userA = await createTestUser({ workspaceId: workspaceA.id });
    userB = await createTestUser({ workspaceId: workspaceB.id });
    await createItem({ workspaceId: workspaceA.id, name: 'Workspace A item' });
  });

  it('userB cannot read workspaceA items via GET /items', async () => {
    const response = await api.get('/items').auth(userB.token);
    expect(response.body.items).toHaveLength(0);
    expect(response.body.items.map(i => i.name)).not.toContain('Workspace A item');
  });

  it('userB cannot read a workspaceA item by ID', async () => {
    const item = await getFirstItem(workspaceA.id);
    const response = await api.get(`/items/${item.id}`).auth(userB.token);
    expect(response.status).toBe(404); // not 403 — don't confirm existence
  });

  it('userB cannot update a workspaceA item', async () => {
    const item = await getFirstItem(workspaceA.id);
    const response = await api.patch(`/items/${item.id}`)
      .auth(userB.token)
      .send({ name: 'hijacked' });
    expect(response.status).toBe(404);
    const unchanged = await getItemById(item.id);
    expect(unchanged.name).toBe('Workspace A item');
  });
});
```

Return `404` (not `403`) for resources that exist but belong to another workspace — do not confirm existence to the requester.

---

## Caching and isolation

Every cached value that is workspace-scoped must include the workspace ID in the cache key:

```typescript
// Wrong — cache pollution across workspaces
const key = `items:${userId}`;

// Correct
const key = `workspace:${workspaceId}:items`;
const key = `user:${userId}:workspace:${workspaceId}:preferences`;
```

When a workspace's data changes, invalidate only that workspace's cache keys. Do not use `FLUSHDB` in production.

---

## Logging and observability

Every log line for a web product request must include `workspaceId` (and `userId` where available):

```json
{
  "level": "info",
  "msg": "item created",
  "workspaceId": "ws_01abc...",
  "userId": "usr_01def...",
  "itemId": "item_01ghi...",
  "traceId": "...",
  "duration_ms": 23
}
```

Without `workspaceId` on logs, debugging a production issue reported by a specific customer requires guessing which data is theirs.
