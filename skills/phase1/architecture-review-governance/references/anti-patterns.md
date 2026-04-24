# Architecture anti-patterns catalogue

Each entry covers: what the pattern is, why it is dangerous, how to detect it, and how to remediate it.

---

## 1. Distributed monolith

**Description:** A system deployed as multiple services but tightly coupled at the data or synchronous-call level, such that services cannot be deployed, scaled, or failed independently. The worst of both worlds: the operational complexity of microservices with none of their benefits.

**Why it is dangerous:** Changes to one service require coordinated changes to others. A single service failure cascades across the entire system. Scaling one service requires scaling all services together. Deployment requires coordination across all teams.

**How to detect it:**
- Multiple services share a single database or schema
- Services cannot start or function without other specific services being available
- Deployments require coordinating multiple services simultaneously
- A change to one service's internal data model requires changes to other services

**Remediation:** Define clear service boundaries with each service owning its data. Replace direct database access with API calls. Introduce event-driven patterns to break synchronous coupling. This is a long-term refactoring effort — treat it as high-priority technical debt.

---

## 2. Shared database across services

**Description:** Multiple services read from and write to the same database tables, sharing schema ownership.

**Why it is dangerous:** Schema changes in the database break multiple services simultaneously. There is no way to evolve one service's data model without coordinating all consumers. Authorisation at the service layer is bypassed — any service can read any data. It is impossible to understand the blast radius of a database change.

