# Reconciliation runbook

Reconciliation is the nightly process that proves your internal ledger matches what the processor actually moved. Without it, you do not know whether you are losing money. With it, you discover discrepancies within hours instead of months.

This runbook defines the triggers, steps, escalation, and example queries for daily and weekly reconciliation of payment records against processor records.

---

## Scope

Reconcile every money-movement object you originate with the processor's record of the same object. Typical objects:

- Charges / payment intents
- Refunds
- Payouts (processor → your bank)
- Transfers (between connected accounts, e.g., Stripe Connect)
- Disputes and chargebacks (as they move through lifecycle states)

For each object type, maintain a reconciliation job. Running them as one monolithic job is brittle — when refunds fail to reconcile, charges should still run.

---

## Triggers

| Trigger | Scope | Cadence |
|---------|-------|---------|
| Nightly batch | All charges, refunds, payouts from the previous UTC day | Every day, 02:00 UTC |
| Weekly sweep | Past 7 days (catches late-settling items) | Every Monday, 03:00 UTC |
| Monthly full | Past 31 days; produces the finance-team report | First of month, 04:00 UTC |
| On-demand | Operator-triggered for a specific date range | Manual |

Nightly catches most issues. Weekly catches items whose processor-side state changed after the nightly window (payouts in transit, disputes opened). Monthly is the authoritative report for finance.

---

## Steps — nightly batch

1. **Fetch processor records for the window.** Pull all charges, refunds, payouts from the processor where `created` falls in `[yesterday 00:00 UTC, yesterday 23:59:59 UTC]`. Use pagination; never assume one page.
2. **Fetch internal records for the same window.** From the `orders` / `charges` / `ledger_entries` tables.
3. **Join on external ID.** Every internal record should have a `processor_charge_id`. Every processor record should map to an internal `order_id` via metadata.
4. **Classify each record:**
   - **Matched:** present on both sides; amount, currency, status all equal.
   - **Missing internal:** exists in processor, absent or `unknown` on your side.
   - **Missing external:** exists internally, absent on processor side.
   - **Mismatch:** exists on both sides but amount, currency, or status differs.
5. **Write the report** to `recon_reports` with per-category counts and line items for each mismatch.
6. **Alert** if mismatches > 0 or missing > 0. Zero-count days are logged but silent.
7. **Auto-heal where safe** (see below). Queue the rest for operator review.

---

## Auto-heal categories

Some mismatches are safe to resolve without a human. Keep this list small; when in doubt, escalate.

| Category | Action |
|----------|--------|
| Internal status `pending`, processor status `succeeded`, amounts match | Update internal to `succeeded`. This is a webhook-miss recovery. |
| Internal status `succeeded`, processor status `refunded` (full), matching refund in processor | Mark order `refunded`; create the missing internal refund row. |
| Processor record present, internal record missing entirely | Do NOT auto-create. Someone made a payment outside your system. Escalate. |
| Amount mismatch | Never auto-heal. Always escalate. |
| Currency mismatch | Never auto-heal. Always escalate. |

---

## Escalation

| Severity | Condition | Action |
|----------|-----------|--------|
| P3 (info) | 1–3 orphan webhook-miss items; auto-healed | Log only |
| P2 (warn) | More than 3 auto-heals in one run, or any mismatch queued for review | Page the on-call engineer the next business morning; post to #payments-ops |
| P1 (high) | Amount or currency mismatch; missing external record; processor balance diverges from ledger by >$1 | Page on-call immediately; freeze automated payouts until resolved |
| P0 (crit) | Net ledger vs processor delta > $100 or > 0.1% of volume | Page on-call + finance lead immediately; consider halting new charges pending investigation |

Payment ops ≠ SRE ops. The on-call rotation may need its own roster.

---

## Queries to run (Stripe + Postgres Orders table)

Assume internal table:

```sql
CREATE TABLE orders (
    order_id         TEXT PRIMARY KEY,
    processor_charge_id TEXT UNIQUE,
    amount_cents     BIGINT NOT NULL,
    currency         TEXT   NOT NULL,
    status           TEXT   NOT NULL,  -- pending|succeeded|failed|refunded
    created_at       TIMESTAMPTZ NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL
);
```

And a staging table loaded each run from the Stripe API:

