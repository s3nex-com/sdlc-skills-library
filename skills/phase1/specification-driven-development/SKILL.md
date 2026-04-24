---
name: specification-driven-development
description: >
  Governs contract-first and specification-driven development — defining interfaces,
  schemas, and workflows before implementation begins. Use this skill whenever the
  user wants to: write an OpenAPI 3.x specification, author a Protobuf or gRPC schema,
  define an AsyncAPI spec for event-driven interfaces, write a GraphQL schema, write a
  JSON Schema, review an API contract for completeness or correctness, detect breaking
  vs non-breaking changes, design a workflow or sequence before coding it, or validate
  that an implementation matches its contract. Also trigger for: "define the interface
  before coding", "API spec", "contract-first", "freeze the contract", "service contract",
  "define the schema", "sequence diagram", "API design", "contract review", "Protobuf",
  "AsyncAPI", "OpenAPI", "gRPC schema", "GraphQL schema", "schema-first GraphQL",
  "write the schema before resolvers", "GraphQL API design".
---

# Specification-driven & contract-first development

## Purpose

No code is written until the interfaces, contracts, schemas, and workflows are defined. If the interface is ambiguous before implementation, integration becomes a debugging marathon.

**The contract is the truth. Code is secondary.** When an implementation deviates from the contract, the implementation is wrong, not the contract.

## When to use

- Writing a new API specification (OpenAPI, Protobuf, AsyncAPI, GraphQL)
- Reviewing an API spec before development begins or before freezing
- Defining a JSON Schema for a payload, event, or configuration file
- Freezing a contract so implementation can begin
- Detecting whether a proposed change is breaking or non-breaking
- Designing a workflow or multi-step interaction before implementation
- Defining Kafka topic schemas, NATS subjects, or any event-driven interface (use AsyncAPI spec first, publish/subscribe code second)
- Building event-driven microservices where producers and consumers are in separate services or repositories
- Working on IoT telemetry streams, device lifecycle events, or any system where messages flow asynchronously
- Adding a new event type to an existing Kafka or NATS system (treat this as a contract change — spec it before implementing)
- Designing a GraphQL API: write the schema first, agree on it with the team, then implement resolvers

## When NOT to use

- Enforcing the spec at runtime or in CI (contract tests, consumer-driven contracts, breaking-change detection in pipelines) → `api-contract-enforcer`
- Decomposing product requirements into user stories and BDD acceptance criteria → `requirements-tracer`
- Producing the `DESIGN.md` that integrates the contract into the technical design → `design-doc-generator`
- Recording the decision to adopt a particular protocol or schema pattern → `architecture-decision-records`
- Reviewing the system architecture the contract sits within → `architecture-review-governance`
- Generating the public API reference documentation from an accepted spec → `documentation-system-design`

## Process

1. Identify all API surfaces that need a contract: list every REST endpoint group, gRPC service, event channel, or GraphQL schema from the user stories or PRD.
2. Pick one spec format per interface: OpenAPI for REST, Protobuf for gRPC, AsyncAPI for event-driven, GraphQL SDL for GraphQL. Never mix formats for the same interface.
3. Write the full spec before writing any implementation code. For REST: every operation needs operationId, description, success response, and documented error responses (400/401/403/404/500). For events: define every message schema in components/messages; specify delivery guarantees in the channel description.
4. Define a consistent error envelope schema once and reference it everywhere. Do not inline error schemas.
5. Run the contract review checklist from `references/contract-review-checklist.md`. Focus on: error model completeness, versioning strategy, ambiguous field semantics, required vs optional.
6. For REST specs: run `scripts/validate_openapi.py` to verify structural correctness before freezing.
7. Freeze the contract: tag the spec in version control, confirm the spec is final (a PR merge or explicit team message suffices — no ceremony required).
8. For any change to a frozen contract: run `scripts/diff_contracts.py` to classify breaking vs non-breaking. Breaking changes require an ADR.
9. Render and publish the frozen spec so consumers can explore it without opening the raw file (Swagger UI, Redoc, or `/docs` route).
10. Append the execution log entry.

