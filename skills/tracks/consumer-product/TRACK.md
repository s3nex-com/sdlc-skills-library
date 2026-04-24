---
name: consumer-product
description: >
  Activates when the user mentions A/B test, experiment, split test, variant, product
  analytics, event tracking, funnel analysis, Amplitude, Mixpanel, Heap, PostHog,
  Segment, referral, viral loop, growth feature, consumer, B2C, end user, push
  notification engagement, or retention metric. Also triggers on explicit
  declaration: "Consumer product track" or "Consumer track".
---

# Consumer product track

## Purpose

This track covers B2C products where the user is an individual consumer, success is measured by engagement and retention rather than contractual uptime, and the team ships many small bets protected by experiments and feature flags. Consumer product work has a distinct shape the base library does not encode: every feature is a hypothesis, the hypothesis is tested on live users under a flag, statistical discipline is not optional, analytics instrumentation is part of the definition of done, and consent for that instrumentation is a legal precondition.

The track covers the full breadth of consumer product work — not just A/B testing. Experimentation is the backbone, but the track also handles: notification pipelines (push, in-app, email) where unsubscribe compliance and delivery timing are first-class concerns; content feeds and recommendation surfaces where caching and personalisation strategy determine product quality; viral and referral mechanics where idempotency of invite-claim flows prevents double-attribution; and consumer-scale performance where a 200ms regression in time-to-interactive costs measurable retention. These patterns are invisible in the base library and must be made explicit.

The failure mode this track prevents is shipping on vibes — a feature launched because it felt right, instrumented after the fact, and rolled out without a rollback path. In consumer product, that class of failure compounds: every bad ship teaches the team nothing, every good ship gets no credit, and the product drifts. Experimentation rigor is the corrective — but it only works if the product surface is observable, performant, and reachable by the users the experiment is trying to measure.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "A/B test", "experiment", "split test", "variant", "treatment vs control", "holdout"
- "product analytics", "event tracking", "funnel analysis", "activation funnel"
- "Amplitude", "Mixpanel", "Heap", "PostHog", "Segment", "Rudderstack"
- "referral", "viral loop", "growth feature", "invite flow", "share flow"
- "consumer", "B2C", "end user", "app store", "DAU / MAU", "WAU"
- "push notification", "push campaign", "notification inbox", "in-app notification", "notification engagement", "unsubscribe", "opt-out"
- "retention metric", "day-7 retention", "day-30 retention", "re-engagement"
- "cohort", "stickiness", "activation rate", "aha moment", "time to value"
- "paywall", "upgrade funnel", "subscription", "freemium", "trial conversion"
- "content feed", "recommendation", "personalisation", "ranked feed", "algorithm"
- "social feature", "follow", "like", "share", "comment", "user-generated content"
- "viral coefficient", "k-factor", "network effect", "invite tree"

Or when the system under discussion has these properties:

- A user-facing product where the unit of value is an individual end consumer
- A culture of shipping behind flags and measuring lift before rolling out
- Engagement, retention, or monetisation as the primary success metric
- A product analytics pipeline (Segment / warehouse / Amplitude-style tool) already in place or being built
- A growth function distinct from sales (no account executives, no enterprise contracts)

---

## When NOT to activate

Do NOT activate this track when:

- The product is sold to businesses — use SaaS B2B track instead
- The product is a purely internal tool used only by employees — no track needed
- Experimentation is explicitly not part of the team's culture and the team ships without flags — fix that before activating; experimentation rigor is a precondition here, not an output
- The work is infrastructure or platform with no end-user surface — no track needed
- The primary risk is regulatory (HIPAA, FedRAMP) and the consumer surface is incidental — use the regulatory track as primary; add this only if analytics and experimentation are also in scope

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| feature-flag-lifecycle | Standard | Mandatory | Mandatory + experiment flags | Mandatory + experiment flags + statistical review |
| accessibility | Standard | Mandatory | Mandatory | Mandatory + annual audit |
| comprehensive-test-strategy | Standard | Standard | Standard + A/B test scenarios | Standard + A/B + client-side testing |
| data-governance-privacy | Mandatory | Mandatory | Mandatory + analytics consent | Mandatory + granular consent |
| observability-sre-practice | Standard | Standard + funnel metrics | Standard + product metrics | Standard + cohort analysis |
| caching-strategy | N/A | Advisory | Mandatory (feed and recommendation caching strategy required; cache poisoning invalidates A/B assignment) | Mandatory |
| performance-reliability-engineering | Standard | Advisory | Mandatory (consumer-scale p50/p95 targets documented and verified post-deploy) | Mandatory + load test at projected peak |

