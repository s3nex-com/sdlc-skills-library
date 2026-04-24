# Trade-off frameworks

Use these frameworks to structure technical trade-off decisions. For each decision, work through the relevant framework, document the analysis, and record the outcome in an ADR.

---

## Framework 1: CAP theorem

**When to apply:** Any time a system must store or replicate distributed state — databases, caches, distributed queues.

**The theorem:** In a distributed system subject to network partitions (P), you must choose between Consistency (C) and Availability (A). You cannot guarantee both simultaneously.

| Property | Definition | What you give up |
|----------|-----------|-----------------|
| **Consistency** | All nodes see the same data at the same time | Some requests will fail or block during partition |
| **Availability** | Every request receives a response (not necessarily current data) | Responses may contain stale data during partition |
| **Partition tolerance** | The system continues operating despite network partitions | Not negotiable in any distributed system |

**Decision guide:**

| Business requirement | Choose | Example systems |
|---------------------|--------|-----------------|
| Transactions must never see stale data (financial, inventory) | CP | PostgreSQL, HBase, Zookeeper |
| System must always respond (IoT ingestion, metrics collection) | AP | Cassandra, DynamoDB, CouchDB |
| Single-node (no replication) | CA | Not applicable to distributed systems |

**Questions to ask:**
1. What is the business cost of returning stale data?
2. What is the business cost of rejecting a request during a partition?
3. How often do network partitions occur in the target environment?
4. Is the system read-heavy or write-heavy?

---

## Framework 2: PACELC

**When to apply:** After determining C vs A preference (CAP), refine the trade-off for the normal (non-partition) case.

**The extension:** PACELC extends CAP: in the case of Partition (P), choose Availability (A) or Consistency (C). Else (E), in normal operation, choose Latency (L) or Consistency (C).

| System | Partition behaviour | Normal operation | Use case |
|--------|---------------------|------------------|---------|
| PA/EL | Available | Low latency | High-volume event ingestion, caches |
| PC/EC | Consistent | Consistent | Financial transactions, user accounts |
| PA/EC | Available | Consistent | Content delivery, IoT telemetry |

**Practical guidance:**
- Most web/API services: PA/EL (prioritise availability and speed; strong consistency is rarely needed)
- Payment and billing: PC/EC (correctness over speed)
- Telemetry and analytics ingestion: PA/EL (you can afford to lose a few events; you cannot afford to block ingestion)
- User profile reads: PA/EC (acceptable to serve slightly stale profiles; reads should be fast)

---

## Framework 3: Build vs buy

**When to apply:** When considering adopting a third-party library, SaaS product, or managed service vs building the capability in-house.

**Decision matrix:**

| Factor | Build | Buy |
|--------|-------|-----|
| Control over behaviour | Full | Limited to vendor's API |
| Time to first value | Slow | Fast |
| Ongoing maintenance cost | High (your team owns it) | Transferred to vendor |
| Customisation | Unlimited | Limited |
| Vendor dependency risk | None | Lock-in, price changes, discontinuation |
| Integration complexity | Depends | Usually lower initially |
| Expertise required | In-house expertise needed | Vendor provides documentation |

**Questions to ask:**
1. Is this a core competency of the business? (Build if yes — this is a competitive differentiator)
2. Does a good-enough solution exist that is within budget? (Buy if yes)
3. What is the switching cost if the vendor fails or becomes unsuitable?
4. What are the data privacy and compliance implications of sending data to a third party?
5. What is the total cost of ownership over 3 years (build: engineering time; buy: licence cost + integration time)?

**Signals to buy:** Commodity functionality (email sending, payment processing, maps), strong existing solutions, low strategic value, fast time-to-market needed.

**Signals to build:** Core competitive differentiator, unique requirements not served by existing solutions, strict data sovereignty requirements, unacceptable vendor lock-in risk.

---

## Framework 4: Synchronous vs asynchronous communication

**When to apply:** When designing communication between services — choosing between direct HTTP/gRPC calls and message broker-based communication.