**How to detect it:**
- Multiple services listed in the database connection configuration
- Database tables with columns clearly "owned" by different services (e.g., `orders.shipping_status` updated by the shipping service, but `orders` is the orders service's table)
- A service that queries tables it does not own

**Remediation:** Assign each table to exactly one owning service. Migrate cross-service data access to API calls or event consumption. This is a Critical finding — do not proceed with development until the data ownership model is resolved.

---

## 3. Synchronous call chains

**Description:** Service A calls Service B synchronously, which calls Service C synchronously, which calls Service D. The entire chain must be available for any request to succeed.

**Why it is dangerous:** Latency adds up — a 100ms response from each service creates 400ms total latency in a 4-deep chain. A single service failure at any depth causes the entire chain to fail. As the chain grows, the failure probability approaches 1. This pattern makes the system's availability the product of all service availabilities, not their minimum.

**How to detect it:**
- Tracing shows requests spanning 3 or more services synchronously
- Services in the chain have similar response time SLOs but the system SLO is much higher
- A single slow database query in one service causes widespread latency degradation

**Remediation:** Break the chain with async processing where immediacy is not required. Cache data at the call boundary. Consider whether multiple synchronous calls can be collapsed into a single call to an orchestrating service. For each synchronous call in the chain, validate that the caller genuinely cannot proceed without the response.

---

## 4. Missing circuit breakers

**Description:** Services make outbound calls to dependencies without circuit breakers, causing requests to block and accumulate when dependencies are slow or unavailable.

**Why it is dangerous:** Without a circuit breaker, a slow dependency causes the caller's thread pool (or async queue) to fill with pending requests. This eventually exhausts the caller's resources, causing it to fail too — cascading the failure upward. A single slow downstream service can bring down the entire system.

**How to detect it:**
- No circuit breaker library in the service's dependencies
- Load tests show that slowing a single downstream service causes the caller to stop responding entirely
- Incident history shows cascading failures from a single service outage

**Remediation:** Implement circuit breakers (Resilience4j, Hystrix, or built-in patterns in the service framework) for all outbound calls to services that have shown instability. Configure: failure rate threshold (when to open), wait duration (how long to stay open), and half-open probing.

---

## 5. God service

**Description:** A single service that owns far too many responsibilities — multiple unrelated domains, business functions, and data entities — because it started as a monolith and was never decomposed.

**Why it is dangerous:** Any change to the god service is high-risk because changes in one business domain can unintentionally affect others. The service is impossible to test comprehensively. It becomes a deployment bottleneck — all teams must coordinate changes through a single service. It also tends to accumulate technical debt faster than it can be addressed.

**How to detect it:**
- A service with 50+ endpoints across unrelated business domains
- A service that owns more than 3-4 unrelated database tables
- A service that multiple teams all need to change simultaneously
- A service where changes always require "a full regression test of the whole system"

**Remediation:** Identify bounded contexts within the service and extract them progressively into separate services. Use the Strangler Fig pattern to migrate domain by domain. This is a long-term effort — prioritise the highest-change-frequency domains first.

---

## 6. Chatty services

**Description:** Services that make many small, fine-grained API calls to accomplish a single business operation, generating excessive network traffic and inter-service latency.

**Why it is dangerous:** Network calls are orders of magnitude slower than in-process function calls. A service that makes 20 API calls to assemble a response will have 20× the latency exposure of a service that makes 1 call. It also generates load on the downstream services and the network fabric.

**How to detect it:**
- Traces show a single user-visible request generating 15+ inter-service calls
- API endpoints that return a single entity field (e.g., GET /users/{id}/email instead of returning the full user)
- High API call volume not correlated with user traffic growth

**Remediation:** Introduce aggregation endpoints that return composite responses. Use the Backend for Frontend (BFF) pattern. Consider whether some cross-service data should be cached locally or replicated via events.

---

## 7. No saga pattern for distributed transactions

**Description:** A business operation that spans multiple services requires atomic consistency, but is implemented using sequential service calls without compensation logic for partial failures.

**Why it is dangerous:** When step 3 of a 5-step cross-service operation fails, steps 1 and 2 have already committed. Without compensation logic, the system is left in an inconsistent state with no automatic recovery path. This is a data integrity failure mode.

**How to detect it:**
- Business operations that require writes to multiple services' databases
- No compensation or rollback logic for cross-service write failures
- Incident history showing inconsistent data states after failed operations

**Remediation:** Implement the Saga pattern. For choreography-based sagas: each service publishes events that trigger the next step; failure events trigger compensating transactions. For orchestration-based sagas: a saga orchestrator manages the workflow and drives compensations on failure.

---

## 8. Configuration in code

**Description:** Configuration values — environment-specific settings, feature flags, connection strings, thresholds — are hardcoded in the application code rather than externalised.

**Why it is dangerous:** Configuration changes require code changes, which require code review, CI/CD pipeline runs, and deployment. A configuration change to fix a production issue takes hours instead of minutes. It also makes the code environment-aware in a way that introduces subtle bugs ("works in development, fails in production").

**How to detect it:**
- Strings like "https://api.production.example.com" hardcoded in source files
- `if environment == "production"` branches throughout the code
- Feature flags implemented as code constants

**Remediation:** Externalise all configuration to environment variables, a configuration service, or a secrets manager. The code should be environment-agnostic — the environment is injected at runtime, not baked in at build time.

---

## 9. Synchronous coupling to slow operations

**Description:** A user-facing request path performs slow operations synchronously — sending email, generating PDFs, calling slow third-party APIs, resizing images — blocking the response until the slow operation completes.

**Why it is dangerous:** Slow operations in the request path increase latency for all users. They also create unpredictable response times, as the slow operation's latency varies. Under load, the queue of waiting requests can grow faster than it is drained, eventually exhausting connection pools or thread pools.

**How to detect it:**
- Response time SLO is regularly breached when a specific third-party service is slow
- Services in the critical path call email/SMS/notification services synchronously
- CPU-intensive operations (PDF generation, image processing) in the HTTP request handler

**Remediation:** Move slow operations out of the request path using message queues. Return an accepted (202) response immediately and process the slow operation asynchronously. Use webhooks or polling to notify the caller when the operation is complete.

---

## 10. Missing idempotency in consumers

**Description:** Message consumers or webhook handlers process each message exactly once without idempotency guarantees, causing duplicate side effects when messages are redelivered.

**Why it is dangerous:** All message brokers (Kafka, RabbitMQ, SQS) guarantee at-least-once delivery — they do not guarantee exactly-once. Network failures, consumer crashes, and rebalancing all cause message redelivery. A non-idempotent consumer will create duplicate database rows, send duplicate emails, process duplicate payments, or otherwise corrupt state.

**How to detect it:**
- Consumer code that does not check whether it has already processed a given message ID
- Database tables with no unique constraints on event IDs or message IDs
- User reports of duplicate emails or duplicate transactions

**Remediation:** Implement idempotency at the consumer level: store a record of processed message IDs (in a database or cache with TTL), and skip processing if the message has already been seen. Use database unique constraints as a safety net.

---

## 11. Large payloads in message queues

**Description:** Events published to a message broker include large binary payloads (images, documents, large JSON blobs) rather than references to the data.

**Why it is dangerous:** Message brokers are optimised for high-volume small messages, not for storing large payloads. Large messages reduce throughput, increase broker storage costs, slow down consumers, and can exceed message size limits (Kafka default: 1MB). They also make message replay expensive.

**How to detect it:**
- Events in the queue with payloads > 100KB
- Consumers that process large binary data inline
- Broker storage growing faster than event volume

**Remediation:** Use the Claim Check pattern: store large payloads in object storage (S3, GCS) and publish only a reference (URL or object key) in the message. Consumers retrieve the payload from object storage when needed.

---

## 12. No graceful shutdown

**Description:** Services are terminated abruptly (SIGKILL) without implementing graceful shutdown, causing in-flight requests to be dropped and partial database transactions to be left uncommitted.

**Why it is dangerous:** During deployments and autoscaling scale-down events, services are terminated. If the service does not handle SIGTERM gracefully — finishing in-flight requests, committing or rolling back pending transactions, flushing message batches — data is lost or corrupted on every deployment.

**How to detect it:**
- Service code that does not handle SIGTERM
- Error rate spike during every deployment
- Partial transaction records in the database after a deployment

**Remediation:** Implement a SIGTERM handler that: (1) stops accepting new requests (signals readiness probe to fail so the load balancer removes the instance), (2) waits for in-flight requests to complete with a configurable timeout, (3) flushes any pending writes or message batches, (4) closes database connections cleanly, (5) exits.