## Contract-first workflow

1. **Define the contract** — Write the full API spec before any implementation code. Pick one spec format per interface: OpenAPI for REST, Protobuf for gRPC, AsyncAPI for events.
2. **Review the contract** — Use `references/contract-review-checklist.md` to verify completeness (error model, versioning, ambiguous field semantics)
3. **Freeze** — The spec is frozen when implementation starts. "Frozen" means: no changes without an ADR and re-evaluation of affected implementation. A message in Slack or a commit message confirming the spec is final is sufficient — no ceremony required.
4. **Implement** — Build to the frozen spec. Any deviation creates an ADR.
5. **Validate** — Contract tests verify that implementations honour the spec

## OpenAPI 3.x specifications

Use `references/openapi-guide.md` for complete guidance. Key requirements:

- Every operation must have an `operationId` (unique, descriptive, camelCase)
- Every operation must have a description
- Every operation must define responses for: success (2xx), client error (400/422), authentication failure (401), authorisation failure (403), not found (404 if applicable), and server error (500)
- Error responses must use a consistent error envelope schema — define it once in `components/schemas` and `$ref` everywhere
- Request body schemas must define all fields as required or optional, with types and constraints
- All shared schemas go in `components/schemas` — never inline complex schemas in path items

### Error envelope standard

Define a consistent error response schema and use it for all error responses:

```yaml
components:
  schemas:
    ErrorResponse:
      type: object
      required: [error, message]
      properties:
        error:
          type: string
          description: Machine-readable error code
          example: validation_error
        message:
          type: string
          description: Human-readable error description
          example: Required field missing: device_type
        field:
          type: string
          description: The field that caused the error, if applicable
          example: device_type
        request_id:
          type: string
          description: Request ID for correlation with server logs
          example: req-abc-123
```

## Protobuf schemas

Use `references/protobuf-guide.md` for complete guidance. Key rules:

- Field numbers must never be reused after removal — mark removed fields as `reserved`
- Use well-known types from `google/protobuf/` (Timestamp, Duration, Empty) rather than reinventing them
- Services must define all RPCs with proper request and response messages
- Never use field number 1 for a field that might be removed — number 1 gets special encoding treatment

## AsyncAPI specifications

Use `references/asyncapi-guide.md` for event-driven interfaces. Key requirements:

- Define every message schema in the `components/messages` section
- Specify the protocol binding (Kafka, MQTT, AMQP) in the channel bindings
- Document the consumer group or subscription model expected
- Define whether messages use schema registry validation

### Event-driven contract workflow

Event-driven systems have two sides of the contract: the producer publishes a message; the consumer reads it. Both sides must agree on the schema before either is built.

**Steps for defining an event-driven contract:**

1. **Define channel schemas first.** Write the AsyncAPI spec before any producer or consumer code. The spec is the single source of truth — not the first service that happened to publish something.

2. **Define the message envelope explicitly.** Every event message must document:
   - `schema_version` — the schema version, as a field in the payload (not just in the channel name)
   - `correlation_id` — for tracing a request across multiple async hops
   - `timestamp` — when the event occurred (device time), not when it was ingested
   - `event_id` — a UUID for idempotency; consumers use this to deduplicate

   ```yaml
   # Minimum required envelope fields for every event type
   required: [event_id, schema_version, correlation_id, timestamp]
   properties:
     event_id:
       type: string
       format: uuid
       description: Unique event ID. Consumers use this for deduplication.
     schema_version:
       type: string
       example: "1.0"
       description: Schema version. Consumers use this to select a deserialiser.
     correlation_id:
       type: string
       description: Trace ID propagated from the originating request.
     timestamp:
       type: string
       format: date-time
       description: When the event occurred (source time, not ingestion time).
   ```

3. **Specify delivery guarantees in the spec.** Document the delivery semantic for each channel:

   | Guarantee | When to use |
   |-----------|-------------|
   | At-most-once | Telemetry where occasional loss is acceptable (high-frequency sensor data) |
   | At-least-once | Events that must be processed but consumers are idempotent |
   | Exactly-once | Financial or state-change events; requires consumer deduplication on `event_id` |

   Put this in the channel `description` — it is part of the contract, not the implementation.

