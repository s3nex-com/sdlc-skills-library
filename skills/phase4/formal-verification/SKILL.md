---
name: formal-verification
description: >
  Activate when designing a custom distributed protocol that must be provably correct —
  consensus algorithms, leader election, two-phase commit, idempotency guarantees,
  exactly-once delivery, or any concurrent protocol where an incorrect interleaving
  causes data loss or corruption. Use TLA+ to specify and model-check the protocol
  before writing a line of implementation code.
---

# Formal verification (TLA+)

## Purpose

Some distributed protocols cannot be adequately tested — the state space is too large, the problematic interleavings too rare, and the consequences of a bug (data loss, silent corruption) too severe. TLA+ is a formal specification language that lets you describe the protocol as a state machine, declare safety and liveness properties, and have the TLC model checker exhaustively explore all reachable states across all thread interleavings. If TLC finds a violation, it produces a concrete execution trace — a step-by-step path to the failure — which is far more useful than "it blew up in production after 3 weeks." This skill covers when to apply TLA+, how to write a specification, and what to do with the output.

---

## When to use

- You are designing a **custom distributed protocol**: consensus, leader election, two-phase commit, saga orchestration, exactly-once delivery, distributed locks
- The protocol involves **concurrent actors and shared state** — correctness depends on the ordering of operations
- An incorrect implementation causes **data loss, silent duplication, or corruption** — not just an error response
- **Conventional testing cannot cover the state space** — the number of possible orderings is too large to enumerate in tests
- You are about to implement something and want to know: "Is this design even correct before I write the code?"

---

## When NOT to use

- **Standard CRUD services** with well-understood consistency models — ACID databases give you the guarantees; you do not need to verify them yourself
- **Services backed by proven libraries or platforms** — if you are using Kafka exactly-once semantics or Postgres transactions, those protocols are already verified; verify your use of them with integration tests instead
- **Performance validation** — TLA+ says nothing about latency or throughput. Use `performance-reliability-engineering`
- **Testing that code matches spec** — TLA+ verifies the design, not the implementation. Integration tests verify the implementation
- **Chaos resilience testing** — that is `phase3/chaos-engineering`
- **Any standard service where "it passes in staging" is genuinely sufficient** — most services. TLA+ is rare.

---

## Process

### 1. Decide if TLA+ is warranted (5 minutes)

Ask three questions:
- Is there shared mutable state accessed by concurrent actors?
- Can the wrong interleaving cause data loss or silent duplication (not just a visible error)?
- Is testing all interleavings infeasible in practice?

If the answer to all three is yes: proceed. Otherwise: integration tests in `comprehensive-test-strategy` are sufficient.

### 2. Name the protocol and identify actors (30 minutes)

Write down in plain English:
- What are the actors (producers, consumers, coordinators, replicas)?
- What state does each actor own?
- What are the operations (send, receive, process, ack, commit)?
- What must always be true (safety: "no event is stored twice")?
- What must eventually become true (liveness: "every submitted event is eventually stored")?

Do this before touching TLA+. If you cannot express the invariants in English, you are not ready to formalise.

### 3. Write the TLA+ module

Structure every module the same way:

```
EXTENDS — standard modules (Naturals, Sequences, FiniteSets)
CONSTANTS — parameters (max retries, set of nodes, set of events)
VARIABLES — mutable state
TypeInvariant — type-checks for all variables
Init — initial state
Next — all possible transitions (one UNCHANGED-free action per operation)
Spec == Init /\ [][Next]_vars /\ Fairness

Safety properties — what must never happen (invariants)
Liveness properties — what must eventually happen (temporal formulas)
```

Keep the first specification small. Model 2–3 actors, 2–3 events, 1–2 retries. TLC's state space grows exponentially — a small model catches most bugs.

### 4. Run TLC model checker

```bash
# Install TLA+ Toolbox or use the CLI jar
java -jar tla2tools.jar -config MyProtocol.cfg MyProtocol.tla

# Minimal .cfg file
SPECIFICATION Spec
INVARIANT TypeInvariant NoDuplicates NoPhantomEvents
PROPERTY EventuallyStored

# Model values (keep small)
CONSTANTS
  Events = {e1, e2}
  MaxRetries = 2
```

TLC output is one of:
- **No error found** — properties hold for all states in the model. This is evidence (not proof) for the parameterised sizes you chose. Increase parameters and re-run to gain confidence.
- **Invariant violation** — TLC prints a counterexample trace. Read the trace, find the problematic interleaving, and fix the protocol design.
- **Deadlock detected** — the system reaches a state with no enabled transitions. Usually a missing recovery path.

### 5. Fix the protocol design (not the spec)

