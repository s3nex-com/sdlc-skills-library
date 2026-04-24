# Data contracts

A data contract is the API contract of the data world. A producer publishes a dataset or a topic and commits to a schema, a freshness SLA, a uniqueness key, ordering guarantees (if any), and a compatibility policy. Consumers register their expectations: which fields they read, what staleness they tolerate, what they do when the producer breaks. Without this, every schema change is a production incident waiting for a scheduled run.

Treat data contracts exactly like API contracts: versioned, reviewed in the design stage, enforced in CI, and broken only with a migration plan.

---

## Shape of a data contract

Every contract has five required parts. Missing any one turns it into a wish.

### 1. Identity

- `name` — fully qualified dataset or topic name (e.g. `events.user_signup`, `warehouse.dim_customer`).
- `owner` — team or individual responsible. Not an email list. A person who owns the rollback.
- `version` — semver. `major.minor.patch`. Major = breaking schema change. Minor = additive field. Patch = docs or SLA tightening.
- `status` — `draft` / `active` / `deprecated` / `sunset`.

### 2. Schema

Machine-readable, versioned alongside code. Avro, Protobuf, or JSON Schema are the three real choices (see `schema-registry-design.md`). Pick one per organization and stick with it. Mixing formats turns your registry into a junk drawer.

Schema must include:
- Field name, type, required/optional.
- Semantic description per field (one sentence).
- PII classification per field (`pii: true|false`, with subcategory if true).
- Default value where applicable.

### 3. Producer spec (guarantees)

What the producer commits to:

- **Freshness SLA** — "99% of events emitted within 5 minutes of the underlying event occurring."
- **Uniqueness key** — which fields form the natural primary key. Dedup window if events can arrive twice.
- **Ordering guarantee** — per-key ordered / globally ordered / unordered. Be explicit. Unordered is fine if stated.
- **Completeness** — "signup_timestamp is never null for rows where status = 'completed'."
- **Retention** — how long the producer keeps the data in the source-of-truth store. After that, it's gone.
- **Compatibility mode** — `BACKWARD` (default), `FORWARD`, `FULL`, or `NONE`. See `schema-registry-design.md`.

### 4. Consumer spec (expectations)

What consumers need:

- **Required fields** — the subset of the schema this consumer actually reads.
- **Tolerated staleness** — "data up to 10 minutes old is fine; beyond that trigger an alert."
- **Breakage notification window** — "notify 30 days before a breaking change."
- **Downstream impact** — what this consumer produces if the contract breaks (a dashboard? a model? a billing run?).

Consumers register against the contract. The producer cannot ship a breaking change without seeing the consumer list.

### 5. Evolution policy

- **Additive changes** — allowed any time, bump minor version.
- **Breaking changes** — require a deprecation window (default: 30 days for internal, 90 days for external), a migration guide, and explicit sign-off from every registered consumer.
- **Emergency breakage** — allowed only for security (PII field must be removed from all events retroactively). Documented as an incident.

---

## Tooling

Three real options, each with a different philosophy:

| Tool | Scope | Strength | Weakness |
|------|-------|----------|----------|
| Kafka Schema Registry (Confluent) | Streaming topics | Battle-tested, enforces compatibility on the write path | Only covers Avro/Protobuf/JSON over Kafka; doesn't know about freshness SLAs |
| dbt contracts | Warehouse models | Enforced at `dbt build`; contracts live next to the model code | Only covers warehouse tables; no producer/consumer registration |
| Gable | Contract management across the stack | Unifies contracts across Kafka, warehouse, and services; consumer registration first-class | External service; adds a vendor |

For a 3-5 person team: start with Kafka Schema Registry for events and dbt contracts for warehouse models. Add Gable (or a similar contract platform) only when the number of producers or consumers makes ad-hoc coordination break down.

---

## Versioning rules

Semver applied to schema:

- **MAJOR** (2.0.0 → 3.0.0): removed a field, changed a type, renamed a field, changed a required field to a more restrictive type. Requires deprecation window and consumer sign-off.
- **MINOR** (2.0.0 → 2.1.0): added an optional field, relaxed a constraint (string length increase), added an enum value where consumers are tolerant.
- **PATCH** (2.0.0 → 2.0.1): documentation only, SLA tightening (not loosening), non-behavioural metadata.

Consumers pin to a major version. Minor/patch upgrades are transparent.

---

## Worked example — `events.user_signup`

A Kafka topic emitting one event per completed user signup. Consumed by the warehouse `dim_user` load, the growth analytics dashboard, and the welcome-email service.

### Contract file (`contracts/events.user_signup.yaml`)

