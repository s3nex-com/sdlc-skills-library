# RBAC design

B2B SaaS authorization lives on a spectrum. On one end, a fixed set of built-in roles (Owner, Admin, Member) the product ships with. On the other end, customers define their own roles with arbitrary permissions. This reference covers the permission model, when to stay RBAC vs reach for ABAC, enforcement rules that keep authorization honest, and the providers worth integrating with rather than building from scratch.

---

## The permission model

A permission is a `(resource, action)` pair. A role is a named bundle of permissions. A user in a tenant has one or more roles. Authorization is "does any of this user's roles grant `(resource, action)` in this tenant?".

```python
class Permission(str, Enum):
    REPORTS_READ = "reports:read"
    REPORTS_WRITE = "reports:write"
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"
    USERS_INVITE = "users:invite"
    USERS_MANAGE_ROLES = "users:manage_roles"

class Role:
    name: str
    tenant_id: UUID | None  # None = system role, shipped with product
    permissions: frozenset[Permission]

BUILTIN_ROLES = {
    "owner":  Role("owner",  None, frozenset(Permission)),
    "admin":  Role("admin",  None, frozenset(p for p in Permission if p != Permission.BILLING_MANAGE)),
    "member": Role("member", None, frozenset({Permission.REPORTS_READ})),
}
```

Rules that keep the model sane:

- Permissions are additive, never subtractive. A role grants; another role does not revoke. If you find yourself wanting a deny rule, you have discovered that RBAC is the wrong shape for that requirement.
- Resource scoping lives inside permission evaluation, not in the role. `reports:read` is granted; whether this specific report is readable is resolved at check time against tenant scope.
- One role rarely covers all of a product's surface. Two to five built-in roles is typical. Avoid the "super-admin with special cases" role — it metastasizes.
- System roles (`tenant_id IS NULL`) ship with the product. Custom roles (`tenant_id = T`) are created by customers and scoped to that tenant.

---

## Role hierarchy

A hierarchy lets an Admin inherit everything Member has, without listing permissions twice. Implement it by flattening at role-save time, not at check time. Flatten once, check fast.

```sql
CREATE TABLE roles (
  id uuid PRIMARY KEY,
  tenant_id uuid,                  -- NULL for system roles
  name text NOT NULL,
  parent_role_id uuid REFERENCES roles(id),
  permissions text[] NOT NULL,     -- flattened, includes inherited
  created_at timestamptz DEFAULT now(),
  created_by uuid
);

CREATE UNIQUE INDEX roles_name_per_tenant
  ON roles (coalesce(tenant_id, '00000000-0000-0000-0000-000000000000'), name);
```

Recompute `permissions` when the role or any ancestor changes. Cache check results per request, not across requests.

---

## Custom roles

The enterprise tier will ask for custom roles. Build them as:

1. A UI for an admin to create a role, pick a name, and tick permissions from the full permission catalogue.
2. A server-side check that refuses to save a role that grants permissions the product does not expose (defence against stale front-end).
3. A protected list of permissions only system roles may hold (`tenant:delete`, `billing:manage` in some pricing models). Custom roles cannot grant these.
4. An export / import format so a customer with 40 tenants can replicate their role catalogue without clicking through 40 admin UIs.

Custom roles that exist but grant zero users anything are not a problem. Custom roles that grant one user everything usually are — flag roles with `permissions = all` and review them quarterly.

---

## RBAC vs ABAC

RBAC: authorization is a function of the user's roles. Static, predictable, auditable, the right default for B2B SaaS.

ABAC: authorization is a function of arbitrary attributes (user, resource, environment). Dynamic, flexible, hard to reason about. Appropriate when the authorization model is genuinely attribute-driven: "users in the Sales team can read deals in their region where the deal amount is under their approval limit".

Decision rule:

- Start RBAC. Stay RBAC until a real requirement forces otherwise.
- Move one specific decision to ABAC rather than converting the whole system. Policy-based tools (OPA, Cedar, Oso) let you express the attribute rule for that one decision while the rest stays RBAC.
- If you end up with dozens of roles that differ only by "but not for this team" or "only on Tuesdays", you have discovered ABAC by accretion. Rewrite that portion intentionally.

