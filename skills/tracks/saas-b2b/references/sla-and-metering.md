# SLAs and usage metering

SLAs convert uptime into a financial instrument. Metering converts usage into revenue. Both turn engineering decisions into contract outcomes. This reference covers how to pick an uptime tier without overcommitting, how credits compute cleanly, how to instrument a billable event so it can survive an audit, and the integration hooks to the billing system.

---

## Uptime SLA tiers

| Tier | Monthly downtime budget | Typical context |
|------|------------------------|-----------------|
| 99.9% | 43 min 49 sec | Default for paid tier. Realistic without heroics. |
| 99.95% | 21 min 54 sec | Enterprise tier with dedicated on-call. Multi-AZ minimum. |
| 99.99% | 4 min 23 sec | Mission-critical. Multi-region, active-active, formal change management. Expensive. |

Rules for committing:

- Never commit to a higher SLA than the weakest dependency. If your auth provider offers 99.9%, you cannot offer 99.99% honestly.
- Exclude planned maintenance windows explicitly in the contract, with notice requirements (typically 72h).
- Exclude force-majeure events and customer-caused outages (their misconfigured SSO, their IP blocklist, their account suspension).
- Measure from the edge the customer experiences, not from the inside of the product. An internal health check at 100% with an unreachable load balancer is a 0% month for the customer.
- The engineering team enforcing the SLA must be the same team authorizing the contract language. "Sales promised 99.99%" is how breach-of-contract clauses enter your Jira backlog.

---

## Credit calculation

SLA credits are the contractual remedy when uptime falls below the committed tier. Keep the formula simple enough to compute without a lawyer and defensible enough to survive one.

Typical tiered credit schedule:

| Actual uptime | Credit |
|--------------|--------|
| < 99.9% and >= 99.0% | 10% of monthly fee |
| < 99.0% and >= 95.0% | 25% of monthly fee |
| < 95.0% | 50% of monthly fee |

Implementation notes:

- Credits are applied to the next invoice, not refunded. Never commit to cash refunds — they break accounting and create legal exposure.
- A claim cap (max credit = 50% of monthly fee) is standard and negotiable upwards only in enterprise contracts.
- Customers must file a claim within a window (30 or 60 days) with supporting data. You are entitled to independently verify the outage before granting the credit — automate this verification against the same uptime signal you bill against.
- Per-tier SLOs: a free-tier tenant does not need a 99.9% SLO, but the same infrastructure may carry both. Measure them separately; commit contractually only to paid and enterprise.

```python
def compute_credit(tenant: Tenant, month: Month, uptime: Decimal) -> Credit:
    contract = tenant.active_contract_for(month)
    if uptime >= contract.sla_threshold:
        return Credit.zero()
    if uptime < Decimal("0.95"):
        pct = Decimal("0.50")
    elif uptime < Decimal("0.99"):
        pct = Decimal("0.25")
    else:
        pct = Decimal("0.10")
    return Credit(
        tenant_id=tenant.id,
        month=month,
        amount=contract.monthly_fee * pct,
        reason=f"SLA breach: {uptime:.4%} vs {contract.sla_threshold:.4%}",
    )
```

---

## Usage metering — the billable event

Consumption-based billing requires that each chargeable action produces a clean, durable, replayable event. A "billable event" is the atomic unit of what gets counted on an invoice.

Cleanly defining one is harder than it looks. Examples:

- API request: one billed event per request, with metadata (endpoint, tenant, timestamp, status_code). Easy.
- Active user: one billed event per user per calendar month in which they logged in at least once. Requires de-duplication across the month.
- Data stored: one billed event per GB-hour. Emit at fixed intervals (hourly). Requires a reliable sampler.
- LLM tokens: one event per completed API call with `tokens_in` and `tokens_out`. Events are frequent and small; batch aggressively.

Rules:

- The billable event has a unique, idempotent identifier. Re-emitting the same event ID produces no duplicate charges. This is the only way to survive retries, replays, and reprocessing without over-billing.
- The event carries the billing attributes the pricing model needs — no more, no less. Pricing changes should not require backfilling events from logs.
- Emission is asynchronous from the user request. Write the event to a durable buffer (Kafka, Kinesis, Postgres outbox) in the request path; aggregate and push to billing out of band.
- Aggregation is deterministic. Same input events must produce the same aggregates forever. This is what lets a customer dispute an invoice and you recompute it from events.

