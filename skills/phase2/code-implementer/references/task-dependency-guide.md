# Task dependency guide: ordering implementation correctly

The order in which implementation tasks run matters. Wrong ordering causes integration failures, blocked engineers, and rework. This guide explains how to determine the correct order from the design doc.

---

## The dependency hierarchy

Implementation dependencies follow a general bottom-up pattern:

```
1. Data stores (migrations, schema)
        ↓
2. Domain models / entities (structs, types)
        ↓
3. Repository layer (database access)
        ↓
4. Service layer (business logic)
        ↓
5. Handler / controller layer (HTTP, gRPC, event consumers)
        ↓
6. Integration tests (crosses layers)
        ↓
7. Acceptance tests (crosses components)
```

Each layer depends on the layer below it. Do not implement a handler before the service exists, or a service before the repository exists.

---

## Cross-component dependencies

When multiple components interact, the order is:

1. **Implement the provider before the consumer.** If Component A calls Component B, implement B first (at least the interface/contract) before implementing A's integration with it.
2. **Implement shared libraries/utilities before consumers.** If multiple components use a common auth middleware, implement the middleware first.
3. **Implement event producers before event consumers.** If Component A publishes an event that Component B consumes, implement A's publish logic first so B can be tested end-to-end.

---

## Identifying dependencies from the design doc

**From Section 3 (Component design):**
- Read each component's "Inputs" — the component that provides that input must be implemented first
- Read "Dependencies" — these are implementation prerequisites

**From Section 4 (Data flows):**
- Read each sequence diagram left-to-right and top-to-bottom — this is the call order
- The leftmost actor is always the consumer; the rightmost is always the provider
- Providers must be implemented before consumers can be tested end-to-end

**From Section 6 (Data models):**
- Migrations must run before any code that uses the table
- Tables with foreign keys: implement the referenced table first, then the referencing table

---

## Dependency matrix

When planning a phase, build a dependency matrix before writing code:

```
Task        | Depends on         | Required before
---------------------------------------------------------------------------
1.1 Schema  | Nothing           | 1.2, 1.3, 1.4
1.2 Models  | 1.1 Schema        | 1.3, 1.4, 1.5
1.3 Repository | 1.1 Schema, 1.2 Models | 1.4
1.4 Service | 1.3 Repository    | 1.5
1.5 Handler | 1.4 Service       | Integration tests
```

Topological sort this matrix to get the implementation order. Tasks with no dependencies can run in parallel if multiple engineers are available.

---

## Parallelisation

Some tasks can run in parallel if engineers are available:

**Safe to parallelise:**
- Two components with no shared interfaces (confirmed by checking Section 4 flows)
- Unit tests for separate layers (repository tests vs service tests can be written concurrently)
- Schema migration vs domain model definition (no runtime dependency — the migration creates the table, the model describes it)

**Not safe to parallelise:**
- Consumer before provider (the integration will fail)
- Two tasks that modify the same file or migration (merge conflicts and logic conflicts)
- A task and the review of a task it depends on

---

## Handling external dependencies

If a task depends on an external system (partner API, third-party service):

1. **Check if the spec is frozen.** If the spec is not frozen, do not implement the integration — implement a stub behind an interface and replace it when the spec is frozen.
2. **Implement an interface first.** Define the interface the external system must satisfy before implementing the real adapter. This allows tests to use a mock and real code to use the real adapter.
3. **Contract tests, not mocks.** Use `api-contract-enforcer` to verify the external system actually matches the spec — do not rely on mocks alone.

```go
// Good: interface defined first
type DeviceRegistryClient interface {
    RegisterDevice(ctx context.Context, req RegisterRequest) (RegisterResponse, error)
}

// Real implementation (depends on external system being available)
type HTTPDeviceRegistryClient struct { ... }

// Test implementation (no external dependency)
type MockDeviceRegistryClient struct { ... }
```

---

## When a dependency is blocked

If Task N.M is blocked because its dependency is not complete:

1. Record the block in `docs/implementation-status.md`
2. Identify what can be done while waiting:
   - Write unit tests for the blocked component using a mock/stub for the dependency
   - Implement the domain model and repository layers (these don't depend on the missing component)
   - Write the acceptance scenario (BDD feature file) — this doesn't require implementation
3. Do not implement around the block by making assumptions — this produces integration failures when the dependency arrives

---

## Phase boundary rule

No task from Phase N+1 may start until all tasks in Phase N are complete and the phase gate is passed. This is not negotiable.

**Why:** Phase N+1 tasks depend on Phase N outputs. If Phase N is incomplete, Phase N+1 tasks will encounter missing interfaces, missing data, or missing schema — and the resulting failures are harder to debug than the original incomplete state.

**Exception:** Domain modelling (entities, interfaces) for Phase N+1 may be drafted during Phase N as long as it is clearly marked as draft and not integrated. This allows engineers to think ahead without creating dependencies.