```yaml
name: events.user_signup
owner: platform-team (on-call: @signup-owner)
version: 2.1.0
status: active
format: avro
topic: user-signup-v2
compatibility: BACKWARD

schema:
  type: record
  name: UserSignup
  fields:
    - name: user_id
      type: string
      doc: Stable internal user identifier (ULID).
      pii: false
    - name: email
      type: string
      doc: User email at time of signup.
      pii: true
      pii_subcategory: contact
    - name: signup_timestamp
      type: { type: long, logicalType: timestamp-millis }
      doc: UTC epoch millis when the user completed signup.
      pii: false
    - name: source
      type: { type: enum, symbols: [organic, referral, paid, partner] }
      doc: Acquisition source at time of signup.
      pii: false
    - name: country_code
      type: [null, string]
      default: null
      doc: ISO-3166-1 alpha-2 country code derived from IP. Null if lookup failed.
      pii: false
    - name: referrer_user_id
      type: [null, string]
      default: null
      doc: If source=referral, the user_id of the referring user.
      pii: false

producer:
  freshness_sla: "p99 emitted within 60 seconds of signup completion"
  uniqueness_key: [user_id]
  dedup_window: "24h (duplicate user_id within 24h is treated as a replay and dropped downstream)"
  ordering: "per user_id ordered (keyed by user_id); no global order"
  completeness:
    - "signup_timestamp is never null"
    - "source is never null"
    - "country_code may be null (documented above)"
  retention: "7 days on the topic; source-of-truth in users table indefinitely"

consumers:
  - name: warehouse.dim_user_load
    owner: data-team
    reads: [user_id, email, signup_timestamp, source, country_code]
    tolerated_staleness: "15 minutes"
    breakage_window: "30 days"
    downstream: "dim_user table; feeds all marketing and finance reporting"
  - name: growth.signup_dashboard
    owner: growth-team
    reads: [user_id, signup_timestamp, source, country_code, referrer_user_id]
    tolerated_staleness: "5 minutes"
    breakage_window: "30 days"
    downstream: "Looker daily signup dashboard"
  - name: comms.welcome_email_service
    owner: growth-team
    reads: [user_id, email, signup_timestamp, source]
    tolerated_staleness: "2 minutes"
    breakage_window: "30 days"
    downstream: "welcome email sent within 10 minutes of signup"

evolution_policy:
  additive: "allowed any time; bump minor version; notify consumers on next weekly sync"
  breaking: "30-day deprecation window; consumer sign-off required from every registered consumer; migration guide in the PR"
  emergency: "security-only (PII field removal); requires incident declaration"
```

### How this is enforced

- **On the producer side:** the service serializes with the Avro schema pulled from Schema Registry. Registry is set to `BACKWARD` compatibility — if the producer tries to register a schema that breaks consumers, the publish fails in CI.
- **On the consumer side:** each registered consumer has a CI check that pulls the current producer schema and asserts the consumer's expected fields are present with compatible types. If the producer removes a field the consumer reads, the consumer CI goes red before the producer can merge.
- **Freshness SLA:** monitored via `observability-sre-practice`. Alert fires when p99 emission lag exceeds 60s for 5 consecutive minutes.
- **Quality tests:** uniqueness on `user_id` within the dedup window, completeness on `signup_timestamp` and `source`. Run in the pipeline and in CI against a sample.
- **Evolution:** a breaking change triggers a contract PR. All three consumers get a review request. After 30 days, if a consumer has not responded, the change is escalated to the owning team's lead, not auto-approved.

---

## Anti-patterns

- **Schema in a wiki page.** Not enforceable. Goes stale. Never do this.
- **"The schema is whatever the producer emits today."** That is the definition of no contract.
- **One giant shared schema for every event type.** Turns every additive change into a global coordination exercise.
- **No consumer list.** If you cannot name who depends on the data, you have no idea what you can change.
- **Deprecation window shorter than the consumer's release cadence.** If a consumer ships monthly and you give 14 days, they cannot migrate in time.

---

## Quick checklist before shipping a new dataset or topic

- [ ] Contract file committed alongside the producer code.
- [ ] Schema in the registry (Kafka Schema Registry, dbt contracts, or equivalent).
- [ ] Compatibility mode set (default: BACKWARD).
- [ ] Freshness SLA, uniqueness key, ordering, completeness all stated.
- [ ] At least one consumer registered, or explicit note that no consumer exists yet (and therefore this contract's status stays `draft` until one does).
- [ ] Evolution policy copied from the standard template; deviations justified.
- [ ] Data quality tests wired to the producer CI and the scheduled pipeline.
- [ ] Contract referenced in the design doc.
