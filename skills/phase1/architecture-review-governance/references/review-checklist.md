# Architecture review checklist

Work through all seven dimensions for every architecture review. Mark each item: ✅ Pass | ⚠️ Concern | ❌ Fail | N/A

---

## Dimension 1: Scalability

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 1.1 | Can the service scale horizontally (multiple instances) without code changes? | High | Stateless services scale; stateful services need explicit clustering design |
| 1.2 | Are there any shared in-process caches or local state that would break under horizontal scaling? | Critical | Session state, local file storage, in-memory queues |
| 1.3 | Are database queries bounded? (no unbounded SELECT * without LIMIT) | High | Unbounded queries degrade under load |
| 1.4 | Are there obvious N+1 query patterns in the data access layer? | High | N+1 queries are invisible at low volume, catastrophic at scale |
| 1.5 | Is the database connection pool sized appropriately for the expected concurrency? | High | Pool exhaustion is a common production failure mode |
| 1.6 | Are there any single-threaded or single-instance bottlenecks in the critical path? | High | Identify and quantify the throughput ceiling |
| 1.7 | Has a scaling ceiling been identified and documented? (what is the maximum load this design can handle?) | Medium | Must know when to scale before scaling becomes urgent |
| 1.8 | Are background jobs and batch operations isolated from the request-serving path? | Medium | CPU-intensive batch work steals capacity from request serving |

---

## Dimension 2: Security

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 2.1 | Is every endpoint authenticated unless explicitly designed to be public? | Critical | Unauthenticated endpoints require architecture review sign-off |
| 2.2 | Is authorisation enforced at the service layer, not just at the API gateway? | Critical | Gateway-only auth fails when internal services communicate directly |
| 2.3 | Is all inter-service communication encrypted (TLS)? | Critical | Includes internal cluster traffic |
| 2.4 | Are secrets (API keys, credentials, tokens) stored in the secrets manager, not in config files or code? | Critical | Any hardcoded or file-based secret is a Critical finding |
| 2.5 | Is all user input validated before processing? | Critical | SQL injection, command injection, path traversal |
| 2.6 | Are error responses sanitised? (no stack traces, database errors, or internal paths leaked to callers) | High | Error messages are a common information disclosure vector |
| 2.7 | Is a threat model available for this component? | High | Required for all internet-facing or data-storing components |
| 2.8 | Are privilege levels minimised? (least privilege for database users, IAM roles, service accounts) | High | Over-privileged service accounts amplify the impact of compromise |
| 2.9 | Is rate limiting configured for all public-facing endpoints? | High | Prevents abuse and protects downstream services |

---

## Dimension 3: Operability

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 3.1 | Does the service expose liveness and readiness health check endpoints? | High | Required for container orchestration and load balancer integration |
| 3.2 | Does the service emit structured JSON logs with the required fields (timestamp, severity, trace_id, service)? | High | Unstructured logs cannot be queried in production incidents |
| 3.3 | Does the service emit RED metrics (request rate, error rate, request duration)? | High | Without these metrics, SLOs cannot be measured |
| 3.4 | Does the service propagate distributed trace context? | Medium | Required for root cause analysis across service boundaries |
| 3.5 | Is there a runbook for deployment, rollback, and common failure scenarios? | High | Required before production deployment |
| 3.6 | Can the service be rolled back without data loss or downtime? | High | Database migrations must be backward compatible |
| 3.7 | Is configuration externalised (environment variables or config service)? No config changes should require redeployment | Medium | Configuration-driven behaviour changes require redeployment risk |
| 3.8 | Are database migrations idempotent and reversible? | High | Non-reversible migrations block rollback |

---