Skills not listed keep their default mode behaviour. A cell reading "Mandatory + X" means the skill fires AND X is required for the stage gate to pass. "Experiment flags" means flags tied to a running experiment's result and either graduated (winner rolled out, flag removed) or rolled back, distinct from long-lived release or ops flags.

The elevations encode six assertions specific to consumer product work:

1. **Feature-flag discipline scales with mode.** A Nano change still has a flag. A Rigorous change has a flag, a pre-registered experiment, and a statistical review signed off by a named analyst before the graduation decision.
2. **Accessibility is non-negotiable from Lean upwards.** Consumer products face broad audiences and consumer-protection regimes (ADA in the US, EN 301 549 in the EU, AODA in Ontario). An inaccessible consumer feature is a liability, not a trade-off.
3. **A/B test scenarios are test scenarios.** From Standard mode, `comprehensive-test-strategy` covers the variant matrix — rendering the treatment path, rendering the control path, and the assignment code itself. Rigorous adds client-side testing discipline (visual regression, analytics emission verification under real device conditions).
4. **Analytics consent is a data-governance obligation, not a cookie banner.** From Standard, the PIA must name the consent category for each event and the gating mechanism. Rigorous requires granular, per-purpose consent with a defensible audit trail.
5. **Cache poisoning invalidates experiments.** `caching-strategy` at Standard+ is required because a shared cache key that serves different users the same cached response silently breaks A/B assignment — a user in the treatment group sees the control experience because someone else's cached response was served. Per-user or per-segment cache keys are required on any surface covered by an active experiment.
6. **Consumer-scale latency is a retention variable.** `performance-reliability-engineering` at Standard+ is required because in B2C products, p95 API response time directly predicts bounce rate, and a regression in time-to-interactive on the feed or notification surface costs measurable retention. Performance targets must be documented at design time and verified after deploy.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | Experimentation plan required if the feature is experimental. The plan names the null hypothesis, the primary success metric with its minimum detectable effect, the guardrail metrics, the sample size, and the planned experiment duration. Non-experimental features must state why they bypass experimentation. |
| Stage 2 (Design) | Event taxonomy defined. The design doc lists every event to be tracked, its required and optional properties, the naming convention applied (noun_verb or verb_noun; one convention per codebase), and where each event sits in the funnel. |
| Stage 3 (Build) | Feature flag in place before code merges to main. Events instrumented and verified in a staging analytics environment. An event sanity check (non-zero volume, property completeness) runs before the flag is enabled for any traffic above 1%. |
| Stage 5 (Ship) | Ramp plan documented: 1% → 10% → 50% → 100% with a defined hold time at each step and explicit guardrail thresholds that trigger rollback. Kill switch verified by actually toggling the flag off in a pre-production environment before the 1% ramp begins. |
| Phase 3 (Ongoing) | Weekly experiment review: every running experiment reviewed for peeking discipline, SRM, guardrail breaches, and stop/continue/ship decision. Stale flag cleanup per `feature-flag-lifecycle` cadence — experiment flags older than the experiment's planned duration + 2 weeks are escalated. |

Strictest-wins applies if another active track modifies the same gate. Common interactions:

- With **SaaS B2B track**: the ramp plan is per-tenant-tier, not per-user-percentage. Free-tier tenants ramp first, enterprise last. Both gates apply — tier ramp and percentage ramp are layered.
- With **Healthcare** or **Regulated**: experimentation is allowed only on non-regulated surfaces. The experimentation plan must explicitly carve out regulated data flows.
- With **Mobile**: the ramp plan accounts for app-store staged rollout percentages separately from server-side flag percentages. Two ramps, both documented.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| feature-flag-lifecycle | `references/ab-testing-design.md`, `references/experiment-statistics.md` |
| comprehensive-test-strategy | `references/ab-testing-design.md` |
| data-governance-privacy | `references/event-taxonomy.md`, `references/product-analytics-setup.md` |
| observability-sre-practice | `references/event-taxonomy.md`, `references/experiment-statistics.md` |
| code-implementer | `references/event-taxonomy.md`, `references/product-analytics-setup.md` |
| design-doc-generator | `references/ab-testing-design.md`, `references/event-taxonomy.md`, `references/product-analytics-setup.md` |
| prd-creator | `references/ab-testing-design.md`, `references/experiment-statistics.md` |
| release-readiness | `references/ab-testing-design.md`, `references/experiment-statistics.md` |
| caching-strategy | `references/feed-caching.md` — feed and recommendation cache key design; A/B experiment integrity; per-user cache key scoping requirement |
| performance-reliability-engineering | `references/notification-design.md`, `references/feed-caching.md` — consumer-scale p50/p95 targets for feed and notification surfaces; latency regression is a retention variable |

Specific guidance the injection encodes:

- When `feature-flag-lifecycle` fires, distinguish experiment flags (temporary, tied to experiment result, removed after graduation or rollback) from release flags (temporary, tied to a deploy, removed after stability) and ops flags (long-lived, kill switches and configuration toggles). Each class has a different expiry and a different owner.
- When `data-governance-privacy` fires, ensure analytics consent is covered in the PIA. CCPA, GDPR, and ePrivacy impose different consent regimes; the PIA must name which apply and how the consent state gates event emission.
- When `observability-sre-practice` fires, product metrics (activation, day-1 / day-7 / day-30 retention, referral rate, revenue per user) sit alongside technical SLIs (latency, error rate, saturation). The same dashboards, not two separate systems.
- When `comprehensive-test-strategy` fires in Standard+ mode, the test matrix covers both the treatment and control code paths plus the assignment logic itself. Do not ship variant code that has never been exercised in CI.
- When `prd-creator` and `design-doc-generator` fire, the experimentation plan and event taxonomy sections are required outputs. The orchestrator refuses to advance Stage 1 → Stage 2 without them.
- When `release-readiness` fires, the ramp plan and kill-switch verification artefacts are required evidence. A launch without a documented rollback path fails the gate.

---

## Reference files

- `references/ab-testing-design.md` — experiment design. Null hypothesis, success and guardrail metrics, sample size and power, A/B vs multi-armed bandit vs pre-post, common pitfalls (peeking, novelty, multiple comparisons, SRM, stratification), worked sample size calculation, pre-launch checklist.
- `references/experiment-statistics.md` — frequentist vs Bayesian. Confidence intervals, effect size, power, run duration. Stopping rules, sequential testing, and CUPED for variance reduction.
- `references/event-taxonomy.md` — naming conventions (noun_verb or verb_noun, one only), hierarchical categorisation, required vs optional properties, property schema, governance for adding an event, worked taxonomy for a consumer app.
- `references/product-analytics-setup.md` — instrumenting events in code, Segment vs direct integration trade-offs, session tracking, user identification across devices and across the anonymous → signed-in transition, sanity checks on event volume and property completeness.
- `references/notification-design.md` — push/in-app/email notification pipeline design, consent and compliance (GDPR, CAN-SPAM, unsubscribe), fanout patterns, delivery idempotency, frequency caps, A/B testing notification content, notification metrics.
- `references/feed-caching.md` — content feed caching architecture, per-user/per-segment cache key design, A/B experiment integrity (cache poisoning prevention), write-time fanout vs read-time compute trade-offs, CDN vs application cache, state stores for streaming feeds, performance targets.
- `references/viral-mechanics.md` — invite flow design (creation, distribution, acceptance, reward), double attribution prevention, fraud and abuse vectors, k-factor measurement SQL, network effect activation funnel, minimal invite DB schema.

