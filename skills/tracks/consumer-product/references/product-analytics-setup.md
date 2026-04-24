# Product analytics setup — instrumentation, identity, sanity checks

An analytics pipeline that emits noisy, inconsistent events is worse than no pipeline. Every wrong event corrupts a decision. Instrument with the same discipline you apply to production code: typed, tested, reviewed, monitored.

---

## Instrumenting events in code

Do not call the analytics SDK directly from feature code. Wrap it.

### The wrapper pattern

```ts
// analytics.ts — the only file that imports the vendor SDK
import { registry } from "./event-registry";

export function track<E extends EventName>(
  event: E,
  properties: EventProps<E>,
) {
  if (!registry[event]) {
    if (process.env.NODE_ENV !== "production") throw new Error(`unknown event ${event}`);
    return; // fail closed in prod — never crash on analytics
  }
  validate(registry[event], properties);
  enrichWithContext(properties); // session_id, experiment_assignments, etc.
  vendor.track(event, properties);
}
```

Benefits:
- Event names and property types are compile-time checked against the registry.
- Global context (session, experiment assignments, platform) is attached in one place.
- Swapping vendors (Segment → Mixpanel direct → Amplitude) is a one-file change.
- Analytics failures never crash the product.

### What NOT to instrument

- **Every render.** Instrument user-visible events that drive decisions.
- **Internal retries and implementation details.** If a button shows a loading spinner while the API retries, emit `cta_clicked` once, not on every retry.
- **PII.** Never pass names, emails, or free-text input as property values.
- **Secrets or tokens.** Obvious, but it still happens.

### Client-side vs server-side

| Emit from client | Emit from server |
|------------------|------------------|
| User interactions (clicks, views, scrolls) | Financial events (purchases, subscriptions) |
| Client-only state (video position, scroll depth) | Authoritative state changes (account created, subscription activated) |
| UI performance (TTI, LCP) | Events that must not be ad-blocked |

Critical funnel events (signup_completed, purchase_completed) should have a server-side source of truth. Client-side events are blocked by ad-blockers and VPNs at rates of 15–40% depending on audience; server-side emissions survive.

---

## Segment vs direct integration

### Segment (or Rudderstack / similar CDP)

**Pros:** one SDK integration, many downstream destinations, central routing and filtering, consent-management hooks, replay to new destinations.

**Cons:** added cost per MTU, extra latency, another point of failure, pricing scales uncomfortably as you grow.

### Direct integration (Amplitude SDK / Mixpanel SDK)

**Pros:** cheaper at scale, one less hop, richer vendor-specific features accessible.

**Cons:** vendor lock-in, harder to add a second destination later, consent handling lives in your code.

### Rule of thumb

- Early stage (< 100k MAU, one analytics destination): direct integration. Simpler.
- Growth stage (multiple destinations — warehouse + Amplitude + marketing): Segment. The routing saves more than it costs.
- Scale stage (millions of MAU, Segment bill is a line item): consider a self-hosted alternative or direct integration with a warehouse-first pattern.

The wrapper pattern above makes this choice reversible.

---

## Session tracking

A session is a bounded period of user activity. The definition must be stable across the codebase.

### Standard rules

- A session starts on the first event after 30 minutes of inactivity, or on app cold start.
- A session ends 30 minutes after the last event, or on app background (mobile) for more than 30 minutes.
- Every event within the session shares a `session_id`.
- Session start and end events are emitted: `session_started`, `session_ended`.

### What 30 minutes means

The 30-minute window is convention, not law. Pick a number that matches product usage patterns — 30 minutes is appropriate for social apps and marketplaces, 60+ minutes for long-form content consumption, 5–10 minutes for short-form.

Document the choice. Do not change it without migrating historical dashboards.

### Cross-device sessions

Do not try to stitch sessions across devices. A session is per-device. User-level analysis happens at the user level, not the session level.

---

## User identification across devices and auth states

### The four identity states

| State | `user_id` | `anonymous_id` | `device_id` |
|-------|-----------|----------------|-------------|
| Never signed in, first visit | null | new UUID | new UUID |
| Anonymous return visitor | null | persisted from storage | persisted |
| Signed-up user on same device | set on signup | same as pre-signup | same |
| Signed-in user on new device | set on login | new UUID on this device | new UUID |

### The anonymous → signed-in transition

This is the single most error-prone part of analytics. Get it wrong and you break every activation funnel.

On signup or login, call the vendor's `identify` or `alias` API to link the anonymous ID to the new user ID:

```ts
// before: user_id = null, anonymous_id = "a1b2..."
onSignupCompleted(() => {
  analytics.identify(newUserId, { anonymous_id: currentAnonymousId });
  // from now: user_id = newUserId, anonymous_id = "a1b2..." preserved
});
```

Consequences of missing this:
- The user's pre-signup events (landing view, feature exploration, signup start) are attributed to the anonymous ID.
- The user's post-signup events are attributed to the new user ID.
- Funnel analysis fragments the same real user into two rows.

Always verify the identify call with a post-signup smoke test on a real install before launch.

### Cross-device stitching

The only reliable cross-device link is the authenticated `user_id`. Anonymous cross-device stitching is best-effort at best; do not rely on it for experiment analysis. If a feature must analyse cross-device behaviour, require auth before the first event is emitted.

---

## Sanity checks

Every new event goes through sanity checks before it is trusted for decisions.

### Volume checks

- **Is it emitting at all?** Query the last hour for at least one event. Zero emissions is a bug.
- **Is volume plausible?** Compare to related events. If `video_played` fires 1000x/hour and `video_paused` fires 3x, the pause instrumentation is broken.
- **Is volume stable across platforms?** iOS : Android : Web ratios should match your DAU split. Large deviations point to platform-specific instrumentation bugs.
- **Are there suspicious spikes?** A 100x spike in the middle of the night is a bot or a retry storm.

### Property completeness

For each required property, compute the percentage of events where the property is non-null and type-correct. Target: ≥99%. Anything below 95% means the instrumentation is broken somewhere.

### Experiment assignment coverage

For users in an active experiment, the percentage of their events that carry `experiment_assignments` with the expected key must be ≥99%. If it is lower, the flag SDK is not fully initialised before the event is fired — almost always a race condition.

### SRM check on day one

For every running experiment, chi-square test the assignment split against the configured ratio. A significant SRM on day one invalidates the experiment; fix the assignment pipeline before interpreting any results.

### Automated checks — not manual

Sanity checks are scheduled jobs that run daily, not things a human remembers to do. Output goes to the same alerting channel as production incidents. An analytics outage is a product outage.

---

## The instrumentation definition of done

A feature is not shipped until:

1. Every event in the design doc is instrumented and registered.
2. Every event is emitting in staging with ≥99% required-property completeness.
3. `experiment_assignments` is populated for the feature's flag if the feature is experimental.
4. The anonymous → signed-in identify path has been smoke-tested end to end.
5. The relevant dashboard or funnel query returns non-zero rows.
6. Sanity-check jobs are configured and alerting.

No instrumentation, no ship.
