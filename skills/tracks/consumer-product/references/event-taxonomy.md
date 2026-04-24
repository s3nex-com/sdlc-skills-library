# Event taxonomy — naming, schema, and governance

An event taxonomy is a contract. Once an event is emitted at volume, renaming it breaks every downstream dashboard, funnel, and experiment. The taxonomy is a product surface, not an implementation detail. Design it deliberately or pay for it later.

---

## Naming convention — pick one

Use **one** convention across the entire codebase. The two defensible choices:

### Option A: `object_action` (noun_verb)

```
video_played
video_paused
signup_completed
referral_sent
cart_updated
```

Sorts alphabetically by domain — all `video_*` events cluster together. Easier to browse in analytics tools. This is the convention most tools default to.

### Option B: `action_object` (verb_noun)

```
played_video
completed_signup
sent_referral
updated_cart
```

Reads like English. Sorts by action — all `completed_*` events cluster. Better when you want funnel steps to read naturally (`viewed_landing`, `clicked_cta`, `completed_signup`).

Pick one. Document it in the repo. Reject PRs that mix conventions. Mixing `signup_completed` and `viewed_landing` in the same product is the single most common taxonomy failure; it makes funnels painful to assemble.

### Rules that apply to both

- **Snake_case only.** No camelCase, no spaces, no hyphens.
- **Past tense for actions that have happened** (`signup_completed`, not `signup_complete`).
- **No tool names or implementation details** (`stripe_checkout_opened` is wrong; `checkout_opened` with a `payment_provider: stripe` property is right).
- **No PII in event names.** Ever.
- **No environment markers** (`prod_signup_completed` is wrong; use a property or a separate workspace).

---

## Hierarchical categorisation

Group events by product area using a consistent prefix (`auth_*`, `video_*`, `social_*`) or a `category` property. Prefix style is easier to grep and clusters in the analytics UI. Property style is easier to rename categories later. Pick one, document it.

---

## Required vs optional properties

Every event has two property tiers:

### Global required properties — emitted on every event

| Property | Type | Source | Notes |
|----------|------|--------|-------|
| `user_id` | string or null | auth state | null for anonymous users |
| `anonymous_id` | string | client SDK | stable per device, survives logout |
| `session_id` | string | client SDK | resets on 30-min inactivity or app restart |
| `timestamp` | ISO-8601 | client clock, server reconciled | |
| `platform` | enum | client | `web`, `ios`, `android`, `backend` |
| `app_version` | string | build | semver |
| `device_id` | string | client | stable install id |
| `locale` | string | client | `en-US` |
| `experiment_assignments` | map<string, string> | flag SDK | `{ "checkout_redesign_v2": "treatment" }` |

`experiment_assignments` is non-negotiable. Without it, A/B test analysis is impossible at the event level.

### Per-event required properties — enforced by schema

Every event declares its required properties. Example for `video_played`:

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| `video_id` | string | yes | stable id, not title |
| `video_duration_sec` | int | yes | |
| `video_category` | string | yes | enum: `tutorial`, `marketing`, `user_generated` |
| `autoplay` | bool | yes | |
| `playback_position_sec` | int | yes | 0 on first play, resume point on resume |
| `playlist_id` | string | no | null if single-video context |

### Optional properties — allowed but not enforced

Anything that adds context but is not required for analysis. Keep the list short; every optional property is a future debate.

---

## Property schema — worked conventions

- **Types are fixed** across all emissions of an event. `video_duration_sec` is always an int, never a string. Schema-drift bugs break downstream at the worst time.
- **Units in the name.** `video_duration_sec` not `video_duration`. `price_usd_cents` not `price`. Never make the consumer guess.
- **IDs are strings, not integers.** Analytics tools coerce types inconsistently; strings round-trip cleanly.
- **Enums are closed sets.** Document the allowed values; reject unknown values at the schema check, not silently.
- **No free-text properties** unless there is a specific analytic use. Free text generates infinite cardinality and kills query performance.
- **Booleans are booleans**, not `"true"` / `"false"` strings.
- **Currency has a currency code.** `price_amount: 499, price_currency: "USD"`. Never `price: 4.99`.

---

## Worked taxonomy — a consumer video app

```
# Auth
auth_signup_started           { method }
auth_signup_completed         { method, referral_code? }
auth_login_succeeded          { method }
auth_login_failed             { method, reason }

# Onboarding
onboarding_step_viewed        { step_index, step_name }
onboarding_step_completed     { step_index, step_name, duration_sec }
onboarding_completed          { total_duration_sec }

# Content
content_opened                { content_id, source, slot_index? }
video_played                  { video_id, autoplay, playback_position_sec }
video_paused                  { video_id, playback_position_sec, duration_watched_sec }
video_completed               { video_id, duration_watched_sec }

# Social
referral_link_shared          { channel }
referral_accepted             { referral_code, new_user_id }

# Monetisation
subscription_purchase_started   { plan_id, price_amount_cents, price_currency }
subscription_purchase_completed { plan_id, price_amount_cents, price_currency, transaction_id }
subscription_purchase_failed    { plan_id, reason }

# Engagement
notification_opened           { type, campaign_id? }
notification_disabled         { type }
```

Every event has a one-line docstring in the taxonomy registry explaining when it fires and who consumes it.

---

## Governance — who can add an event

Uncontrolled event creation is how you end up with `video_played`, `played_video`, `VideoPlayed`, and `vid_play` all live in production. Governance is the antidote.

### Roles

- **Instrumentation engineer:** proposes a new event. Writes the schema entry, the docstring, and the downstream consumer list.
- **Taxonomy owner:** one named person per team (typically the product analyst or a senior engineer). Reviews and approves.
- **Consumers:** data team, growth team, any team that owns a dashboard that this event might feed.

### Process

1. PR adding a new event must include: event name, properties schema with types, docstring, the dashboard or experiment that will use it, the consent category it falls under.
2. Taxonomy owner reviews against the naming convention, checks for duplicates and near-duplicates, confirms the schema types match existing patterns.
3. Merge triggers a schema registry update. The client SDK wrapper rejects events that do not match the registry in CI and warns in production.
4. Events are deprecated, not deleted. Deprecation means the event is marked stale in the registry, new code does not emit it, dashboards migrate off it, and after a grace period (typically 90 days) emissions are alerted on.

### What gets rejected

- Event names that violate the convention.
- Properties that duplicate existing properties under a different name.
- Free-text properties with no bounded cardinality.
- Events emitted at a frequency that would overwhelm the pipeline (more than ~1 event per user per second sustained) without batching.
- Events that leak PII in property values.

The registry is the source of truth. If the registry and the code disagree, the registry wins and the code is broken.