---

## What good looks like

A Standard-mode Consumer-track feature reaches the ship gate with:

- A one-page experiment design in the PRD naming hypothesis, metric, MDE, guardrails, sample size, duration, and stop rule.
- A flag in the flag system with owner, expected expiry date (experiment end + 2 weeks), and a tested kill switch.
- An event schema registered before the first user sees the treatment.
- A dashboard query that returns non-zero rows in staging and a sanity-check job configured for production.
- A ramp plan in the release doc: 1% → 10% → 50% → 100% with hold times and guardrail thresholds.
- A named decision-maker and a calendar invite for the review at the planned stop point.

A Rigorous-mode feature adds: a pre-registered statistical analysis plan, a statistical review by a named analyst, and an annual accessibility audit covering the feature's surface.

---

## What bad looks like

The failure patterns this track exists to block:

- A feature shipped behind a flag with no experiment — the team ships to 100% on the first sign of "looking good" without a stop rule.
- Instrumentation added after launch because "we forgot to track that". The funnel now has a gap nobody can fill retroactively.
- Events named inconsistently across platforms — `signup_completed` on web, `SignupCompleted` on iOS, `signup_complete` on Android. Every funnel query becomes a union.
- Experiment assignments not attached to events, so the A/B analysis is impossible and the team argues about which variant a user was in.
- A flag still live six months after the experiment ended, forked code paths decaying in parallel, nobody remembers which variant won.
- A cookie banner that says "we use cookies" with no connection to the consent state the analytics SDK actually reads.

Each of these is a gate failure under this track.

---

## Typical session flow

A feature starting from an idea and moving through this track:

1. **Idea arrives.** `prd-creator` fires with the ab-testing-design and experiment-statistics references injected. The PRD is not accepted until it carries the experimentation plan or a written opt-out.
2. **Design stage.** `design-doc-generator` fires with the event-taxonomy and product-analytics-setup references. The design doc names every event, the properties, and the funnel shape the team will monitor.
3. **Build stage.** `feature-flag-lifecycle` fires with the ab-testing-design and experiment-statistics references — the flag must be classified (experiment vs release vs ops) and the experiment flag carries its experiment id. `code-implementer` fires with the taxonomy and setup references, ensuring new events go through the wrapper and the schema registry.
4. **Verify stage.** `comprehensive-test-strategy` fires with the ab-testing-design reference. Test cases cover both variants and the assignment code. Analytics instrumentation is smoke-tested in staging.
5. **Ship stage.** `release-readiness` fires with the ab-testing-design and experiment-statistics references. The ramp plan, kill-switch verification, and decision calendar are required evidence.
6. **Ongoing.** `feature-flag-lifecycle` runs the weekly stale-flag sweep. `observability-sre-practice` fires with the event-taxonomy and experiment-statistics references; the weekly experiment review runs off its dashboards.

---

## Ownership and escalation

Inside a small team, ownership is named, not delegated:

- **Experiment design owner:** the PM or engineer proposing the feature. Owns the plan end-to-end.
- **Taxonomy owner:** one named person per codebase (usually the senior engineer closest to analytics). Approves new events, rejects duplicates, owns the registry.
- **Statistical reviewer (Rigorous mode only):** a named analyst or senior engineer with statistical training. Signs off on the analysis plan and the final decision.
- **Kill-switch operator:** on-call engineer. Knows where the flag lives and how to toggle it at 2am.

Escalation path for a guardrail breach during ramp: on-call engineer flips the kill switch first, posts the incident second, runs the postmortem third. No debate about statistical significance during a breach — the kill switch is the debate-resolution tool.

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: consumer-product | mode: <Mode> | duration: project
```

Skill firings under this track append the track context:

```
[YYYY-MM-DD] feature-flag-lifecycle | outcome: OK | note: experiment flag created for onboarding-v2 | track: consumer-product
[YYYY-MM-DD] data-governance-privacy | outcome: OK | note: analytics consent PIA updated | track: consumer-product
```
