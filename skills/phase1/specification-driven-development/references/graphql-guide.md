# GraphQL schema-first guide

Use this when writing a GraphQL schema as part of specification-driven development. The schema is the contract. Write it before any resolver code.

---

## Complete minimal schema example — Device Management API

```graphql
# device-management.graphql

scalar DateTime
scalar UUID

# ─── Enums ───────────────────────────────────────────────────────────────────

enum DeviceStatus {
  ONLINE
  OFFLINE
  PROVISIONING
  ERROR
}

enum DeviceType {
  EDGE_NODE
  GATEWAY
  SENSOR
}

# ─── Core types ──────────────────────────────────────────────────────────────

type Device {
  id: UUID!
  displayName: String!
  status: DeviceStatus!
  type: DeviceType!
  config: DeviceConfig!
  owner: User!                    # resolved via DataLoader — see N+1 section
  telemetry: [TelemetryEvent!]!   # paginated; see connection pattern below
  createdAt: DateTime!
  updatedAt: DateTime!

  # Deprecated field — kept for backward compat during migration
  name: String @deprecated(reason: "Use displayName. Will be removed after 2026-07-01.")
}

type DeviceConfig {
  reportingIntervalSeconds: Int!
  tags: [String!]!
  metadata: String              # JSON blob; nullable — may not exist
}

type User {
  id: UUID!
  email: String!
  devices: [Device!]!
}

type TelemetryEvent {
  id: UUID!
  deviceId: UUID!
  payload: String!              # JSON; schema-validated at ingestion
  recordedAt: DateTime!
}

# ─── Pagination (Connection pattern) ─────────────────────────────────────────

type DeviceConnection {
  edges: [DeviceEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type DeviceEdge {
  node: Device!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# ─── Input types (all mutations use input types) ──────────────────────────────

input CreateDeviceInput {
  displayName: String!
  type: DeviceType!
  ownerId: UUID!
  config: DeviceConfigInput
}

input DeviceConfigInput {
  reportingIntervalSeconds: Int
  tags: [String!]
  metadata: String
}

input UpdateDeviceInput {
  displayName: String
  config: DeviceConfigInput
}

input DevicesFilterInput {
  status: DeviceStatus
  type: DeviceType
  ownerId: UUID
}

# ─── Root types ───────────────────────────────────────────────────────────────

type Query {
  device(id: UUID!): Device             # nullable — returns null if not found
  devices(
    filter: DevicesFilterInput
    first: Int
    after: String
  ): DeviceConnection!
  me: User!
}

type Mutation {
  createDevice(input: CreateDeviceInput!): Device!
  updateDevice(id: UUID!, input: UpdateDeviceInput!): Device!
  deleteDevice(id: UUID!): Boolean!
  provisionDevice(id: UUID!): Device!
}

type Subscription {
  deviceStatusChanged(deviceId: UUID!): Device!
  telemetryReceived(deviceId: UUID!): TelemetryEvent!
}
```

Key decisions visible in this schema:
- `device(id)` is nullable (returns null for 404, not an error)
- All lists use the Connection pattern for pagination
- All mutations take a single input type — not positional scalars
- Subscriptions are scoped to a single device to control fan-out

---

## @deprecated usage pattern

GraphQL has no `/v2` URL. Retire fields by deprecating them, not by removing them.

```graphql
type Device {
  # Old field — kept alive, consumers still read it
  name: String @deprecated(reason: "Use displayName. Will be removed after 2026-07-01.")

  # New field — add alongside the old one, never rename
  displayName: String!
}
```

**Migration workflow:**

1. Add the new field to the schema. Ship the resolver.
2. Mark the old field `@deprecated` with a reason and removal date.
3. Track which clients still request the deprecated field (introspection logs or field-level metrics if your server supports it).
4. Once all clients have migrated, remove the field from the schema.
5. A schema snapshot test will catch the removal and force a deliberate update — this is the gate.

Never rename a live field. A rename is a remove + add: the old field disappears from existing queries and breaks clients silently if the client does not know to update.

---

## N+1 prevention — design for DataLoader

Every field that resolves a relationship is a potential N+1 problem. Design the schema knowing this.

**The problem:**
```
Query devices → [Device, Device, Device, ...]
For each Device → resolve owner → SELECT * FROM users WHERE id = ?
```
100 devices = 101 queries.

**Design rule:** Any field on a type that resolves by looking up another entity by ID must be batched. Document this requirement in the schema comment.

```graphql
type Device {
  # Resolved via UserLoader (DataLoader batch by owner ID).
  # Do NOT resolve this with a direct DB call per device.
  owner: User!
}
```

**DataLoader pattern (resolver implementation note — not schema, but document it):**

```typescript
// UserLoader batches all user IDs from a single query execution
const UserLoader = new DataLoader(async (ids: readonly string[]) => {
  const users = await db.users.findMany({ where: { id: { in: ids } } });
  return ids.map(id => users.find(u => u.id === id) ?? null);
});
```

