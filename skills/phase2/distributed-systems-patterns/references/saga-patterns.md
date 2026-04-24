# Saga patterns — orchestration vs choreography

A saga is a sequence of local transactions across multiple services, where each step has a compensating action that undoes its effect. Sagas replace distributed ACID transactions, which do not work well across service boundaries.

---

## When a saga is the right tool

- A business workflow spans 2+ services and each step mutates state the other services cannot see.
- The workflow has a clear "happy path" but failures at any step are possible and must be recoverable.
- Eventual consistency is acceptable (saga does not give you linearizable multi-service writes).

## When a saga is overkill

- Single service + single database → just use a DB transaction.
- The workflow is read-only — no state to compensate.
- The workflow has one "real" write and one "nice to have" side-effect (e.g. analytics) — use the outbox, not a saga.
- You can model the operation as idempotent replay from a single event log — consider event sourcing's natural replay instead.

---

## Orchestration vs choreography — the trade

### Orchestration

One service (the orchestrator) owns the workflow. It calls each step synchronously or via commands, tracks progress, and decides what to do on failure.

```
┌─────────────────┐
│   Orchestrator  │
└────┬───┬───┬────┘
     │   │   │
     ▼   ▼   ▼
 ┌────┐ ┌────┐ ┌─────┐
 │Inv │ │Pay │ │Ship │
 └────┘ └────┘ └─────┘
```

**Pros:**
- Single mental model: "look at the orchestrator code to see the workflow."
- Easy to add a new step — edit one place.
- State of any in-flight workflow is queryable in one system.
- Debugging is straightforward — one log has the full trace.

**Cons:**
- The orchestrator is a coupling hub. Every participant is known to it.
- Orchestrator itself is a service that must be highly available.
- Can become a god-object if you keep adding workflows.

### Choreography

No central coordinator. Each service publishes events about what it did, and other services react to those events.

```
Order service ───OrderPlaced───▶ (bus)
                                  │ ├──▶ Inventory (reserve)
                                  │ ├──▶ Payment (charge)
                                  │ └──▶ Shipping (create label)

Inventory ──────InventoryReserved─▶ (bus)
...
```

**Pros:**
- Loosely coupled — new consumers can subscribe without changing producers.
- No central failure point.
- Scales naturally with event volume.

**Cons:**
- End-to-end state is not materialized anywhere. "Is order 42 done?" requires aggregating across services.
- Cyclic event chains are hard to spot in code review — workflow lives in the event topology, not in any file.
- Debugging requires excellent distributed tracing. Without it, on-call engineers drown.
- Compensations for multi-step failures are harder — there is no single place that "knows" what has been done.

### Decision matrix

| If... | Prefer |
|-------|--------|
| Workflow is well-defined and unlikely to change often | Orchestration |
| Many consumers react to the same event | Choreography |
| Team lacks mature distributed tracing | Orchestration |
| You need to answer "what's the state of workflow X?" in one query | Orchestration |
| Services are owned by different teams with different release cadences | Choreography |
| Compensation logic is non-trivial | Orchestration |

**Default:** orchestration. Move to choreography only with a specific reason and the tracing to support it.

---

## Compensation design rules

Every mutating step needs a compensation. Write it at the same time as the forward step.

1. **Compensation must be idempotent.** It will be retried. `DELETE WHERE id = X` is safe to replay; `decrement_count()` is not.
2. **Compensation cannot fail permanently.** If it does, you must surface it as a ticket / alert — never swallow. Log and retry with backoff; after retries are exhausted, emit to a dead-letter queue AND alert on-call.
3. **Order compensations in reverse.** If steps are A, B, C and C fails, compensate C (if partially done), then B, then A.
4. **Irreversible steps go last.** Sending an email, transferring physical goods, calling a third-party billing API that cannot refund — these go AFTER all reversible steps have committed. You cannot un-send an email.
5. **Include the original context in the compensation payload.** The compensator may run hours later; it needs the correlation ID, original amounts, etc.

### Compensation patterns by step type

| Forward step | Compensation |
|--------------|--------------|
| Insert row | Delete row (by natural key) |
| Reserve resource | Release reservation |
| Charge card | Refund card |
| Deduct inventory | Add inventory back |
| Create external record (Stripe customer, etc.) | Delete or mark inactive |
| Send email / SMS | None — move step to end |
| Transfer physical goods | None — move to end, or design human-in-loop reversal |

---

## Worked example — orchestrated order-placement saga

