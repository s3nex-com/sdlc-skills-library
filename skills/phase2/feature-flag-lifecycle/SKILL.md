---
name: feature-flag-lifecycle
description: >
  feature flag, flag lifecycle, flag debt, flag cleanup, stale flags, release flag,
  flag registry, rolling out a flag, flag removal, dark launch, kill switch,
  gradual rollout, flag expiry, flag audit, feature toggle
---

## Purpose

Manages the full lifecycle of feature flags: deciding when to create one, naming it correctly, rolling it out safely, and — critically — removing it before it becomes permanent dead code. Flag debt is as real as any other technical debt: a flag that was "temporary" twelve months ago is now an invisible conditional that no one dares touch. This skill enforces a create-own-expire-remove discipline that keeps the codebase clean.

---

## When to use

- Merging an incomplete feature to main so it can ride the deployment train without being visible to users
- Gradual production rollout of a completed feature (0% → 10% → 100%)
- Dark launch: deploy and monitor a feature before any user can trigger it
- Kill switch: you need the ability to disable a risky integration without a deployment
- A/B experiment: route a subset of users to a different code path and measure the outcome
- Monthly flag audit: reviewing flags that have passed their expiry date or have no owner
- Removing a flag that has been at 100% for 14+ days

---

## When NOT to use

- **Environment differences** (dev vs staging vs prod): use environment variables or deployment config, not flags. A flag that is always on in one environment and always off in another is not a feature flag — it is a misconfigured env var.
- **Permanent configuration** (timeouts, thresholds, retry counts): use config files or a config service.
- **Access control** (who is allowed to use a feature at all): permission flags are managed in customer config, not in a release flag system — see the `devops-pipeline-governance` reference for the distinction.
- **Hiding broken features indefinitely**: if a flag has been off for 6+ months and the feature is not actively in development, delete both the flag and the dead code.

---

## Process

### Step 1 — Create the flag

1. Choose the flag type. This determines naming prefix, expected lifespan, and cleanup obligation:

   | Type | Prefix | Lifespan | Cleanup required? |
   |------|--------|----------|-------------------|
   | Release | `release_` | Days to 2 sprints after 100% | Yes — remove flag and else branch |
   | Experiment | `exp_` | Duration of A/B test | Yes — remove losing path |
   | Ops (kill switch) | `ops_` | Semi-permanent circuit breaker | No planned removal; review annually |
   | Permission | `perm_` | Until feature is GA and legacy dropped | Remove when legacy path is gone |

2. Name the flag: `{prefix}{feature_area}_{what_it_controls}`. Example: `release_device_onboarding_new_flow`.

3. Set an expiry date for `release_` and `exp_` flags at creation. If you cannot set an expiry date, you do not yet know what done looks like — figure that out first.

4. Add the flag to the flag registry (see Output format below).

5. Set the default value to `false` (off). The default is what happens when the flag service is unavailable — it should be the safe, known-working state.

### Step 2 — Implement

1. Read flag value from the flag service or environment. Never hardcode it in source or in tests.
2. Write parameterised tests for both flag states (on and off). Code that only passes with the flag on is not shippable.
3. Tag BDD scenarios that depend on the flag with `@flag:{flag_name}` and run the suite with each state in CI.

### Step 3 — Roll out

Follow the 0% → 1% → 10% → 50% → 100% ladder. At each step:
- Monitor error rate, latency, and the key business metric for 15–30 min
- If metrics degrade: step back to the previous percentage, investigate
- Do not skip steps for convenience — the blast radius is the point

### Step 4 — Monitor

- Alert if the flag is evaluated in an unexpected state (e.g. ops kill switch tripped unexpectedly)
- Track adoption rate at each rollout step so you know when 50% is genuinely stable
- Review flag expiry dates weekly (sprint planning is the natural moment)

### Step 5 — Remove

Trigger: flag is at 100%, stable for 14+ days (release) or experiment concluded (experiment).

1. Create a cleanup task. This is non-optional — put it in the current sprint.
2. Remove the flag check from every call site in the code.
3. Delete the else branch (the old behaviour). The goal is no conditionals, just the new path.
4. Remove tests that tested the old behaviour only.
5. Delete the flag from the flag service configuration.
6. Remove the entry from the flag registry.
7. PR should be small. If it is large, the flag was gating too much at once.

### Flag debt audit (monthly)

Run this check at the start of each month:
- Any `release_` or `exp_` flag past its expiry date gets a P1 cleanup task this sprint
- Any flag with no expiry date or no named owner is flag debt — assign an owner immediately
- Any `release_` flag at 100% rollout for 30+ days with no cleanup task is overdue

Write a CI test that fails if any release flag has been at 100% for more than 14 days. A failing test in CI cannot be quietly ignored the way a Jira ticket can.

---

## Output format

### Flag registry entry (YAML)

```yaml
flag: release_new_device_onboarding
type: release
owner: thanassis
created: 2025-11-01
expires: 2025-12-01
default: false
status: rolling-out (60%)
description: New 5-min onboarding flow for IoT devices. Replaces 12-step legacy wizard.
removal-criteria: stable at 100% for 14 days, no rollback events in 7 days
```

### Flag registry table (Markdown, for wikis or PR descriptions)

| Flag | Type | Owner | Created | Expires | Status |
|------|------|-------|---------|---------|--------|
| release_new_device_onboarding | release | thanassis | 2025-11-01 | 2025-12-01 | Rolling out (60%) |
| ops_email_notifications | ops | alice | 2025-06-01 | — | Active (on) |
| exp_dashboard_layout_v2 | experiment | bob | 2025-11-10 | 2025-12-10 | Active (50/50) |

### Cleanup task format

```
[cleanup] Remove release_new_device_onboarding flag
Flag has been at 100% since 2025-12-05. Remove:
  - flag check in device_onboarding_service.py:87
  - legacy WizardOnboardingFlow class and its tests
  - flag entry in unleash / flag config
  - row in flag-registry.yaml
Acceptance: no flag check exists in the codebase for this flag name
```

---

## Skill execution log

Append one line to `docs/skill-log.md` each time this skill fires:

```
[YYYY-MM-DD] feature-flag-lifecycle | outcome: OK|BLOCKED|PARTIAL | next: <next action> | note: <one-line summary>
```

Examples:
```
[2026-04-20] feature-flag-lifecycle | outcome: OK | next: monitor at 50% | note: created release_new_device_onboarding, rolling out
[2026-04-20] feature-flag-lifecycle | outcome: OK | next: done | note: monthly audit — 2 flags past expiry, cleanup tasks created
[2026-04-20] feature-flag-lifecycle | outcome: BLOCKED | next: needs owner assigned | note: 3 flags found with no owner; cannot set expiry without owner decision
```

---

## Reference files

`skills/phase2/feature-flag-lifecycle/references/flag-registry-template.md` — flag registry template in both YAML and Markdown table formats, ready to copy into a project.

`skills/phase2/devops-pipeline-governance/references/feature-flags-guide.md` — detailed reference covering flag types with code examples, testing patterns (parameterised tests, BDD tagging), CI enforcement (stale flag test), tooling options (LaunchDarkly, Unleash, Flipt, env vars), and how flags integrate with canary deployments.
