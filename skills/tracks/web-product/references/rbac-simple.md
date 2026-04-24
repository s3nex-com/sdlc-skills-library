# Simple RBAC for web products

## The standard three-role model

Most web products with workspaces/teams need exactly three roles:

| Role | Who | What they can do |
|------|-----|-----------------|
| **Owner** | 1 per workspace (the creator) | Everything — including deleting the workspace and transferring ownership |
| **Admin** | 0 to N per workspace | Manage members (invite, remove, change roles), manage billing, manage workspace settings, do everything a Member can do |
| **Member** | 0 to N per workspace | Use the product — create, read, update, delete their own resources; read shared resources |

Start with this. Add roles only when you have a real use case, not in anticipation.

---

## Permission naming convention

Use `resource:action` format. Consistent naming makes permission checks readable and auditable.

```
items:create
items:read
items:update
items:delete
members:invite
members:remove
members:change-role
billing:read
billing:manage
workspace:settings:read
workspace:settings:update
workspace:delete
```

Group permissions into role definitions:

```typescript
const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  owner: [
    'items:create', 'items:read', 'items:update', 'items:delete',
    'members:invite', 'members:remove', 'members:change-role',
    'billing:read', 'billing:manage',
    'workspace:settings:read', 'workspace:settings:update',
    'workspace:delete',
  ],
  admin: [
    'items:create', 'items:read', 'items:update', 'items:delete',
    'members:invite', 'members:remove', 'members:change-role',
    'billing:read', 'billing:manage',
    'workspace:settings:read', 'workspace:settings:update',
  ],
  member: [
    'items:create', 'items:read', 'items:update', 'items:delete',
    'workspace:settings:read',
  ],
};
```

---

## Enforcement location

**Enforce at the service layer, not only in the UI.** A disabled button or hidden route is UX, not security.

```typescript
// Wrong — only UI guard, no server enforcement
<Button disabled={user.role !== 'admin'} onClick={deleteWorkspace}>Delete</Button>

// Correct — service layer check
async function deleteWorkspace(ctx: RequestContext, workspaceId: string) {
  requirePermission(ctx, 'workspace:delete'); // throws 403 if not permitted
  await db.workspace.delete({ where: { id: workspaceId } });
}

function requirePermission(ctx: RequestContext, permission: Permission) {
  const allowed = ROLE_PERMISSIONS[ctx.user.role];
  if (!allowed.includes(permission)) {
    throw new ForbiddenError(`Missing permission: ${permission}`);
  }
}
```

**Router-level middleware** for coarse-grained protection (e.g., all `/admin/*` routes require admin+):

```typescript
router.use('/admin', requireRole(['admin', 'owner']));
```

**Service-layer checks** for fine-grained control (e.g., only the resource owner or admin can delete):

```typescript
async function deleteItem(ctx: RequestContext, itemId: string) {
  const item = await db.item.findUnique({ where: { id: itemId } });
  if (!item) throw new NotFoundError();

  const canDelete =
    item.createdById === ctx.user.id ||  // own resource
    hasPermission(ctx, 'items:delete');   // or elevated role

  if (!canDelete) throw new ForbiddenError();

  await db.item.delete({ where: { id: itemId } });
}
```

---

## RBAC vs ABAC

| Use RBAC | Use ABAC |
|----------|----------|
| Permission depends only on the user's role | Permission depends on the resource's attributes or relationships |
| "Admins can delete any item" | "Users can delete items they created; admins can delete any item" |
| Simple to reason about and audit | More expressive but harder to audit |

Most web products start with RBAC. Add ABAC conditions (ownership, resource state) when a business rule requires it. Mix freely — the example above (`item.createdById === ctx.user.id OR hasPermission`) is a minimal ABAC extension on top of RBAC.

---

## Invitation flow

```
1. Admin or Owner clicks "Invite member"
2. Enter email address + choose role
3. Server creates an invitation record:
   { id, workspaceId, email, role, token: UUID, expiresAt: now + 7 days, status: 'pending' }
4. Send invitation email with link: https://app.example.com/invite/{token}
5. Recipient clicks link:
   a. If not logged in → signup/login flow → then accept
   b. If logged in → confirm acceptance
6. Server: verify token, not expired, not already accepted
7. Create membership: { userId, workspaceId, role }
8. Mark invitation as accepted
9. Redirect to workspace
```

**Edge cases to handle:**
- Email already has a membership in this workspace → show error, do not create duplicate
- Token expired → show "link expired" with option to request a new one
- Token already used → show "already accepted" message
- User signs up with a different email than invited → match on token, not email (they chose their signup email)

---

## Role change and removal

```typescript
// Only owners can change another owner's role
async function changeMemberRole(ctx: RequestContext, targetUserId: string, newRole: Role) {
  requirePermission(ctx, 'members:change-role');

  const target = await getMembership(targetUserId, ctx.workspaceId);
  if (target.role === 'owner' && ctx.user.role !== 'owner') {
    throw new ForbiddenError('Only an owner can change another owner\'s role');
  }
  if (ctx.user.id === targetUserId) {
    throw new BadRequestError('Cannot change your own role');
  }

  await db.membership.update({
    where: { userId: targetUserId, workspaceId: ctx.workspaceId },
    data: { role: newRole },
  });

  await logAuditEvent(ctx, 'member.role-changed', { targetUserId, from: target.role, to: newRole });
}
```

**Audit log every role change.** Who changed whose role, from what to what, and when. This is essential for debugging access issues and for compliance.

---

## Audit logging for permission events

Log these events at minimum:

| Event | Data to log |
|-------|-------------|
| `member.invited` | workspaceId, invitedEmail, role, invitedBy |
| `member.joined` | workspaceId, userId, role, via (invitation or direct) |
| `member.removed` | workspaceId, removedUserId, removedBy |
| `member.role-changed` | workspaceId, userId, fromRole, toRole, changedBy |
| `workspace.deleted` | workspaceId, deletedBy |
| `billing.plan-changed` | workspaceId, fromPlan, toPlan, changedBy |

Store audit logs in a separate table or append-only log service. Do not delete audit log entries.

---

## Testing RBAC

```typescript
describe('RBAC: items:delete', () => {
  it('member cannot delete another member\'s item', async () => {
    const { workspace, userA, userB } = await setupWorkspace({ roles: ['member', 'member'] });
    const item = await createItem({ workspaceId: workspace.id, createdById: userA.id });

    const res = await api.delete(`/items/${item.id}`).auth(userB.token);
    expect(res.status).toBe(403);
  });

  it('admin can delete any item', async () => {
    const { workspace, admin, member } = await setupWorkspace();
    const item = await createItem({ workspaceId: workspace.id, createdById: member.id });

    const res = await api.delete(`/items/${item.id}`).auth(admin.token);
    expect(res.status).toBe(200);
  });

  it('member can delete their own item', async () => {
    const { workspace, member } = await setupWorkspace();
    const item = await createItem({ workspaceId: workspace.id, createdById: member.id });

    const res = await api.delete(`/items/${item.id}`).auth(member.token);
    expect(res.status).toBe(200);
  });
});
```

One test per role per sensitive operation. Not one test per endpoint — test the permission boundary.
