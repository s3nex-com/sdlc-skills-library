# Fraud signal integration

Every payment system needs a fraud stance. Building fraud scoring in-house from scratch is a multi-year investment; integrating a provider (Stripe Radar, Sift, Signifyd, Kount) takes days to weeks and is the right call for 3-5 person teams. This guide is the integration pattern: when to call, how to act on verdicts, how to handle uncertainty, how to build a manual review queue, and how to close the feedback loop so the provider's model keeps improving.

---

## When to call the fraud provider

Not every transaction needs a fraud score. Scoring costs money (per-call fees) and latency (50–300ms). Call on events that actually matter.

| Event | Score? |
|-------|--------|
| Account signup / registration | Yes (Sift/Signifyd) — catches synthetic identity early |
| First payment method added | Yes |
| Charge attempt (new card or unfamiliar amount) | Yes |
| Charge attempt (returning card, typical amount) | Optional — let issuer handle |
| High-velocity events (5+ charges in 10 min) | Always |
| Payout / withdrawal / cash-out | Always |
| Password change or 2FA reset | Yes (account takeover signal) |
| Profile change (address, email, phone) | Yes |
| Read-only actions (browsing, viewing invoice) | No |

Pass everything relevant: session fingerprint, device ID, IP, user agent, the transaction, the full customer record, recent behavior. Under-signaling is the #1 reason provider models underperform.

---

## Call pattern — sync vs async

**Synchronous** (blocks the user response): for charge attempts and withdrawals. Latency budget typically 200–500ms. Timeout aggressively (300ms); on timeout, fall back to a pre-configured default verdict (see below).

**Asynchronous** (fire-and-forget): for signals the provider uses to update its model but you don't need a verdict for (page views, session data, low-risk events). Queue to the provider via a worker.

Example synchronous call (TypeScript / Sift-style):

```ts
async function scoreCharge(ctx: Ctx, charge: Charge): Promise<Verdict> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300);
  try {
    const r = await fetch("https://api.sift.com/v205/events", {
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify({
        $type: "$create_order",
        $api_key: process.env.SIFT_KEY,
        $user_id: charge.customer_id,
        $order_id: charge.id,
        $amount: charge.amount_micros,
        $currency_code: charge.currency,
        $session_id: ctx.session_id,
        $ip: ctx.source_ip,
        return_score: true,
      }),
    });
    return parseVerdict(await r.json());
  } catch (e) {
    logger.warn("fraud.score.timeout", { charge_id: charge.id });
    return fallbackVerdict(charge);  // deterministic, conservative default
  } finally {
    clearTimeout(timer);
  }
}
```

Fallback verdict on timeout should match your risk appetite: for a high-value withdrawal, default to "review"; for a $5 charge from a long-tenured customer, default to "approve".

---

## Verdict handling

Providers return a risk score (0–100 typically) and sometimes a verdict (`approve` / `review` / `reject`). Translate into three deterministic actions.

| Score band | Action | Notes |
|------------|--------|-------|
| 0–40 (low) | Approve | Process normally |
| 41–75 (medium) | Step-up | Add friction: 3DS challenge, OTP, email verification, or hold-for-review depending on type |
| 76–100 (high) | Reject | Do not process. Return a generic error to the client. |

Thresholds are product decisions, not engineering decisions — calibrate them with the fraud analyst / compliance operator using historical data. Engineers own the plumbing; thresholds live in a config the ops team can tune without a deploy.

```yaml
# fraud-thresholds.yaml (feature-flag or remote config backed)
charge:
  approve_below: 40
  reject_above: 75
payout:
  approve_below: 25     # stricter: money leaving is higher risk
  reject_above: 60
signup:
  approve_below: 50
  reject_above: 85
```

---

## The uncertain verdict — manual review queue

Medium-band verdicts (`review`) are the hardest part. You cannot make users wait for a human, and you cannot silently approve. Three options:

1. **Step-up authentication in-band.** Trigger a 3DS2 challenge or OTP to the registered phone. If passed, approve. If failed, reject. Good for card-not-present transactions.
2. **Hold-for-review.** Accept the payment intent but delay capture. Queue the transaction for manual review. Notify the user "Payment pending review" with an expected SLA (often 1 business day). Good for marketplace payouts and high-value transfers.
3. **Conditional approval with reversal window.** Approve now, review within 24 hours, reverse if fraudulent. Only appropriate for reversible actions (internal credits, not card charges where reversal has fees).