**Schema smell to flag during review:** A chain of more than two nested relationship types in a single query path (e.g. `device.owner.organisation.billingPlan`) — each hop is a potential N+1. Flag it, either add pagination controls or document that field-level DataLoaders are required.

---

## Schema snapshot testing

Test that the schema has not changed without a deliberate update. This is the GraphQL equivalent of a contract test.

```typescript
// schema-snapshot.test.ts
import { printSchema } from 'graphql';
import { schema } from '../src/schema';

describe('GraphQL schema contract', () => {
  it('matches the committed schema snapshot', () => {
    const sdl = printSchema(schema);
    expect(sdl).toMatchSnapshot();
  });
});
```

**What this catches:**
- A resolver accidentally adds a field that was never in the spec
- A type change slips in without a spec update
- A field removal happens without going through the deprecation process

**When the snapshot fails:** The developer must explicitly update the snapshot (`--updateSnapshot`) and the diff goes into the PR for review. This is the gate — no silent schema changes.

**Also test:** Every type and field has at least one test that exercises the resolver. Schema snapshot alone does not verify correctness — it only verifies the contract has not changed.

---

## Federation subgraph example (Apollo Federation)

If the system uses federated GraphQL (multiple subgraphs composed into one graph):

```graphql
# devices-subgraph.graphql
# This subgraph owns: Device, DeviceConfig, TelemetryEvent

extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key", "@external", "@shareable"])

type Device @key(fields: "id") {
  id: UUID!
  displayName: String!
  status: DeviceStatus!
  config: DeviceConfig!
}

# Reference to User — owned by the users-subgraph
# This subgraph can resolve device fields on User, but does not own User
type User @key(fields: "id", resolvable: false) {
  id: UUID!
}
```

```graphql
# users-subgraph.graphql
# This subgraph owns: User

type User @key(fields: "id") {
  id: UUID!
  email: String!
  # This subgraph resolves devices by calling the devices-subgraph
  devices: [Device!]!
}

# Stub for Device — owned by devices-subgraph
type Device @key(fields: "id", resolvable: false) {
  id: UUID!
}
```

**Document in the spec (before implementation):**

| Type | Owning subgraph | Key field |
|------|----------------|-----------|
| `Device` | devices-subgraph | `id` |
| `DeviceConfig` | devices-subgraph | — (embedded) |
| `User` | users-subgraph | `id` |
| `TelemetryEvent` | telemetry-subgraph | `id` |

Resolve ownership disputes before freezing the schema. A type cannot be owned by two subgraphs.

---

## Common mistakes

### Nullable everything (the "defensive nullable" trap)

```graphql
# Wrong — nullable fields create ambiguity downstream
type Device {
  id: UUID
  displayName: String
  status: DeviceStatus
}

# Right — non-null only where the field is always present
type Device {
  id: UUID!           # always exists once created
  displayName: String!  # always set on creation
  status: DeviceStatus! # always has a value
  metadata: String    # may be absent — correctly nullable
}
```

Over-nullable schemas push null-checks into every client. Every `!` in the schema is a promise you must keep in every resolver. Make the promise when you can keep it; use nullable when you cannot.

### Deeply nested mutations

```graphql
# Wrong — nested mutations have inconsistent behaviour across servers
type Mutation {
  device: DeviceMutations!
}
type DeviceMutations {
  create(input: CreateDeviceInput!): Device!
  delete(id: UUID!): Boolean!
}

# Right — flat, operation-named mutations
type Mutation {
  createDevice(input: CreateDeviceInput!): Device!
  deleteDevice(id: UUID!): Boolean!
}
```

Nested mutations look elegant but break in unexpected ways (transaction semantics, error propagation). Keep mutations flat.

### Returning raw database objects

```graphql
# Wrong — leaks database structure, impossible to evolve independently
type Device {
  db_id: Int!
  created_timestamp: String!
  owner_user_id: Int!
}

# Right — domain-shaped API type, decoupled from storage
type Device {
  id: UUID!
  createdAt: DateTime!
  owner: User!
}
```

If your schema looks like your database schema, you have skipped the design step. The schema is a domain API, not a database view.

### Positional scalar arguments on mutations

```graphql
# Wrong — order-dependent, impossible to add optional args later
type Mutation {
  createDevice(name: String!, type: DeviceType!, ownerId: UUID!): Device!
}

# Right — input type is versioning-friendly and self-documenting
type Mutation {
  createDevice(input: CreateDeviceInput!): Device!
}
```

Every mutation argument must use an input type. No exceptions.

### No deprecation — just removing fields

Do not remove a field from a live schema without going through the `@deprecated` workflow. A field removal is a breaking change for any client that requests that field. The client will receive a query error, not a null — it will break.
