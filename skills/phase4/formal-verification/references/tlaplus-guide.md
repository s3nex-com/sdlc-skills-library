# TLA+ reference guide

## Operator cheatsheet

### Set operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `\in` | Element of | `e \in Events` |
| `\notin` | Not element of | `e \notin processed` |
| `\subseteq` | Subset | `pending \subseteq Events` |
| `\cup` | Union | `storage \cup {e}` |
| `\cap` | Intersection | `pending \cap processed` |
| `\` | Set difference | `pending \ {e}` |
| `{}` | Empty set | `storage = {}` |
| `{x \in S : P(x)}` | Set filter | `{e \in Events : e.id \in processed}` |
| `\A x \in S : P` | Universal quantifier | `\A e \in storage : e \in Events` |
| `\E x \in S : P` | Existential quantifier | `\E e \in Events : e \notin storage` |
| `Cardinality(S)` | Set size (FiniteSets) | `Cardinality(storage) = 1` |

### Action operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `x'` | Next value of x | `storage' = storage \cup {e}` |
| `UNCHANGED x` | x does not change | `UNCHANGED <<storage, processed>>` |
| `UNCHANGED <<x, y>>` | Tuple unchanged | Preferred over multiple UNCHANGED |
| `/\` | Logical AND (used in actions) | `e \in pending /\ e.id \notin processed` |
| `\/` | Logical OR | `ProcessEvent(e) \/ RejectDuplicate(e)` |

### Temporal operators (for liveness properties)

| Operator | Meaning | Example |
|----------|---------|---------|
| `[]P` | Always P | `[]NoDuplicates` |
| `<>P` | Eventually P | `<>(e \in storage)` |
| `P ~> Q` | P leads to Q | `(e \in pending) ~> (e \in storage)` |
| `WF_vars(A)` | Weak fairness of action A | Enabled A must eventually occur |
| `SF_vars(A)` | Strong fairness of action A | Repeatedly enabled A must eventually occur |

Most liveness properties only require `WF` (weak fairness). Use `SF` only when an action may be enabled and disabled repeatedly.

---

## Common invariant patterns

### No duplicate writes

```tla
NoDuplicates ==
  \A e1, e2 \in storage : e1.id = e2.id => e1 = e2
```

### No phantom writes (every stored item came from a valid source)

```tla
NoPhantomWrites ==
  \A e \in storage : e \in Events
```

### No lost messages (everything sent is eventually received)

```tla
NoLostMessages ==
  \A m \in sent : m \in delivered \/ m \in inFlight
```

### At most one leader at any time

```tla
AtMostOneLeader ==
  Cardinality({n \in Nodes : role[n] = "leader"}) <= 1
```

### Lock exclusion (at most one holder)

```tla
MutualExclusion ==
  \A n1, n2 \in Nodes :
    (holding[n1] /\ holding[n2]) => n1 = n2
```

### Monotonic sequence numbers (no rollback)

```tla
MonotonicSeqNums ==
  \A n \in Nodes : seq_num[n] >= seq_num_history[n]
```

---

## Common liveness patterns

### Every submitted event is eventually stored

```tla
EventuallyStored ==
  \A e \in Events : <>(e \in storage)
```

### Every message is eventually delivered

```tla
EventuallyDelivered ==
  \A m \in Messages : <>(m \in delivered)
```

### System eventually reaches consistent state

```tla
EventuallyConsistent ==
  <>(\A n \in Nodes : state[n] = state[CHOOSE n2 \in Nodes : TRUE])
```

### Leader is eventually elected

```tla
EventuallyHasLeader ==
  <>(Cardinality({n \in Nodes : role[n] = "leader"}) = 1)
```

---

## Module structure (full template)

```tla
----- MODULE ProtocolName -----
EXTENDS Naturals, Sequences, FiniteSets

\* Parameters (set in .cfg file)
CONSTANTS
  Nodes,        \* Set of participating nodes
  Events,       \* Set of events in the model
  MaxRetries    \* Retry limit

\* State variables
VARIABLES
  state,        \* Function from Nodes to state values
  messages,     \* Set of in-flight messages
  processed     \* Set of processed event IDs

\* Helpers
vars == <<state, messages, processed>>

\* Type invariant (run as INVARIANT in TLC)
TypeInvariant ==
  /\ \A n \in Nodes : state[n] \in {"idle", "processing", "done"}
  /\ messages \subseteq Messages
  /\ processed \subseteq {e.id : e \in Events}

\* Initial state
Init ==
  /\ state = [n \in Nodes |-> "idle"]
  /\ messages = {}
  /\ processed = {}

\* Actions (one per logical operation)
SendEvent(e, n) ==
  /\ e \notin processed   \* Guard: only if not yet processed
  /\ messages' = messages \cup {[event |-> e, dest |-> n]}
  /\ UNCHANGED <<state, processed>>

