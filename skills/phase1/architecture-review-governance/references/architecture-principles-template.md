# Architecture principles template

## How to use this template

Architecture principles are the non-negotiables — constraints and values that every architectural decision must respect. They are not preferences or guidelines; they are commitments. When a proposed design violates a principle, the design must change, not the principle (unless the principle itself is updated through a formal ADR).

Write each principle with its rationale. A principle without a "why" will be ignored or misapplied under pressure. The rationale is what helps engineers make correct decisions in situations the principle authors did not anticipate.

---

## Principle 1: Design for failure

**Statement:** Every component must assume that all of its dependencies — internal services, external APIs, databases, message brokers — can and will fail at any time.

**Rationale:** Distributed systems fail in partial and unpredictable ways. A component that assumes its dependencies are always available will propagate failures rather than contain them. When a downstream service times out, the caller must handle that gracefully — not wait indefinitely or crash.

**How to apply:**
- All outbound network calls must have explicit timeouts configured
- Services must implement circuit breakers for dependencies that have shown instability
- Degraded-mode behaviour must be defined for every critical dependency failure: fail fast, serve stale data, queue for retry, or return a meaningful error
- Load tests must include dependency failure scenarios

**Examples of violation:**
- An HTTP client with no timeout (will hang indefinitely if the server stops responding)
- A service that returns 500 when a non-critical enrichment service is unavailable, instead of returning the core data without the enrichment
- A database connection pool with no overflow handling (will block all requests when connections are exhausted)

---

## Principle 2: Each service owns its data

**Statement:** No service may read from or write to another service's database directly. All data access across service boundaries must go through the owning service's API.

**Rationale:** Direct cross-service database access creates invisible coupling. When Service A queries Service B's database directly, changes to B's schema break A without any API contract violation being detectable. This pattern also makes it impossible to reason about data consistency, audit data access, or enforce authorisation at the service boundary.

**How to apply:**
- Each service has its own database instance or schema that no other service accesses directly
- Data needed by multiple services is exposed via API endpoints, not shared tables
- Event-driven patterns (publishing events to Kafka) are acceptable for broadcast data — consuming services maintain their own read models
- Read replicas for analytics are acceptable if they are read-only and the consuming service accepts eventual consistency

**Examples of violation:**
- Service A joining its own tables with tables owned by Service B in a single SQL query
- A shared `users` table written to by three different services
- A batch job that reads from the production database of a microservice to generate reports

---

## Principle 3: Observability is not optional

**Statement:** Every service must emit structured logs, metrics, and distributed traces from the first day of operation. Observability cannot be added retroactively.

**Rationale:** A system you cannot observe is a system you cannot operate. Problems found in production without observability are diagnosed by guesswork and often take 10× longer to resolve. In a cross-company context, observability is also a trust mechanism — it provides objective evidence of system behaviour that both companies can reference.

**How to apply:**
- All services must emit JSON-structured logs with the required fields defined in the log standards
- All services must instrument RED metrics (Rate, Errors, Duration) using the OpenTelemetry SDK
- All services must propagate trace context across all inter-service calls
- Observability instrumentation is reviewed as part of every code review
- A service without observability instrumentation fails the pre-release security and quality gate

**Examples of violation:**
- A service that logs unstructured text strings instead of JSON
- An HTTP endpoint that does not record request duration as a histogram
- An async worker that processes messages without emitting processing time or error count metrics
- A service that does not propagate the `traceparent` header to downstream calls

---

## Principle 4: Contracts are the truth

**Statement:** The API contract (OpenAPI spec, Protobuf schema, AsyncAPI spec) is the source of truth for an interface. Implementation must conform to the contract, not the other way around.

**Rationale:** In a cross-company context, both teams build against the same contracts. If one team's implementation deviates from the contract, the other team's implementation breaks — often silently, and often discovered late. The contract also provides a legally defensible record of what was agreed.

**How to apply:**
- No code is written for an interface until its contract is reviewed and frozen
- All contracts are stored in version control
- Contract compliance is enforced by automated contract tests in CI/CD
- Breaking contract changes require a formal change request and both-company sign-off
- Implementation bugs are fixed by changing the code, not by changing the contract (unless the contract was wrong, which requires a formal change process)

**Examples of violation:**
- Adding a required field to a response without updating the OpenAPI spec
- Implementing a 201 response where the contract specifies 200
- Changing an endpoint path in code without updating the spec

---

## Principle 5: Prefer async over sync for non-critical paths

**Statement:** For operations that do not require an immediate response, prefer event-driven asynchronous patterns over synchronous request/response. Reserve synchronous calls for operations where the caller genuinely cannot proceed without the response.

**Rationale:** Synchronous call chains couple services temporally — if any service in the chain is slow or unavailable, all callers are blocked. Async patterns break this coupling: the publisher can continue operating even if the consumer is temporarily unavailable, and the consumer can process at its own pace. This improves resilience, scalability, and throughput.

