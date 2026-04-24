# Schema registry design

A schema registry is the gatekeeper between producers and consumers. It stores every schema version, enforces compatibility rules on new versions, and serves schemas at read time so consumers can deserialize correctly. Without a registry, your data contracts are wishes. With a registry and the wrong compatibility mode, you will either ship breaking changes daily or freeze the schema forever.

This document covers compatibility modes, how to pick one, schema evolution plans, serialization formats, and what to do when you must break compatibility.

---

## Compatibility modes

A registry enforces compatibility on **write** (producer registers a new schema version) and sometimes on **read** (consumer deserializes with an older or newer schema). The four standard modes — using Confluent Schema Registry terminology — are:

### BACKWARD (default — pick this unless you have a reason not to)

**Rule:** a new schema version can be read by consumers using the previous schema version.

**Allows:** delete optional fields, add optional fields with a default, broaden types in a compatible way.

**Blocks:** add required field without default, change field type incompatibly, rename a field.

**When to use:** the common case. Consumers upgrade at their own pace. Producers upgrade first. This is what you want for most event streams and most warehouse tables.

### FORWARD

**Rule:** data produced with a new schema can be read by consumers using the previous schema.

**Allows:** add required fields, delete optional fields.

**Blocks:** add optional fields that consumers on the old schema would then not know about.

**When to use:** rare. Useful when consumers upgrade before producers — e.g. a slow-to-deploy mainframe consumer that cannot be upgraded quickly, but a fast-moving producer keeps adding data.

### FULL

**Rule:** BACKWARD and FORWARD combined. New schema is compatible in both directions.

**Allows:** add or delete optional fields.

**Blocks:** add required fields, delete required fields, change types.

**When to use:** when producer and consumer upgrade independently and in any order. More restrictive, so schemas evolve more slowly — but gives the widest compatibility window. Good for long-lived contracts with many independent consumers.

### NONE

**Rule:** no compatibility enforcement. Any change is allowed.

**When to use:** only inside a tightly coupled team that deploys producer and all consumers atomically, or for an experimental topic where breakage is tolerable. If you set NONE in production, write down why, because future-you will want to know.

---

## Picking a mode — decision table

| Situation | Mode |
|-----------|------|
| Public event topic with many internal consumers on different release cadences | BACKWARD |
| Warehouse table consumed by analysts and dashboards | BACKWARD |
| Topic with one producer and one consumer in the same team, same deploy | NONE (pragmatic) or BACKWARD (correct) |
| Event topic where consumers must be upgraded before producers (rare legacy case) | FORWARD |
| Long-lived public contract, many external consumers, unknown release cadences | FULL |
| Schema is experimental, topic is marked `draft` in the contract | NONE |

Default is BACKWARD. Deviate only with a written reason in the contract.

---

## Schema evolution plan

Every schema change needs a plan before it lands. The plan answers five questions:

1. **Is this additive or breaking?** Additive = new optional field, new enum value (if consumers tolerate unknown values), widened type. Breaking = removed field, renamed field, required field added without default, type narrowing.
2. **Which compatibility mode does this need to respect?** Check the registry setting.
3. **What version bump?** Minor for additive. Major for breaking. Patch for metadata only.
4. **Who are the consumers?** Pull the consumer list from the contract. Count them. If zero, this is easy. If many, this is a migration project.
5. **What is the rollout order?** Usually: new schema registered → producer upgraded → consumers upgraded (at their pace, within the deprecation window for breaking). Never the reverse.

### Additive change — worked example

Add an optional `utm_campaign` field to `events.user_signup`.

1. Additive.
2. BACKWARD compatible (new optional field with default `null`).
3. Minor bump: 2.1.0 → 2.2.0.
4. Consumers: all three existing consumers. None of them currently read this field — no action required on their side.
5. Rollout: register new schema (passes BACKWARD check), deploy producer, consumers continue unchanged.

Total effort: one PR.

### Breaking change — worked example

Rename `source` to `acquisition_channel` in `events.user_signup`. `source` is used by two of three consumers.

1. Breaking (rename = delete + add).
2. BACKWARD does not allow a bare rename. Must be done as a two-phase migration.
3. Major bump on completion: 2.2.0 → 3.0.0.
4. Consumers: growth.signup_dashboard and warehouse.dim_user_load read `source`. Both must migrate.
5. Rollout:
   - **Phase 1 (minor bump, 2.3.0):** add `acquisition_channel` as optional, populate it from `source` for every emitted event. `source` remains. Register new schema, deploy producer. Consumers can read either field. This is BACKWARD compatible.
   - **Deprecation window:** 30 days. Announce on the contract PR, add a note to the contract's `status` field: `deprecating: source → acquisition_channel by 2026-06-01`. Register consumer migrations.
   - **Phase 2 (major bump, 3.0.0):** after all registered consumers confirm migration and the deprecation date passes, remove `source`. Register new schema. The registry will require a manual compatibility override because removing a field that consumers still technically "can" read is BACKWARD-incompatible. This is the intended breaking-change path; override is logged.
   - Deploy producer. Old consumers that didn't migrate will break. At this point that is an escalation, not a surprise.