4. **Consumer contract testing.** Consumers must validate schema evolution:
   - Adding a new optional field: consumers must ignore unknown fields. Test this explicitly — deploy a producer with the new field; verify the old consumer still processes events without error.
   - Removing a field: this is a breaking change. It requires a new schema version and a migration window. Spec the new channel version (`v2`) before removing from `v1`.
   - Changing a field type: always breaking. Never do this without a new schema version.

### Backward and forward compatibility rules

| Change type | Compatible? | Required action |
|-------------|-------------|-----------------|
| Add optional field to payload | Forward-compatible | Update spec, increment minor version (`1.0` → `1.1`). Consumers must ignore unknown fields. |
| Add required field to payload | Breaking | New schema version, new channel (`v2`). Run both channels during migration window. |
| Remove any field | Breaking | New schema version. Never remove from a live channel without a deprecation period. |
| Change field type | Breaking | New schema version. |
| Change field from optional to required | Breaking | New schema version. |
| Rename a field | Breaking | Treat as remove + add. |

**Deprecation process for a field:**
1. Mark the field as `deprecated: true` in the spec with a `description` note: "Deprecated. Will be removed in schema v2.0. Use `new_field_name` instead."
2. Run both old and new field in the payload during the migration window (typically one sprint for internal consumers, longer for external).
3. Confirm all consumers have migrated before removing.

**Channel versioning convention:** Use the version in the channel name (`edgeflow.telemetry.events.v1`, `edgeflow.telemetry.events.v2`). Do not reuse a channel name for a schema-breaking change — consumers cannot independently choose when to migrate if the channel name changes under them.

## GraphQL specifications

Use `references/graphql-guide.md` for complete guidance. Key rules:

### Schema-first development

Write the `.graphql` schema file before any resolver code. The schema is the contract — resolvers are the implementation. Any resolver that returns data not in the schema is a defect.

### Type system basics

Every schema must define:
- `Query` — all read operations
- `Mutation` — all write operations (if any)
- `Subscription` — all real-time operations (if any)
- Custom types, input types, enums, and scalars

### Schema design rules

- **Non-null (`!`) only for fields guaranteed to always exist.** If there is any code path that can produce null, the field must be nullable. Over-using non-null causes runtime panics and makes schema evolution harder.
- **Design for DataLoader from the start.** Every field that resolves a relationship (e.g. `device.owner`) is a potential N+1 query. If you cannot batch it, document why. The schema design must account for this — deeply nested relationship chains are a schema smell.
- **Avoid deeply nested mutations.** Mutations should be flat and operation-focused (`createDevice`, `updateDeviceConfig`), not nested under parent types. Nested mutations have inconsistent behaviour across GraphQL servers.
- **Input types for all mutation arguments.** Never pass multiple scalar arguments to a mutation directly. Use an input type — it is easier to version.

### Versioning

GraphQL schemas do not version like REST. There is no `/v2` URL. Evolution rules:

| Action | Rule |
|--------|------|
| Add a new field | Safe — clients that do not request it are unaffected |
| Add a new type | Safe |
| Remove a field | Breaking — use `@deprecated` first, remove only after all clients have migrated |
| Rename a field | Breaking — treat as deprecate + add |
| Change a field type | Breaking — avoid; if necessary, add a new field with the new type |
| Add a non-null argument | Breaking |

**Deprecation pattern:**
```graphql
type Device {
  id: ID!
  # Deprecated: use displayName instead
  name: String @deprecated(reason: "Use displayName. Will be removed in schema v2.")
  displayName: String!
}
```

Add new fields alongside deprecated ones. Never rename a live field. Run both during the migration window.

### Federation