**How to apply:**
- Classify every inter-service operation as: (a) requires immediate response, or (b) fire-and-forget / eventual consistency acceptable
- For category (b), use the message broker (Kafka) instead of synchronous HTTP
- Publish-subscribe patterns are preferred for notifications and data propagation
- Synchronous HTTP is appropriate for: query operations where the caller needs the result immediately, and write operations where strong consistency is required

**Examples of violation:**
- Sending email notifications via a synchronous HTTP call to a notification service from the critical request path
- Auditing events via synchronous writes to an audit service, adding latency to every request
- Triggering downstream processing synchronously when the caller does not need to know the result

---

## Principle 6: Security is structural, not bolted on

**Statement:** Authentication, authorisation, encryption in transit, and secrets management are designed into every component from the start. They are not added after the feature works.

**Rationale:** Security added retroactively is always weaker than security designed in. It is also significantly more expensive — refactoring authentication into an existing service is orders of magnitude harder than designing it correctly the first time. In a cross-company context, a security failure creates legal liability for both companies.

**How to apply:**
- Every endpoint is authenticated unless explicitly designed to be public (requires architecture review sign-off)
- Authorisation is enforced at the service layer, not only at the API gateway
- All inter-service communication uses TLS, including internal traffic within the cluster
- Secrets are stored in the designated secrets manager; never in code, config files, or environment variables defined in version control
- Security is reviewed as part of every architecture review and code review

**Examples of violation:**
- An internal endpoint that is unauthenticated "because it's not exposed externally" — internal network compromise bypasses this
- A service that fetches authorisation rules from another service on every request without caching, creating a centralised choke point
- Database credentials stored in a `.env` file committed to a private repository

---

## Principle 7: Optimise for operability, not just correctness

**Statement:** A system that works correctly but cannot be operated, diagnosed, or changed safely is not production-ready. Every design decision must consider the operational burden it creates.

**Rationale:** Features are written once but operated continuously. The engineering cost of a feature is dominated by its operational lifetime, not its initial development. Complex configurations, opaque failure modes, and difficult deployment procedures compound over time and eventually dominate engineering capacity.

**How to apply:**
- Every service must have a runbook covering deployment, rollback, scaling, common failure diagnosis, and key configuration parameters
- Configuration changes must not require redeployment (use environment variables or configuration services)
- Database migrations must be backward compatible with the previous release (to enable zero-downtime deployment)
- Services must expose health check endpoints that distinguish between liveness (is the process alive?) and readiness (is the service ready to accept traffic?)

**Examples of violation:**
- A service where changing a feature flag requires a code change and deployment
- A database migration that renames a column, breaking the previous release
- A service with a single `/health` endpoint that returns 200 regardless of whether downstream dependencies are healthy

---

## Principle 8: Explicit is better than implicit

**Statement:** Make behaviour, configuration, and dependencies visible and explicit. Avoid magic — configuration by convention, implicit defaults, and hidden side effects that are not visible in the code or documentation.

**Rationale:** Implicit behaviour is fine until something goes wrong. When debugging a production incident at 2am, implicit defaults and hidden side effects are the hardest things to discover. In a cross-company context, engineers from two organisations are reading each other's code — implicit patterns that are obvious to one team may be entirely opaque to the other.

**How to apply:**
- Configuration values must have explicit defaults documented in code and runbooks; never rely on framework magic
- Dependency injection over service locator patterns — dependencies are visible at the call site
- Error conditions are returned explicitly, not swallowed
- Data transformations are documented; silent type coercion is forbidden
- Cross-service contracts are documented in the API spec, not inferred from behaviour

**Examples of violation:**
- A service that silently retries failed operations with no logging, making retry storms invisible
- A framework that automatically connects to a database using conventions not documented anywhere
- A function that swallows exceptions and returns a zero value, making callers believe the operation succeeded

---

## Principles summary

| # | Principle | Key test question |
|---|-----------|------------------|
| 1 | Design for failure | What happens when each dependency fails? |
| 2 | Each service owns its data | Does any service access another service's database directly? |
| 3 | Observability is not optional | Can you diagnose a production issue without adding new instrumentation? |
| 4 | Contracts are the truth | Is the API contract the single source of truth, enforced by tests? |
| 5 | Prefer async for non-critical paths | Is this synchronous call on the critical path? Could it be async? |
| 6 | Security is structural | Was security designed in, or added after the feature was working? |
| 7 | Optimise for operability | Can this be deployed, rolled back, and diagnosed at 2am? |
| 8 | Explicit is better than implicit | Is every significant behaviour visible and documented? |

**Last reviewed:** [date]
**Approved by:** [Lead Architect, Company A] | [Tech Lead, Company B]