When TLC finds a violation: fix the protocol, update the spec, re-run. The spec is the design artefact. Do not massage the spec to suppress errors — that is falsifying the design.

### 6. Document the protocol

Once TLC confirms the design:
- Write a protocol doc with: actors, state, operations, safety invariants, liveness conditions
- Attach the `.tla` file to the PR or the relevant ADR
- The implementation must match the spec — if the implementation diverges, re-specify

---

## Output format with real examples

### Worked example: event idempotency protocol

The protocol: an ingestion service receives events from producers. Producers retry on failure. The service must store each event exactly once (no duplicates) and must not lose events (no phantom gaps).

```tla
----- MODULE EventIdempotency -----
EXTENDS Naturals, FiniteSets

CONSTANTS Events, MaxRetries

VARIABLES
  pending,        \* Events waiting to be processed (producer's view)
  processed,      \* Event IDs the service has acknowledged
  storage,        \* Events written to the store (must contain each event once)
  retry_count     \* Number of retries remaining per event

TypeInvariant ==
  /\ pending \subseteq Events
  /\ processed \subseteq {e.id : e \in Events}
  /\ storage \subseteq Events
  /\ \A e \in Events : retry_count[e] \in 0..MaxRetries

\* Safety: no event appears in storage more than once
NoDuplicates ==
  \A e1, e2 \in storage : e1.id = e2.id => e1 = e2

\* Safety: every event in storage was in the original event set
NoPhantomEvents ==
  \A e \in storage : e \in Events

\* Liveness: every event is eventually stored (under fair scheduling)
EventuallyStored ==
  \A e \in Events : <>(e \in storage)

Init ==
  /\ pending = Events
  /\ processed = {}
  /\ storage = {}
  /\ retry_count = [e \in Events |-> MaxRetries]

\* Producer sends event; service checks idempotency key
ProcessEvent(e) ==
  /\ e \in pending
  /\ e.id \notin processed
  /\ storage' = storage \cup {e}
  /\ processed' = processed \cup {e.id}
  /\ pending' = pending \ {e}
  /\ UNCHANGED retry_count

\* Duplicate delivery: event arrives again; service rejects (already processed)
RejectDuplicate(e) ==
  /\ e \in pending
  /\ e.id \in processed
  /\ pending' = pending \ {e}
  /\ UNCHANGED <<storage, processed, retry_count>>

\* Producer retries after transient failure
RetryEvent(e) ==
  /\ e \in pending
  /\ retry_count[e] > 0
  /\ retry_count' = [retry_count EXCEPT ![e] = retry_count[e] - 1]
  /\ UNCHANGED <<pending, processed, storage>>

Next ==
  \E e \in Events :
    \/ ProcessEvent(e)
    \/ RejectDuplicate(e)
    \/ RetryEvent(e)

Fairness == WF_<<pending, processed, storage, retry_count>>(Next)

Spec == Init /\ [][Next]_<<pending, processed, storage, retry_count>> /\ Fairness

====
```

### TLC output (no violation)

```
TLC2 Version 2.16
Running breadth-first search Model-Checking with 4 workers
Computed 1,847 states, 3,204 distinct states, 0 states left on queue.

No errors have been found.

Finished in 00s at (2026-04-20 10:14:22)
```

### TLC output (invariant violated — counterexample trace)

```
Invariant NoDuplicates is violated.

The following behaviour constitutes a counter-example:

State 1: Init
  pending = {e1, e2}, processed = {}, storage = {}

State 2: ProcessEvent(e1)
  storage = {e1}, processed = {e1_id}

State 3: RetryEvent(e1)  \* e1 still in pending due to ACK loss
  pending = {e1, e2}     \* <-- this reveals an ACK loss case

State 4: ProcessEvent(e1) again
  storage = {e1, e1}     \* NoDuplicates VIOLATED
```

This trace tells you the protocol is missing idempotency key persistence across the `RetryEvent` path.

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] formal-verification — [one-line description]
```

Example entries:
```
[2026-04-20] formal-verification — TLA+ spec for event idempotency protocol; NoDuplicates confirmed for MaxRetries=3
[2026-04-20] formal-verification — TLC found ACK-loss duplicate in ingestion protocol; fixed and re-verified
[2026-04-20] formal-verification — Specified distributed lock protocol; Liveness violation found under starvation scenario
```

---

## Reference files

`references/tlaplus-guide.md` contains:
- TLA+ operator cheatsheet (set operators, temporal operators, action operators)
- Common invariant patterns (NoDuplicates, NoLostMessages, NoPhantomWrites)
- Common liveness patterns (EventuallyDelivered, EventuallyConsistent)
- TLC configuration reference
- How to interpret counterexample traces
- Links to the TLA+ Toolbox and PlusCal translator