A hybrid example: RBAC for "can this user access the reports area at all?", ABAC for "which specific reports in that area can they see?".

---

## Enforcement at the API / service layer

UI authorization (hiding buttons) is a usability feature, not a security feature. Every authorization decision must be enforced server-side at the API or service boundary. A user who knows the endpoint can always curl it.

Enforcement pattern — a decorator / middleware that wraps every handler:

```python
def require(permission: Permission):
    def decorator(handler):
        @wraps(handler)
        async def wrapped(request, *args, **kwargs):
            user = current_user(request)
            tenant = current_tenant()
            if not authz.has(user, tenant, permission):
                raise Forbidden(f"missing {permission.value}")
            return await handler(request, *args, **kwargs)
        return wrapped
    return decorator

@router.post("/reports")
@require(Permission.REPORTS_WRITE)
async def create_report(request, body: ReportCreate):
    ...
```

Rules:

- Every endpoint that mutates or returns tenant data must pass through `@require`. A handler without an authz decorator fails code review.
- Resource-specific checks (can this user access THIS report) happen inside the handler after the permission check. The permission gate is the broad sieve; the resource check is the fine filter.
- Background jobs and queue consumers reuse the same authz module, never a looser one. A job that runs "as the tenant" still makes permission checks — it just runs them against a system principal with scoped permissions.
- Test authz with at least one negative test per endpoint (authenticated user lacking the required permission gets 403).

---

## Audit logging for permission changes

Every change to the authorization surface is high-value audit data. Log it in a dedicated, append-only table.

```sql
CREATE TABLE authz_audit_log (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL,
  actor_user_id uuid NOT NULL,
  action text NOT NULL,      -- 'role.create', 'role.update', 'user.role.grant', 'user.role.revoke', 'role.delete'
  target_user_id uuid,
  target_role_id uuid,
  payload jsonb NOT NULL,    -- full before/after snapshot
  occurred_at timestamptz NOT NULL DEFAULT now(),
  request_id text,
  ip_address inet
);
```

Events to log:

- Role created, updated, deleted
- Role assigned to user, revoked from user
- Permission added to or removed from a role
- System role overridden (if the product allows it)
- SCIM-driven role sync operations (label the actor differently so human vs automated changes are distinguishable)

Surface this log in the tenant admin UI. Enterprise customers will ask for it during security review, and "we write to a log table" is not the same as "the customer can see the log".

---

## Providers — WorkOS, Auth0, Clerk

For small teams, building the full identity stack (SSO, SCIM, directory sync, MFA, session management) is months of work that returns zero product differentiation. Buy it.

| Provider | Fits when |
|----------|-----------|
| WorkOS | You want SAML SSO, SCIM, and Directory Sync as separable APIs. Opinionated toward B2B enterprise. Docs aimed at engineers. |
| Auth0 | You want a broad identity platform including consumer logins, passwordless, social. Heavier SDK footprint. Older rules / actions model. |
| Clerk | You want UI components for auth out of the box and your app is React-first. Strong developer experience. B2B features catching up. |
| Stytch | Similar positioning to WorkOS; stronger on passwordless. |
| Ory | Self-hosted option if you cannot use SaaS identity. Operational burden falls on you. |

Integration rules:

- The provider owns authentication. Your app owns authorization. Roles, permissions, and the tenant-scoped role assignment table stay in your database.
- Map provider-issued tokens to your User record on every request. The provider's `user_id` is an external identifier; your internal `user_id` is primary.
- Keep the authorization check local. A network call per authz check is a latency and availability bug waiting to happen.
- Have an exit plan. Every identity provider eventually prices out, has an outage during your launch, or gets acquired. Know what it takes to switch.

---

## Verification checklist

- Every HTTP route that returns or mutates tenant data has a server-side authz decorator.
- At least one negative test per endpoint confirms 403 for a user missing the required permission.
- Authz audit log captures every role and permission-assignment change.
- Custom-role UI refuses to grant permissions the product does not expose.
- A user removed from all roles loses access immediately (session revocation on role revoke).
- System roles cannot be deleted by a tenant admin.