## Dimension 4: Maintainability

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 4.1 | Are service boundaries clearly defined and documented? (what does this service own and what does it not own?) | High | Unclear boundaries lead to gradual scope creep and coupling |
| 4.2 | Is the service's purpose cohesive? (does it do one thing well, or is it a general-purpose utility?) | Medium | Services that do many unrelated things are hard to change safely |
| 4.3 | Is the code structured so that tests can be written without complex setup? | Medium | Tightly coupled code is hard to test; hard-to-test code is poorly maintained |
| 4.4 | Are external dependencies abstracted behind interfaces? | Medium | Direct dependency on concrete implementations makes substitution hard |
| 4.5 | Is the data model normalised appropriately for the access patterns? | Medium | Over-normalised models for read-heavy workloads; under-normalised for write-heavy |
| 4.6 | Are there clear contracts between this service and its consumers? | High | Implicit contracts are discovered when they break |

---

## Dimension 5: Integration safety

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 5.1 | Are all outbound HTTP calls configured with explicit timeouts? | Critical | Calls without timeouts will block indefinitely if the remote service hangs |
| 5.2 | Is a circuit breaker implemented for dependencies that have shown instability? | High | Without circuit breakers, cascading failures are inevitable |
| 5.3 | Is retry logic implemented with exponential backoff and jitter? | High | Retry without backoff amplifies load on a struggling dependency |
| 5.4 | Does the service handle partial failures gracefully? (what happens if enrichment data is unavailable?) | High | Define and test degraded-mode behaviour |
| 5.5 | Are async message consumers idempotent? (safe to process the same message twice) | High | Message brokers guarantee at-least-once delivery; consumers must handle duplicates |
| 5.6 | Is dead-letter queue handling defined for messages that cannot be processed? | Medium | Without DLQ handling, failed messages are silently discarded |
| 5.7 | Are integration contracts tested with consumer-driven contract tests? | Medium | Pact or equivalent; validates both sides honour the contract |

---

## Dimension 6: Data integrity

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 6.1 | Is data ownership clearly assigned? (exactly one service writes to each data store) | Critical | Multiple writers with no coordination guarantee means data corruption |
| 6.2 | Is the consistency model defined and documented? (strong / eventual / causal) | High | The wrong consistency model for the business requirement leads to subtle bugs |
| 6.3 | Are database transactions used where atomicity is required? | High | Multiple writes without a transaction can leave data in inconsistent states |
| 6.4 | Is data retention policy defined? (how long is data kept, how is it deleted?) | Medium | Required for compliance and cost management |
| 6.5 | Is PII (personally identifiable information) identified and handled per the data classification policy? | Critical | Unclassified PII is a compliance risk |
| 6.6 | Are database indexes defined for the expected query patterns? | Medium | Missing indexes are the most common performance degradation under load |
| 6.7 | Is backup and restore tested? | High | A backup that has never been restored is untested |

---

## Dimension 7: Failure modes

| # | Check | Severity if fails | Notes |
|---|-------|-------------------|-------|
| 7.1 | Are failure modes documented for every external dependency? (what happens when it is slow? unavailable? returns errors?) | High | Undocumented failure modes are discovered in production |
| 7.2 | Is there a defined degraded-mode behaviour for each critical dependency failure? | High | "Return 500" is not a degraded-mode behaviour; it is a failure propagation |
| 7.3 | Has a blast radius analysis been done? (if this service fails, what other services are affected?) | High | Required for incident response planning |
| 7.4 | Are there resource limits configured? (CPU, memory, connection pool, thread pool) | High | Unbounded resource consumption causes cascading failures in shared environments |
| 7.5 | Is there a documented rollback strategy for each deployment? | High | Without a tested rollback, a failed deployment means downtime |
| 7.6 | Are cascading failure scenarios tested? | Medium | Chaos engineering or load testing with dependency failures injected |

---

## Review summary

**Total items:** 47
**Pass:** ___ | **Concern:** ___ | **Fail:** ___ | **N/A:** ___

**Critical findings:** ___
**High findings:** ___
**Overall recommendation:** Pass / Conditional pass / Fail