If using Apollo Federation or a similar federated GraphQL approach:
- Define subgraph boundaries in the spec before implementation. Each subgraph owns specific types.
- Document the `@key` fields (entity identifiers) for each type in the spec.
- Types referenced across subgraphs must be listed in `references/graphql-guide.md` under "Subgraph ownership".
- A type cannot be owned by two subgraphs — resolve ownership before freezing the schema.

### Contract testing for GraphQL

Test against the schema, not against specific query strings from consumers.

- **Schema snapshot tests:** Capture the schema SDL and fail the build if it changes without a deliberate update. Consumers rely on the schema, not on implementation internals.
- **Type coverage:** Every type and field in the schema must be exercised by at least one test.
- **Do not mock the schema for contract tests.** Run against the real resolver with a real (test) data source. Mocking the schema validates nothing.

---

## Contract review

Before freezing any contract, work through every item in `references/contract-review-checklist.md`. Focus especially on:

- **Error model completeness** — does every error scenario have a defined response?
- **Versioning** — is the version clear in the spec? Is the versioning strategy consistent?
- **Ambiguous field semantics** — does every field have a description that removes ambiguity?
- **Required vs optional fields** — is every optional field documented with its default behaviour?

## Contract freeze process

A frozen contract is locked — no changes without an ADR and re-evaluation of affected implementation.

Process:
1. Complete the contract review checklist
2. Confirm the spec is ready (a commit message, PR merge, or explicit team message suffices)
3. Tag the spec in version control with a version tag (e.g., `v1.0.0`)
4. Any subsequent change: run `scripts/diff_contracts.py` to classify breaking vs non-breaking. Breaking changes require an ADR and coordination with anyone consuming the API.

## Spec publishing

A frozen spec that only exists as a file in the repo is not documentation for consumers. Once a spec is frozen, it must be rendered and accessible.

**Options (pick one):**

| Option | When to use |
|--------|-------------|
| Swagger UI via `/docs` route | API server already running; add one endpoint |
| Redoc static build | Static site or CI-generated docs; zero runtime cost |
| Swagger UI Docker sidecar | Local dev only; no code change to the API |

**Minimum bar:** A developer who has never seen the codebase must be able to explore all endpoints, see request/response schemas, and read field descriptions without opening any `.yaml` or `.json` file.

**Add to the contract freeze checklist:**
- [ ] Spec is rendered and the URL is documented in the root README

---

## Validation

Use `scripts/validate_openapi.py` to check OpenAPI specs for structural completeness before review.
Use `scripts/diff_contracts.py` to evaluate changes to a frozen contract.

## Output format

### API spec review findings

**Spec:** [filename and version]
**Reviewer:** [name]
**Date:** [date]

| # | Finding | Section | Severity | Recommendation |
|---|---------|---------|----------|----------------|

**Overall assessment:** [Ready to freeze / Needs revision / Major issues]

### Contract change assessment

**Change type:** Breaking / Non-breaking / Additive
**Affected consumers:** [list of services/teams that must update]
**Required actions:** [what each consumer must do]

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] specification-driven-development — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] specification-driven-development — OpenAPI spec written for ingestion API v2
[2026-04-20] specification-driven-development — Contract review: 2 breaking changes identified
[2026-04-20] specification-driven-development — Contracts frozen for Sprint 14
```

---

## Reference files

- `references/openapi-guide.md` — Complete OpenAPI 3.x guide with worked example (Device Telemetry API)
- `references/protobuf-guide.md` — Protobuf guide with backward compatibility rules and worked example
- `references/asyncapi-guide.md` — AsyncAPI 2.x guide with event-driven worked example
- `references/graphql-guide.md` — GraphQL schema-first guide: full schema example, @deprecated pattern, DataLoader design, schema snapshot testing, federation subgraph example, common mistakes
- `references/contract-review-checklist.md` — 35+ item checklist for reviewing any contract
- `references/contract-freeze-process.md` — Step-by-step contract freeze and change process

## Scripts

- `scripts/validate_openapi.py` — Validates an OpenAPI spec for structural correctness and completeness
- `scripts/diff_contracts.py` — Compares two OpenAPI versions and categorises all changes
