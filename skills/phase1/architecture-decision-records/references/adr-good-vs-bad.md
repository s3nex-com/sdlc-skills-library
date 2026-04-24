# ADR good vs bad examples

Three pairs of ADRs showing the difference between well-written and poorly written records. For each pair: the bad version first with annotations, then the good version.

---

## Pair 1: Technology selection

### ❌ Bad ADR: Technology selection

**ADR-010: Database selection**
**Date:** 2024-03-10
**Status:** Accepted
**Owner:** Bob

**Context:**
We needed to pick a database.

**Decision:**
We will use PostgreSQL.

**Alternatives considered:**
- MongoDB: not chosen
- MySQL: not chosen

**Consequences:**
- We have a database now.

---

**Annotations — what makes this bad:**

1. **Context is useless** — "We needed to pick a database" tells a future reader nothing about WHY PostgreSQL was the right choice. What were the requirements? What was the system doing? What scale was involved?

2. **Alternatives are hollow** — "Not chosen" is not an analysis. A future engineer reading this cannot learn anything about why MongoDB or MySQL were rejected. This section could be worse than useless — it implies these were seriously considered when they might not have been.

3. **Consequences are meaningless** — "We have a database now" is not a consequence. Consequences should describe what becomes possible, what becomes constrained, what risks are introduced.

4. **Owner is a first name only** — "Bob" leaves future readers unable to contact the decision owner or understand their context.

5. **No review date** — When should this be revisited? If the scale changes? If a new team member questions it? Without a review date, the decision silently persists forever even as context changes.

---

### ✅ Good ADR: Technology selection

**ADR-010: Use PostgreSQL as the primary relational data store**
**Date:** 2024-03-10
**Status:** Accepted
**Owner:** Alice Chen, Lead Architect, Company A
**Review date:** Phase 2 planning — if sustained write throughput exceeds 50,000/second, evaluate sharding options

**Context:**
The platform requires a persistent store for device registry (device metadata, ownership, configuration), alert rule definitions, and user account data. These data sets are strongly relational: devices belong to organisations, alert rules apply to device types, users are assigned to organisations with specific roles. They also require strong consistency — a device's configuration must be the same regardless of which server handles the request. The team has significant PostgreSQL experience (both companies use it in production systems), and the Phase 1 data volume is well within PostgreSQL's single-node capability (estimated 50,000 devices, 500,000 alert rules). A prototype was built using MongoDB; it was abandoned after the schema flexibility introduced hard-to-debug inconsistency bugs in development and the eventual consistency model required complex application-level workarounds to achieve the consistency semantics required.

**Decision:**
Use PostgreSQL 15, managed via AWS RDS Multi-AZ in eu-west-1, as the primary data store for device registry, alert configurations, and user account data.

**Alternatives considered:**

| Alternative | Pros | Cons | Reason rejected |
|-------------|------|------|-----------------|
| **PostgreSQL 15 (chosen)** | ACID transactions, strong consistency, excellent query planning, team expertise, rich migration tooling | Horizontal write scaling requires sharding at high volume; RDS cost | Chosen |
| MongoDB | Document model, built-in horizontal scaling | Prototype revealed schema inconsistency issues; eventual consistency requires application complexity; less team expertise | Consistency problems in prototype |
| MySQL 8 | Mature, widely deployed | Fewer advanced features than PostgreSQL; less team expertise on both sides | PostgreSQL strictly preferred by both teams |
| CockroachDB | Globally distributed, horizontal scaling built in | Operational complexity and cost not justified at Phase 1 scale; no team expertise | Premature optimisation |

**Consequences:**

What becomes easier:
- ACID transactions for device configuration updates — no distributed transaction complexity
- Complex analytics queries using PostgreSQL CTEs and window functions
- Familiar tooling for both teams (psql, pgAdmin, Alembic, psycopg2)

What becomes harder:
- Horizontal write scaling if sustained writes exceed ~50,000/second — requires sharding or alternative data store
- All schema migrations must be backward compatible to support zero-downtime deployment (healthy constraint, but requires discipline)

New risks:
- Single-region RDS failure — mitigated by Multi-AZ deployment; automatic failover within ~60 seconds
- Cost growth at scale — mitigated by RDS cost alerts at 120% of baseline