---

## Event sourcing for billable events

The outbox pattern is the right shape for billable events. See `phase2/distributed-systems-patterns` for the general pattern; this is the specialization.

```sql
CREATE TABLE billing_events (
  id uuid PRIMARY KEY,           -- idempotency key
  tenant_id uuid NOT NULL,
  event_type text NOT NULL,      -- 'api_request', 'active_user', 'storage_hour'
  quantity numeric NOT NULL,
  occurred_at timestamptz NOT NULL,
  attributes jsonb NOT NULL,
  emitted_at timestamptz,        -- when sent to billing provider, NULL if pending
  emitted_event_id text          -- billing provider's receipt
);

CREATE INDEX billing_events_pending
  ON billing_events (occurred_at)
  WHERE emitted_at IS NULL;
```

Emitter daemon:

```python
def flush_pending_events(batch_size: int = 500) -> None:
    events = db.fetch_pending_events(limit=batch_size)
    if not events:
        return
    for ev in events:
        receipt = stripe.v1.billing.meter_events.create(
            event_name=ev.event_type,
            payload={"tenant_id": str(ev.tenant_id), "value": str(ev.quantity)},
            identifier=str(ev.id),                  # idempotency key
            timestamp=int(ev.occurred_at.timestamp()),
        )
        db.mark_emitted(ev.id, receipt.id)
```

The `identifier` is the durable idempotency key. Stripe (and every serious metering API) de-duplicates on it. Running the flusher twice is safe.

---

## Invoicing integration hooks

Most B2B SaaS products use Stripe, with Recurly / Chargebee / Zuora at higher price points. Integration surface:

| Hook | Direction | Purpose |
|------|-----------|---------|
| `customer.created` | Ours → billing | Create billing customer when tenant signs contract |
| `subscription.created` | Ours → billing | Attach plan (seats, usage component, etc.) |
| `meter_event.create` | Ours → billing | Push each billable event |
| `invoice.finalized` | Billing → ours (webhook) | Apply SLA credits, validate totals, notify customer |
| `invoice.payment_failed` | Billing → ours (webhook) | Trigger dunning flow, optionally suspend service |
| `subscription.cancelled` | Billing → ours (webhook) | Tenant offboarding flow |

Rules:

- Webhooks must be idempotent. Billing providers retry; your handler must produce the same result regardless of how many times it fires.
- Verify webhook signatures. Every major provider signs payloads; an unsigned webhook handler is a remote write endpoint for the internet.
- Never treat the billing system as source of truth for product state. Whether a tenant has access is a decision your app makes based on its own subscription snapshot — the billing webhook updates the snapshot.

---

## Defining the billable event cleanly — a worked example

A customer argues their October API-request invoice is overstated. What should be true:

1. You can regenerate the October invoice from `billing_events` alone, with no access to any logging system or the billing provider's data.
2. Every event has a `tenant_id`, `occurred_at`, and unique `id`. Counting `WHERE tenant_id = X AND occurred_at BETWEEN '2026-10-01' AND '2026-11-01'` reproduces the October quantity exactly.
3. Every event's `attributes.request_id` (or similar) can be cross-referenced to your access logs for that request. The customer can audit a sample and confirm the event corresponds to a real API call they made.
4. No two events share an `id`. Duplicate writes to the table are rejected; duplicate emissions to the billing provider are de-duplicated on the `identifier`.
5. Emission retries do not inflate the count. If a network partition caused the flusher to retry 40 times for the same event, the customer sees one charge.

If any of these is not true, the billable-event definition is not clean — fix it before the dispute, not during.

---

## Verification checklist

- SLA tier committed does not exceed the weakest upstream dependency.
- Uptime is measured at the customer edge, not internal health.
- Credit formula is implemented in code and unit-tested against historical breach scenarios.
- Each billable event has a durable, idempotent `id`.
- Billable events are written to an outbox, emitted asynchronously, and confirmed emitted.
- Webhook handlers from the billing provider verify signatures and are idempotent.
- The October invoice can be regenerated from the event table alone for any given tenant.
