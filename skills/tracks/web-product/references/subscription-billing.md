# Subscription billing for web products

## Overview

Most web products use Stripe. This reference covers the integration patterns that prevent billing bugs — double charges, stale entitlements, missed webhook events — rather than basic Stripe setup.

---

## Checkout flow (Stripe Checkout — recommended)

Stripe Checkout is a hosted page. You redirect the user to Stripe, Stripe handles the card form, and redirects back to your app. You never touch card data.

```typescript
// Create a Checkout session
const session = await stripe.checkout.sessions.create({
  mode: 'subscription',
  customer: user.stripeCustomerId ?? undefined,  // reuse existing customer if available
  customer_email: user.stripeCustomerId ? undefined : user.email,  // create new customer
  line_items: [{
    price: PLAN_PRICE_IDS[plan],  // your Stripe Price ID
    quantity: 1,
  }],
  subscription_data: {
    trial_period_days: 14,  // optional trial
    metadata: { workspaceId: workspace.id },  // attach your ID for webhook processing
  },
  success_url: `${baseUrl}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
  cancel_url: `${baseUrl}/billing`,
});

return redirect(session.url);
```

**On the success page:** do not fulfil the subscription from the success URL. The user could refresh the success page or share the URL. Instead, wait for the `checkout.session.completed` webhook to fulfil the subscription.

---

## Webhooks — the source of truth

The webhook is the authoritative signal for billing state changes. The checkout redirect is just UX.

**Setup:**

```typescript
// Verify the signature — never process without verification
const sig = req.headers['stripe-signature'];
let event: Stripe.Event;

try {
  event = stripe.webhooks.constructEvent(
    req.rawBody,  // must be raw bytes, not parsed JSON
    sig,
    process.env.STRIPE_WEBHOOK_SECRET,
  );
} catch (err) {
  return res.status(400).send(`Webhook signature verification failed: ${err.message}`);
}
```

**Idempotent processing — always deduplicate on `event.id`:**

```typescript
const existing = await db.stripeEvent.findUnique({ where: { id: event.id } });
if (existing) {
  return res.status(200).json({ received: true });  // already processed
}

// Process the event
await processStripeEvent(event);

// Mark as processed
await db.stripeEvent.create({ data: { id: event.id, type: event.type, processedAt: new Date() } });
```

**Return 200 quickly** — move heavy processing to a background job. Stripe retries events if you do not respond with 2xx within 30 seconds. If your webhook times out and Stripe retries, your idempotency check must handle it.

---

## Events to handle

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create subscription record, set plan, send welcome email |
| `invoice.payment_succeeded` | Extend subscription period, clear payment-failed state |
| `invoice.payment_failed` | Enter dunning state, send payment-failed email, restrict features after grace period |
| `customer.subscription.updated` | Plan change, quantity change, trial end → update local subscription record |
| `customer.subscription.deleted` | Subscription cancelled or failed past grace period → downgrade to free tier |
| `customer.subscription.trial_will_end` | Send trial-ending warning email (fires 3 days before trial ends) |
| `payment_method.attached` | Payment method added — useful for updating billing UI |

---

## Entitlements model

Do not hard-code plan names or feature flags in the UI. Build an entitlements layer.

```typescript
// Subscription → Plan → Features
type Plan = 'free' | 'pro' | 'team';

const PLAN_FEATURES: Record<Plan, Set<Feature>> = {
  free: new Set(['items:create', 'items:read']),
  pro: new Set(['items:create', 'items:read', 'items:export', 'api:access']),
  team: new Set(['items:create', 'items:read', 'items:export', 'api:access', 'team:members', 'advanced:reporting']),
};

async function getWorkspacePlan(workspaceId: string): Promise<Plan> {
  const sub = await db.subscription.findFirst({
    where: { workspaceId, status: { in: ['active', 'trialing'] } },
  });
  return sub?.plan ?? 'free';
}

async function hasFeature(workspaceId: string, feature: Feature): Promise<boolean> {
  const plan = await getWorkspacePlan(workspaceId);
  return PLAN_FEATURES[plan].has(feature);
}
```

**Enforce at the API layer, not only in the UI:**

```typescript
async function exportItems(ctx: RequestContext) {
  if (!await hasFeature(ctx.workspaceId, 'items:export')) {
    throw new UpgradeRequiredError('Export requires a Pro plan');
  }
  // proceed with export
}
```

**Cache the plan** but with a short TTL and invalidate on `customer.subscription.updated`:

```typescript
const plan = await redis.get(`workspace:${workspaceId}:plan`)
  ?? await getWorkspacePlanFromDB(workspaceId);
```

---

## Trial periods

```
1. User signs up → trial starts automatically (14 days)
2. Day 0:    Welcome email, prompt to add payment method (optional until day 11)
3. Day 11:   "Trial ending in 3 days" email (via customer.subscription.trial_will_end webhook)
4. Day 14:   Trial ends
   a. Has payment method → converts to paid subscription (invoice.payment_succeeded)
   b. No payment method → subscription moves to past_due or cancelled
5. After trial end with no payment → downgrade to free tier via customer.subscription.deleted
```

**Do not require a credit card to start a trial.** Conversion is higher without upfront payment details. Add the card requirement only when the trial is about to expire.

---

## Dunning flow (failed payment)

```
Day 0:  Payment fails → invoice.payment_failed webhook
        → Send "payment failed" email
        → Set workspace.paymentStatus = 'past_due'
        → Do NOT immediately restrict access (grace period)

Day 3:  Stripe retries (configurable in Stripe dashboard)
        → Another invoice.payment_failed webhook

Day 7:  Stripe retries again
        → Start restricting non-critical features

Day 14: Final retry fails → customer.subscription.deleted webhook
        → Downgrade to free tier
        → Send "subscription cancelled" email
```

**Grace period is good UX.** Users are not always fraudulent — cards expire, limits are hit. Give them 7 days to fix it before restricting access.

---

## Stripe Customer Portal

Let users manage their own subscription without you building a billing UI.

```typescript
const session = await stripe.billingPortal.sessions.create({
  customer: workspace.stripeCustomerId,
  return_url: `${baseUrl}/settings/billing`,
});

return redirect(session.url);
```

The portal handles: plan upgrades/downgrades, cancellations, payment method updates, invoice history. You just need to handle the resulting webhooks.

---

## Pricing tier design principles

- **Free tier:** enough to experience the core value, not enough to avoid paying
- **Pro tier:** removes the friction of the free tier (limits, export, API access)
- **Team tier:** collaboration features (multiple seats, shared workspaces, admin controls)
- **Seat-based pricing:** charge per active member in a workspace — natural expansion revenue
- **Usage-based pricing:** charge per unit consumed (API calls, exports, storage) — requires metering, use Stripe Meters

**Do not make free too generous** (users never upgrade) or too restrictive (users never activate).