| Property | Synchronous (HTTP/gRPC) | Asynchronous (Kafka/AMQP) |
|----------|------------------------|--------------------------|
| Simplicity | Higher — request/response is intuitive | Lower — event-driven thinking required |
| Coupling | Temporal coupling (caller blocked while waiting) | Decoupled — producer and consumer independent |
| Failure handling | Caller must handle downstream failures | Consumer retries independently |
| Latency | Lower for single request | Higher for first event; better throughput at scale |
| Ordering guarantees | Per-connection FIFO | Depends on broker (Kafka: per-partition) |
| Exactly-once semantics | Easier (retry + idempotent endpoint) | Harder (requires idempotent consumers) |
| Traceability | Easier (request ID propagation) | Requires trace context in message headers |
| Back pressure | Caller is naturally throttled by slowdowns | Producer can outpace consumer; requires monitoring |

**Choose synchronous when:**
- The caller genuinely needs the result before proceeding
- Strong consistency is required
- The operation is user-initiated and latency is critical
- The request/response pattern naturally fits (queries, writes with immediate confirmation)

**Choose asynchronous when:**
- The caller does not need to wait for the result
- High throughput is required (event ingestion, analytics pipelines)
- Services should be independently deployable and scalable
- Fan-out is needed (one event consumed by multiple services)
- The operation can tolerate eventual consistency

---

## Framework 5: Monolith vs microservices

**When to apply:** System design phase, or when evaluating whether to decompose an existing system.

| Factor | Monolith | Microservices |
|--------|----------|---------------|
| Operational complexity | Low | High (service mesh, distributed tracing, multiple deployments) |
| Development velocity (small team) | High | Lower (cross-service coordination overhead) |
| Independent scaling | Not possible | Per-service |
| Independent deployments | Not possible | Per-service |
| Cross-service transactions | Easy (shared DB) | Complex (Saga pattern required) |
| Team autonomy | Low | High (each team owns a service) |
| Fault isolation | Low (one bug can crash all features) | High (failure isolated to one service) |
| Technology diversity | Low | High (each service can use different stack) |
| Entry cost | Low | High |

**Choose monolith when:**
- Team size is small (< 8 engineers)
- Domain is not yet well-understood — premature decomposition is expensive
- Speed of iteration is more important than operational independence
- The system is not expected to scale components independently

**Choose microservices when:**
- Multiple independent teams must work autonomously
- Components have very different scaling requirements
- The domain is well-understood and bounded contexts are clear
- Independent deployment of components is a business requirement
- The team has operational maturity to manage distributed systems

**Start monolith, migrate later:** The Strangler Fig pattern allows gradual decomposition of a monolith into services as the domain becomes better understood and scale demands increase.

---

## Framework 6: Edge vs cloud processing

**When to apply:** Systems with IoT devices, edge compute nodes, or latency-sensitive processing that could be placed either at the edge or in the cloud.

| Factor | Edge processing | Cloud processing |
|--------|----------------|-----------------|
| Latency | Ultra-low (< 5ms) | Higher (network round-trip) |
| Bandwidth cost | Low (process locally, send summary) | High (send all raw data to cloud) |
| Operational complexity | High (distributed fleet management) | Low (centralised) |
| Offline operation | Possible | Not possible |
| Compute cost | Higher per-unit | Lower per-unit at scale |
| Data freshness | Real-time | Can be delayed by network |
| Security surface | Larger (physical device access) | Smaller (cloud controls) |
| Software updates | Complex (OTA update management) | Simple |

**Choose edge processing when:**
- Sub-10ms latency is required
- Bandwidth cost from raw data transmission is prohibitive
- Device must operate independently of network connectivity
- Local decisions must be made without cloud round-trip (safety-critical systems)

**Choose cloud processing when:**
- Latency requirements can be met with network round-trip
- Centralised ML/analytics are required across all device data
- Operational simplicity is valued
- Raw data must be retained for audit or ML training

**Hybrid pattern:** Process time-sensitive operations at the edge; aggregate and analyse at cloud. Send summaries and anomalies upstream, raw data on-demand only.