### Manual review queue design

Dedicated queue, separate from general ops. Fraud reviewers need:

- The transaction with full context (customer history, device, IP, amount, counterparty)
- The provider's score and the top contributing risk signals
- Previous decisions on this customer (approvals, rejections, charges-back rate)
- Action buttons: approve / reject / escalate / mark-as-fraud
- An SLA timer — how long until auto-action fires if no human acts

Schema sketch:

```sql
CREATE TABLE fraud_review_queue (
    queue_id       BIGSERIAL PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    customer_id    TEXT NOT NULL,
    risk_score     SMALLINT NOT NULL,
    risk_signals   JSONB NOT NULL,            -- provider's top reasons
    state          TEXT NOT NULL,             -- pending|in_review|approved|rejected|escalated|timeout
    sla_deadline   TIMESTAMPTZ NOT NULL,
    reviewer_id    TEXT,
    decision_at    TIMESTAMPTZ,
    decision_note  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_review_state_sla ON fraud_review_queue (state, sla_deadline);
```

Auto-action on SLA breach: for most teams, default to "reject and notify customer to contact support". Better a false reject than a silent approval that turns into a chargeback 60 days later.

---

## Feedback loop — keeping the model honest

Provider models improve when you tell them which verdicts were right and wrong. Every chargeback, every confirmed fraud case, every false positive the human queue overturned — all go back to the provider.

- **Chargeback webhook → provider feedback.** When a chargeback comes in, call the provider's `$chargeback` or `$order_status` API with the dispute outcome. This is the most important signal.
- **Manual review decisions → provider labels.** When a reviewer marks a transaction as fraudulent or legitimate, push that label to the provider.
- **Customer-reported fraud → provider.** If a customer reports fraud via support (card stolen, unauthorized charge), push the label.

```ts
await siftClient.labelUser({
  userId: customer_id,
  isBad: true,
  reasons: ["$chargeback"],
  description: "Dispute code 10.4 — fraud, card not present",
});
```

Cadence: every chargeback → feedback within 24 hours. Every manual decision → feedback at decision time. Batch label uploads for historical labeling at onboarding.

---

## Observability

Track these as SLOs:

- **Verdict latency p99** (sync calls): alarm if > 500ms sustained for 5 minutes.
- **Provider availability**: alarm if error rate > 1%.
- **Approval rate**: slow-moving; alarm on 10%+ week-over-week shift either direction (could indicate threshold drift or an attack).
- **Chargeback rate per 1,000 approved charges**: target < 0.5% (Visa/Mastercard warn at 0.9%, put you on monitoring at 1%).
- **Manual queue backlog**: alarm if > SLA breached on any item.
- **False positive rate**: rejected charges that were later recovered via support; track to tune thresholds.

---

## Provider selection — quick criteria

Full evaluation is a separate exercise; this is the quick take.

| Provider | Strength | Typical fit |
|----------|----------|-------------|
| Stripe Radar | Tight integration with Stripe payments; zero new vendor | Any team already on Stripe |
| Sift | General-purpose with strong signup/ATO coverage | Marketplaces, consumer apps |
| Signifyd | Chargeback guarantee — they pay if it gets through | E-commerce with high chargeback exposure |
| Kount | Strong in regulated / high-value verticals | Enterprise or regulated |

Avoid multi-provider unless volumes justify it. Running two fraud providers on every transaction doubles latency and cost without doubling accuracy.

---

## What to never do

1. **Reveal the fraud score to the customer.** Fraudsters iterate to beat the score. Return a generic error: "We were unable to process this payment. Contact support."
2. **Block an entire customer based on one high-risk transaction** without a human check. Account-level blocks should go through the manual review queue.
3. **Hard-code thresholds in code.** They will need to change during an incident; deploys are too slow.
4. **Call the provider inside a DB transaction.** Slow calls hold locks. Score first, then transact.
5. **Skip the feedback loop.** An un-trained model decays. Providers will cheerfully take your money while their accuracy drifts.