Dependencies:
- RDS instance provisioned by Company A infrastructure team (target: M0 + 1 week)
- Both teams adopt Alembic for migration management
- Backup restore test completed before production cutover

---

## Pair 2: Architecture pattern choice

### ❌ Bad ADR: Architecture pattern

**ADR-015: Async processing**
**Date:** 2024-04-01
**Status:** Accepted
**Owner:** Dev team

**Context:**
We want to use async processing for some things.

**Decision:**
We will use Kafka for async stuff.

**Alternatives considered:**
- HTTP: slower
- RabbitMQ: also fine but we chose Kafka

**Consequences:**
- Faster processing
- More complexity

---

**Annotations — what makes this bad:**

1. **"Some things" is not a scope** — Which operations? Which services? What defines "async stuff"? This ADR cannot be applied consistently because no one knows when Kafka should be used vs not.

2. **"Slower" is not an analysis of HTTP** — HTTP is not inherently slower for all use cases. The real reason to choose Kafka over synchronous HTTP is decoupling and resilience, not raw speed.

3. **"Also fine but we chose Kafka" is not a reason** — Why was RabbitMQ not chosen? Message ordering? Replay capability? Scale? Operational familiarity? The reader cannot reproduce this decision or understand when it might need to be revisited.

4. **"More complexity" is too vague** — What kind of complexity? Consumer group management? Schema registry? Idempotency requirements? Future engineers need to know what they are taking on.

---

### ✅ Good ADR: Architecture pattern choice

**ADR-015: Use Kafka for inter-service event streaming; synchronous HTTP for query and command operations**
**Date:** 2024-04-01
**Status:** Accepted
**Owner:** Alice Chen, Lead Architect, Company A
**Review date:** When the number of event consumers exceeds 10, evaluate whether the schema registry approach needs revisiting

**Context:**
Several inter-service communication patterns are emerging in the system. The ingestion service must notify the processing pipeline when events arrive — a fire-and-forget pattern where the ingestion service cannot afford to wait for processing to complete. The alert evaluation service must broadcast alert state changes to the notification service and the audit service simultaneously. The query API must remain synchronous because callers need the result immediately. The system needs a clear policy so that both teams make consistent communication architecture decisions without case-by-case negotiation.

**Decision:**
Use Apache Kafka for all inter-service event streaming (fire-and-forget, fan-out, notifications, data propagation). Use synchronous HTTP/REST for all query operations and for write operations where the caller needs immediate confirmation.

**Alternatives considered:**

| Alternative | Pros | Cons | Reason rejected |
|-------------|------|------|-----------------|
| **Kafka + HTTP (chosen)** | Decoupled producers and consumers; high throughput; replay capability; fan-out to multiple consumers | Consumer group management complexity; idempotency must be implemented; schema evolution care | Chosen |
| HTTP only | Simpler mental model; easier debugging | Temporal coupling; each downstream consumer is a potential point of failure for the producer; no replay | Coupling is unacceptable for async use cases |
| RabbitMQ | Familiar to some engineers; AMQP is well-understood | No native message replay; partition-based scaling less mature than Kafka; no schema registry integration | Replay capability required for audit trail; Kafka already chosen as company standard |
| AWS SQS/SNS | Fully managed; no operational overhead | AWS lock-in; less control over retention; separate services for queue vs fan-out (SQS for queue, SNS for fan-out) | Vendor lock-in risk; architecture principle violation |

**Consequences:**

What becomes easier:
- Services can be deployed independently — producers don't know or care about consumers
- Fan-out to multiple consumers without changing the producer
- Event replay for debugging, auditing, and consumer backfill
- High-throughput ingestion without back-pressure on the producer

What becomes harder:
- Idempotency must be implemented in every consumer (Kafka guarantees at-least-once delivery)
- Dead-letter queue handling must be defined for every consumer
- Schema evolution must follow backward/forward compatibility rules
- Debugging across service boundaries requires distributed tracing with trace context in message headers

New risks:
- Schema incompatibility between producer and consumer after a schema change — mitigated by Schema Registry and contract testing
- Consumer lag accumulation during consumer downtime — mitigated by alerting on consumer group lag

Dependencies:
- Confluent Schema Registry provisioned and accessible to all services
- Trace context (W3C traceparent) propagated in all Kafka message headers
- Consumer lag alerting configured for all consumer groups before production

---

## Pair 3: Security approach

### ❌ Bad ADR: Security