Total effort: two PRs, 30 days, coordinated migrations.

---

## Serialization format choice

Three practical options. Pick one per organization. Mixing them is technically possible, but you lose central tooling benefits.

| Format | Schema location | Evolution | Size | Tooling | Human-readable |
|--------|----------------|-----------|------|---------|----------------|
| **Avro** | Separate `.avsc` file; registry serves it at read | Strong (BACKWARD/FORWARD/FULL built in) | Compact binary | Excellent with Confluent registry; native Kafka fit | No (binary) |
| **Protobuf** | `.proto` file; registry or package-distributed | Strong, but trickier (`reserved` required for deleted fields to avoid accidental reuse) | Very compact binary | Excellent cross-language (gRPC ecosystem) | No (binary) |
| **JSON Schema** | JSON file; registry serves it | Weaker (additive-only compatibility is easy; other cases are fiddly) | Large (verbose JSON) | OK; less tightly integrated | Yes |

### When to pick which

- **Avro** — first choice for Kafka-centric platforms. Confluent Schema Registry's native format, richest evolution rules, smallest payload.
- **Protobuf** — first choice if you already have gRPC services and want the same schema language for RPC and events. Better cross-language story (generated types in every major language).
- **JSON Schema** — first choice only when the consumer ecosystem is JSON-native and heterogeneous (JavaScript clients, third parties, debugging with curl). Accept the evolution pain and the larger payloads.

### Mixed-format anti-pattern

Some teams end up with Avro on some topics, Protobuf on others, and JSON in the warehouse. Each format has different evolution semantics, different tooling, and different registry configurations. Rule: one format per organization for streaming events. Warehouse tables can be a separate world (SQL types are the schema there).

---

## Migration strategy when compatibility must break

Sometimes a rename is unavoidable, a type must change, or a PII field must be removed retroactively. Options:

### Option 1 — Dual-write / dual-read (preferred)

Phase 1: producer emits both old and new schema versions (to the same or different topics). Consumers migrate one by one from old to new. Phase 2: producer drops the old schema. This is the `source → acquisition_channel` pattern above. Longer, but safe.

### Option 2 — New topic, migration job

Create a new topic with the new schema. Run a migration job that reads the old topic and writes to the new one with transformation. Consumers cut over one by one. Old topic is decommissioned after all consumers have migrated. Best when the change is significant enough that a parallel topic is cleaner than dual-schema emission.

### Option 3 — Hard break (emergency only)

Producer registers the new incompatible schema with a manual compatibility override. All consumers break simultaneously. Use only for security incidents (must remove a PII field immediately) and declare an incident. Document the override in the registry audit log.

### PII retroactive removal

Special case. If a field was PII and must be scrubbed from the topic's retention window:
- Produce a compaction tombstone (if using a compacted topic) or rotate the topic entirely.
- Update the schema to remove the field (major version bump).
- Notify every consumer; most will need to handle the field's absence gracefully.
- Document under `data-governance-privacy` as a privacy incident.

---

## Registry operational hygiene

- **One schema subject per topic** (Confluent default: `<topic>-value`). Avoid shared subjects across topics — they make compatibility checks global in unintended ways.
- **Registry compatibility mode is set at subject level, not globally** — set it per topic. Default BACKWARD.
- **Registry URL in config, not code.** Dev, staging, prod registries are separate instances. A schema promoted to prod goes through a PR, not an automatic copy.
- **Schema reviews are code reviews.** Treat `.avsc` or `.proto` files as first-class code. Require approval from the contract owner.
- **Never delete a schema version.** Soft-delete (mark sunset) only. Consumers may still have it pinned.

---

## Quick checklist for a schema change

- [ ] Is it additive or breaking? If breaking, do you have a migration plan?
- [ ] Compatibility mode checked — will the registry accept the new schema?
- [ ] Version bump decided (major / minor / patch)?
- [ ] Consumer list reviewed from the contract file?
- [ ] If breaking, deprecation window started and communicated?
- [ ] PR includes the updated contract and the schema file?
- [ ] CI runs the registry's compatibility check before merge?