```python
class PlaceOrderSaga:
    """Orchestrated saga for placing an order across inventory, payment, shipping."""

    def __init__(self, inventory, payments, shipping, notifier, saga_log):
        self.inventory = inventory
        self.payments = payments
        self.shipping = shipping
        self.notifier = notifier
        self.saga_log = saga_log  # persistent log of saga state for recovery

    def run(self, cmd: PlaceOrder) -> SagaResult:
        saga_id = cmd.order_id
        self.saga_log.start(saga_id, cmd)

        try:
            self.saga_log.mark("reserve_inventory_started", saga_id)
            self.inventory.reserve(cmd.order_id, cmd.items, idem_key=f"{saga_id}-inv")
            self.saga_log.mark("reserve_inventory_done", saga_id)

            self.saga_log.mark("charge_started", saga_id)
            charge = self.payments.charge(cmd.order_id, cmd.amount, idem_key=f"{saga_id}-pay")
            self.saga_log.mark("charge_done", saga_id, {"charge_id": charge.id})

            self.saga_log.mark("shipment_started", saga_id)
            shipment = self.shipping.create(cmd.order_id, cmd.address, idem_key=f"{saga_id}-shp")
            self.saga_log.mark("shipment_done", saga_id, {"shipment_id": shipment.id})

            # Irreversible — last
            self.notifier.send_confirmation(cmd.order_id)
            self.saga_log.complete(saga_id)
            return SagaResult.ok(cmd.order_id)

        except SagaStepError as e:
            self._compensate(saga_id)
            self.saga_log.failed(saga_id, reason=str(e))
            return SagaResult.failed(cmd.order_id, reason=str(e))

    def _compensate(self, saga_id: str) -> None:
        state = self.saga_log.load(saga_id)
        # Reverse order; skip steps that never started
        if "shipment_done" in state.marks:
            self._retry(lambda: self.shipping.cancel(state.marks["shipment_done"]["shipment_id"]))
        if "charge_done" in state.marks:
            self._retry(lambda: self.payments.refund(state.marks["charge_done"]["charge_id"]))
        if "reserve_inventory_done" in state.marks:
            self._retry(lambda: self.inventory.release(saga_id))
```

**Key points:**
- Each step uses a deterministic idempotency key derived from the saga id — replays are safe.
- `saga_log` is persistent (e.g. a DB table). On orchestrator crash, a recovery process can resume mid-saga by inspecting the log.
- Compensations themselves are retried with backoff. A compensation that ultimately fails alerts on-call — it never silently drops.

---

## Worked example — choreographed flow

```
Order service
  └─ writes order + outbox row "OrderPlaced" → Kafka

Inventory service
  └─ consumes OrderPlaced
     └─ reserves inventory
     └─ emits "InventoryReserved" OR "InventoryReservationFailed"

Payment service
  └─ consumes InventoryReserved
     └─ charges card
     └─ emits "PaymentCompleted" OR "PaymentFailed"

Shipping service
  └─ consumes PaymentCompleted
     └─ creates shipment
     └─ emits "ShipmentCreated"

Order service
  └─ consumes ShipmentCreated → marks order complete
  └─ consumes *Failed events → emits compensation events
```

**Compensation flow** in choreography is itself event-driven. E.g. `PaymentFailed` triggers an `InventoryReleaseRequested` event the inventory service subscribes to. This doubles the event topology and makes tracing critical.

---

## Saga recovery after orchestrator crash

Orchestrators crash. Design for it.

1. Persist saga state transitions before and after each step. An event-sourced saga log (append-only) is ideal.
2. On startup, the orchestrator scans for sagas in a non-terminal state (`in_progress`, `compensating`).
3. For each, determine the last committed step and resume from there. Because each step is idempotent (via idempotency key), resuming is safe.
4. Put a timeout on in-progress sagas. A saga stuck in `charge_started` for >10 minutes means the payment call hung; the orchestrator must decide — check payment status explicitly, or compensate.

---

## Anti-patterns specific to sagas

- **Saga with no compensations.** "We'll figure it out if it fails." You will not — you'll find half-completed orders in prod at 2am.
- **Saga log kept in memory.** Crash = lost workflow. Saga state must be persistent.
- **Compensation that is not idempotent.** First compensation attempt times out; second attempt over-refunds the customer.
- **Irreversible step in the middle.** Email sent before shipping fails → customer gets confirmation for an order that never ships.
- **Saga driving another saga synchronously.** Nested sagas create nested failure modes. Keep sagas flat; if one saga needs to trigger another, do it via an event at the end of the first.