```sql
CREATE TABLE stripe_charges_staging (
    charge_id      TEXT PRIMARY KEY,
    order_id_meta  TEXT,            -- metadata.order_id from Stripe
    amount_cents   BIGINT NOT NULL,
    currency       TEXT   NOT NULL,
    status         TEXT   NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL
);
```

### Missing internal (present in Stripe, absent locally)

```sql
SELECT s.charge_id, s.order_id_meta, s.amount_cents, s.currency, s.status
FROM stripe_charges_staging s
LEFT JOIN orders o ON o.processor_charge_id = s.charge_id
WHERE o.order_id IS NULL
  AND s.created_at >= $1 AND s.created_at < $2;
```

### Missing external (present locally, absent in Stripe)

```sql
SELECT o.order_id, o.processor_charge_id, o.amount_cents, o.status
FROM orders o
LEFT JOIN stripe_charges_staging s ON s.charge_id = o.processor_charge_id
WHERE s.charge_id IS NULL
  AND o.status = 'succeeded'
  AND o.created_at >= $1 AND o.created_at < $2;
```

### Amount or status mismatch on matched rows

```sql
SELECT o.order_id, o.processor_charge_id,
       o.amount_cents   AS internal_amount,
       s.amount_cents   AS stripe_amount,
       o.status         AS internal_status,
       s.status         AS stripe_status
FROM orders o
JOIN stripe_charges_staging s ON s.charge_id = o.processor_charge_id
WHERE (o.amount_cents <> s.amount_cents
       OR o.currency <> s.currency
       OR o.status <> CASE s.status
                         WHEN 'succeeded' THEN 'succeeded'
                         WHEN 'failed'    THEN 'failed'
                         ELSE o.status   -- tolerate legal intermediate states
                      END)
  AND o.created_at >= $1 AND o.created_at < $2;
```

### Daily summary (ship this to #payments-ops each morning)

```sql
SELECT
  COUNT(*) FILTER (WHERE matched)                           AS matched,
  COUNT(*) FILTER (WHERE category = 'missing_internal')     AS missing_internal,
  COUNT(*) FILTER (WHERE category = 'missing_external')     AS missing_external,
  COUNT(*) FILTER (WHERE category = 'mismatch')             AS mismatch,
  SUM(amount_cents) FILTER (WHERE matched)                  AS matched_volume_cents
FROM recon_results
WHERE run_id = $1;
```

---

## Worked example — nightly Stripe charge reconciliation

Pipeline, roughly:

```python
import stripe, datetime as dt

def reconcile(day: dt.date):
    start = dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)
    end   = start + dt.timedelta(days=1)

    # 1. Pull Stripe charges for the window, page through results
    charges = []
    for c in stripe.Charge.list(
        created={"gte": int(start.timestamp()), "lt": int(end.timestamp())},
        limit=100,
    ).auto_paging_iter():
        charges.append(c)

    # 2. Load internal rows
    internal = db.query(
        "SELECT order_id, processor_charge_id, amount_cents, currency, status "
        "FROM orders WHERE created_at >= %s AND created_at < %s",
        (start, end),
    )

    # 3. Index both sides
    by_charge = {r.processor_charge_id: r for r in internal if r.processor_charge_id}
    results = []

    for c in charges:
        internal_row = by_charge.get(c.id)
        if not internal_row:
            results.append(("missing_internal", c))
            continue
        if c.amount != internal_row.amount_cents or c.currency != internal_row.currency:
            results.append(("mismatch_amount_or_currency", c, internal_row))
            continue
        if not status_equivalent(c.status, internal_row.status):
            results.append(("mismatch_status", c, internal_row))
            continue
        results.append(("matched", c, internal_row))

    # 4. Anything internal without a corresponding Stripe charge
    stripe_ids = {c.id for c in charges}
    for r in internal:
        if r.status == "succeeded" and r.processor_charge_id not in stripe_ids:
            results.append(("missing_external", r))

    persist_results(day, results)
    alert_if_needed(results)
```

---

## What success looks like

- Daily summary posts with `matched=N, missing=0, mismatch=0`.
- Any non-zero categories get a paged review within the SLA in the escalation table.
- At month close, the sum of matched volume equals processor deposits minus processor fees, within a known float for in-transit payouts.
- Historical reconciliation reports are retained for at least 7 years — regulators, tax, and audits expect to see them.

If you have not seen a mismatch for 90 days, verify the job is actually running. A silent reconciliation is worse than no reconciliation.