**ADR-020: Authentication**
**Date:** 2024-04-10
**Status:** Accepted

**Context:**
We need to authenticate users.

**Decision:**
Use JWT tokens.

**Alternatives considered:**
- Sessions: old-fashioned
- API keys: less secure

**Consequences:**
- Users can log in.

---

**Annotations — what makes this bad:**

1. **No owner** — A security decision with no named owner is a liability. Who is accountable for this choice?

2. **"Old-fashioned" is not a technical reason** — Session-based authentication has legitimate use cases. Why is it wrong for THIS system? What about the architecture makes JWTs preferable?

3. **"Less secure" is wrong** — API keys are not inherently less secure than JWTs. API keys with proper rotation and revocation are appropriate for machine-to-machine authentication. This shows the decision maker did not understand the alternatives.

4. **JWT is not a complete decision** — What library? What algorithm (RS256 vs HS256)? What token lifetime? Who issues tokens? How are they revoked? What claims are required? This ADR leaves every implementation detail undefined.

5. **"Users can log in" is not a consequence** — What are the security implications? Token revocation challenges? Statelessness enabling horizontal scaling? Infrastructure required?

---

### ✅ Good ADR: Security approach

**ADR-020: Use OAuth 2.0 with JWT (RS256) for device API authentication; API keys for machine-to-machine integration**
**Date:** 2024-04-10
**Status:** Accepted
**Owner:** Sarah Park, Security Lead, Company A
**Review date:** If user base exceeds 10,000 or machine-to-machine integrations exceed 50; also review after any security incident involving authentication

**Context:**
The platform serves two distinct authentication scenarios: (1) human users accessing the management API through a web dashboard — these need role-based access control, session management, and MFA; (2) partner systems and devices accessing the ingestion and query APIs programmatically — these need stable, long-lived credentials that can be scoped to specific operations. The security team requires that all authentication be auditable, revocable, and that credentials never be stored in plaintext. The platform will be deployed on Kubernetes; token verification must work across all pods without shared state.

**Decision:**
Use OAuth 2.0 with JWT tokens (RS256-signed) for human user authentication, issued by our internal identity provider (Keycloak). Use long-lived API keys (stored hashed in the database, never as plaintext) scoped to specific resources for machine-to-machine and device authentication.

**Alternatives considered:**

| Alternative | Pros | Cons | Reason rejected |
|-------------|------|------|-----------------|
| **OAuth 2.0 + JWT (RS256) for human; API keys for M2M (chosen)** | Stateless JWT verification scales horizontally; industry standard; Keycloak provides OIDC, MFA, audit logs; API keys simple for M2M | JWT revocation requires token blacklist or short expiry; API key rotation requires client coordination | Chosen |
| Session-based authentication | Easy to revoke (delete session); well-understood | Requires shared session store (Redis) across all pods — added operational dependency; doesn't work well for stateless API clients | Shared session store adds operational complexity and a single point of failure |
| mTLS for all clients | Strongest authentication; no token expiry | Client certificate management is complex for devices and partners; requires PKI infrastructure we don't have | Operational complexity is prohibitive for Phase 1 |
| AWS Cognito | Managed, no Keycloak ops | AWS lock-in; limited customisation; data residency concerns for EU customers | Vendor lock-in; data residency requirements |

**Consequences:**

What becomes easier:
- Horizontal scaling without shared authentication state (JWT is self-contained)
- Granular authorisation using JWT claims (role, organisation, permitted scopes)
- Audit trail via Keycloak's built-in audit logs for human authentication
- M2M authentication without Keycloak dependency (API key verified against database)

What becomes harder:
- JWT revocation — a compromised JWT is valid until expiry (mitigated by 15-minute access token lifetime + refresh token rotation)
- API key rotation requires coordination with partner teams — establish a rotation process before launch
- RS256 key rotation requires coordinated update across all services (keys served via JWKS endpoint)

New risks:
- Keycloak availability becomes a hard dependency for human login — mitigated by Keycloak HA deployment (2 replicas)
- JWT algorithm confusion attack (RS256 vs HS256) — mitigated by explicitly validating algorithm in token verification code; forbid HS256

Dependencies:
- Keycloak provisioned with HA configuration by Company A (target: M1)
- JWKS endpoint accessible to all services for JWT verification
- API key hashing standard (bcrypt) documented and enforced in code review