ProcessEvent(m) ==
  /\ m \in messages
  /\ m.event.id \notin processed
  /\ processed' = processed \cup {m.event.id}
  /\ messages' = messages \ {m}
  /\ UNCHANGED state

\* Next state relation
Next ==
  \/ \E e \in Events, n \in Nodes : SendEvent(e, n)
  \/ \E m \in messages : ProcessEvent(m)

\* Fairness (needed for liveness properties)
Fairness == WF_vars(Next)

\* Full specification
Spec == Init /\ [][Next]_vars /\ Fairness

\* Safety properties (checked as INVARIANT)
NoDuplicates ==
  \A e1, e2 \in processed : e1 = e2  \* processed is a set, so this holds trivially
                                      \* for storage: check the storage set

\* Liveness properties (checked as PROPERTY)
EventuallyProcessed ==
  \A e \in Events : <>(e.id \in processed)

====
```

---

## TLC configuration file reference

```cfg
\* MyProtocol.cfg

\* Specify the top-level specification formula
SPECIFICATION Spec

\* Invariants: checked in every reachable state
INVARIANT TypeInvariant
INVARIANT NoDuplicates
INVARIANT NoPhantomWrites

\* Properties: temporal formulas (liveness)
PROPERTY EventuallyProcessed

\* Model values: small sets for tractable state space
CONSTANTS
  Nodes = {n1, n2}
  Events = {e1, e2}
  MaxRetries = 2

\* Symmetry sets (reduces state space): safe for unordered sets
SYMMETRY {Nodes, Events}
```

### TLC invocation

```bash
# Command-line (requires tla2tools.jar)
java -jar tla2tools.jar -config MyProtocol.cfg MyProtocol.tla

# With worker threads (speeds up model checking)
java -jar tla2tools.jar -workers 4 -config MyProtocol.cfg MyProtocol.tla

# With depth-first search (finds errors faster, less exhaustive)
java -jar tla2tools.jar -dfid 20 -config MyProtocol.cfg MyProtocol.tla
```

---

## How to interpret counterexample traces

When TLC reports an invariant violation, it prints a sequence of states leading to the violation.

```
Invariant NoDuplicates is violated.

The following behaviour constitutes a counter-example:

State 1: <Initial predicate>
  pending = {e1, e2}
  processed = {}
  storage = {}

State 2: ProcessEvent(e1)
  pending = {e2}
  processed = {e1_id}
  storage = {e1}

State 3: RetryEvent(e1)     \* e1 was re-added to pending (ACK was lost)
  pending = {e1, e2}
  processed = {e1_id}
  storage = {e1}

State 4: ProcessEvent(e1)   \* Idempotency check missed: e1_id was in processed
  storage = {e1, e1}        \* VIOLATION
```

**Reading the trace:**
1. Find the last state — it contains the violated invariant
2. Find the first state where something unexpected happened (State 3 above)
3. That is the missing protocol handling — the guard in `ProcessEvent` was too weak
4. Fix: add `e.id \notin processed` as a guard in `ProcessEvent`, or ensure ACK loss does not re-add processed events to `pending`

**Common violation patterns:**

| Violation | Usual cause |
|-----------|-------------|
| Duplicate in storage | Missing idempotency check in a retry path |
| Lost message | Missing action for an in-flight message |
| Deadlock | An action has no enabled transitions from some reachable state — missing recovery path |
| Liveness violation | Fairness assumption too weak; a process can be starved indefinitely |

---

## Tooling and resources

**TLA+ Toolbox (GUI)**
Download: https://github.com/tlaplus/tlaplus/releases
The Toolbox integrates TLC and the PlusCal translator. Good for first-time use.

**tla2tools.jar (CLI)**
Download the same release. Use for scripted model checking and CI integration.

**PlusCal**
PlusCal is an algorithm language that compiles to TLA+. It is easier to write than raw TLA+ for imperative-style algorithms. Use it when describing an algorithm that looks like pseudocode; use raw TLA+ when specifying state machines directly.

```
--algorithm EventProcessing {
  variables pending = Events, processed = {};
  process (Consumer \in Nodes) {
    loop: while (pending /= {}) {
      with (e \in pending) {
        if (e.id \notin processed) {
          processed := processed \cup {e.id};
        };
        pending := pending \ {e};
      }
    }
  }
}
```

**Key learning resources**
- Hillel Wayne's *Practical TLA+* — the most accessible introduction for working engineers
- Leslie Lamport's *Specifying Systems* — the definitive reference
- TLA+ Community Modules: https://github.com/tlaplus/CommunityModules — reusable definitions
- TLA+ Examples: https://github.com/tlaplus/Examples — real protocol specifications
