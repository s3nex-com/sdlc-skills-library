---
name: mobile
description: >
  Activates when the user mentions iOS, Android, React Native, Flutter, Swift,
  Kotlin, Xcode, Android Studio, App Store, App Store Connect, Play Console,
  Play Store, TestFlight, internal testing track, mobile app release, app
  version, app update, push notification, APNS, FCM, offline-first, offline
  mode, sync engine, or native mobile. Also triggers on explicit declaration:
  "Mobile track".
---

# Mobile track

## Purpose

This track covers native and cross-platform mobile applications — iOS, Android, React Native, Flutter — where the product ships as an app to end-user devices through Apple's App Store or Google's Play Store. Mobile has a distinct shape the base library does not encode: a store review gate the team cannot bypass, users running arbitrary OS versions from the last four years, unreliable networks as the default assumption, battery and memory as first-class budgets, and a release pipeline that is measured in days rather than minutes. Running a mobile project in the default library leaves offline behaviour, store submission, and crash-free rate implicit. The track makes them explicit and blocks the pipeline when they are missed.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "iOS", "iPhone", "iPad", "Swift", "SwiftUI", "UIKit", "Xcode"
- "Android", "Kotlin", "Jetpack Compose", "Android Studio"
- "React Native", "Flutter", "Expo"
- "App Store", "App Store Connect", "TestFlight", "expedited review"
- "Play Store", "Play Console", "internal testing track", "closed testing"
- "mobile app release", "app version", "app update", "phased rollout"
- "push notification", "APNS", "FCM", "silent push", "notification permission"
- "offline-first", "offline mode", "sync engine", "local-first"
- "IAP", "in-app purchase", "StoreKit", "Play Billing"
- "cold start", "frame rate", "jank", "ANR", "crash-free users"

Or when the system under discussion has these properties:

- A binary artefact distributed through a platform store
- A minimum supported OS version policy
- A user base on devices the team does not control
- A release cadence gated by external review

---

## When NOT to activate

Do NOT activate this track when:

- The product is a mobile-optimised website, PWA, or responsive web app — that is web work; use the Consumer track if applicable
- The product is a desktop app (macOS, Windows, Linux) — store concerns exist but differ enough to need a separate track; no track is the current default
- The project is a mobile SDK for other apps — library concerns dominate; use the Open source track if distributed publicly
- The work is a backend service consumed by mobile clients with no mobile code in scope — standard mode is sufficient
- The mobile app is a thin wrapper over a web view with no native code and no store-specific behaviour — treat as web

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| feature-flag-lifecycle | Mandatory | Mandatory (remote config) | Mandatory | Mandatory |
| accessibility | Standard | Mandatory | Mandatory | Mandatory + platform a11y audit |
| performance-reliability-engineering | Standard | Mandatory (cold start + frame rate) | Mandatory + crash-free rate | Mandatory + crash-free rate + battery |
| release-readiness | Standard | Mandatory (store submission) | Mandatory + phased rollout | Mandatory + phased rollout + rollback |
| observability-sre-practice | Standard | Mandatory (crash reporting) | Mandatory + ANR + perf | Mandatory + per-device-class |
| data-governance-privacy | Mandatory | Mandatory (app privacy labels) | Mandatory | Mandatory |
| cloud-cost-governance | N/A | Advisory | Advisory | Mandatory (store distribution costs + CDN delivery costs for large binaries) |

Skills not listed keep their default mode behaviour. A cell reading "Mandatory + X" means the skill fires AND X is required for the stage gate to pass.

Notes on the additional elevation:

- `cloud-cost-governance` at Rigorous covers the cost surface specific to mobile distribution: CDN delivery costs for large app binaries and OTA update payloads, push notification delivery costs at scale, and remote config / feature flag evaluation costs. At most mode levels this is advisory because the cost is small; at Rigorous (high-scale, regulated mobile apps) these costs become material and must be attributed per-feature.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 2 (Design) | Offline behaviour must be explicit — what works with no connectivity, what degrades, what blocks. Sync reconciliation strategy chosen (last-write-wins, CRDT, user-intervention) and named in the design doc. Cold-start budget stated (target < 1.5s to first meaningful paint). |
| Stage 4 (Verify) | Tested on minimum supported OS versions (not just latest). At least one low-end device class covered (3-year-old mid-range Android; oldest supported iPhone). Airplane mode scenario tested for every screen that fetches data. |
| Stage 5 (Ship) | App store review lead time accounted for in the release plan (1–3 days typical, longer for new apps and first-time submissions). Phased rollout plan documented — start ≤ 10% and halt criteria defined. Remote kill switch (feature flag via remote config) present for every risky feature; no feature ships without a flag if it touches payments, auth, or data sync. |
| Phase 3 (Ongoing) | Weekly crash-free rate review; alert threshold: crash-free users < 99.5% on any supported OS. Minimum supported OS version reviewed quarterly — drop the oldest when its install base falls below 2%. |

Strictest-wins applies if another active track modifies the same gate.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| feature-flag-lifecycle | `references/mobile-version-management.md` |
| release-readiness | `references/app-store-approval-cycles.md`, `references/mobile-version-management.md` |
| accessibility | (platform audit guidance — VoiceOver + Dynamic Type on iOS, TalkBack + font scaling on Android — applied inline) |
| performance-reliability-engineering | `references/mobile-performance.md` |
| observability-sre-practice | `references/mobile-performance.md` |
| data-governance-privacy | `references/app-store-approval-cycles.md`, `references/push-notification-design.md` |
| design-doc-generator | `references/offline-first-patterns.md`, `references/mobile-performance.md` |
| code-implementer | `references/offline-first-patterns.md`, `references/push-notification-design.md`, `references/mobile-performance.md` |
| comprehensive-test-strategy | `references/mobile-version-management.md`, `references/mobile-performance.md` |

Specific guidance the injection encodes:

- When `feature-flag-lifecycle` fires, mobile flags must use a remote config system (Firebase Remote Config, LaunchDarkly, Statsig). In-app static flags fail the gate — a flag you cannot flip without a new build is not a flag, it is a constant. Force-update flags are a special category with their own UX path; see `mobile-version-management.md`.
- When `release-readiness` fires, factor the store review window (1–3 days typical, up to 7 for new apps) into every release plan. An expedited review is a one-shot escape hatch, not a strategy.
- When `accessibility` fires, run the platform-specific audit — VoiceOver traversal and Dynamic Type scaling to the largest size on iOS; TalkBack traversal and 200% font scaling on Android. "Works on the default simulator config" is not an a11y audit.
- When `observability-sre-practice` fires, crash reporting (Crashlytics, Sentry, Bugsnag) is non-negotiable and ANR (Application Not Responding) tracking is mandatory on Android. In Rigorous mode, break out crash-free rate per device class (high-end / mid / low-end) because aggregate rates hide real regressions on old devices.

---

## Reference files

- `references/app-store-approval-cycles.md` — App Store and Play Store review timelines, expedited review triggers, common rejection reasons (IAP bypass, tracking without permission, misleading screenshots), guideline traps (SKAdNetwork, privacy labels, kids-category rules).
- `references/mobile-version-management.md` — semver for apps, minimum supported version policy, forced-update patterns (respectful: warning → deadline → forced), phased rollout mechanics with Play Console and App Store Connect, halting rollouts on crash rate spike.
- `references/offline-first-patterns.md` — local-first storage, optimistic UI, conflict resolution (last-write-wins, CRDT, user-intervention), durable queue for outgoing operations with retry-and-dedup, sync engines (WatermelonDB, PouchDB, custom).
- `references/push-notification-design.md` — APNS and FCM integration, topic-based vs per-user, delivery guarantees (or lack thereof), opt-in UX and iOS 15+ notification summary rules, token rotation, silent push for data sync.
- `references/mobile-performance.md` — cold-start budget, frame rate (60fps / 120fps targets), scroll jank detection, memory footprint, measurement tools (Instruments, Android Profiler, Firebase Performance), battery impact audit.

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: mobile | mode: <Mode> | duration: project
```

Skill firings under this track append the track context:

```
[YYYY-MM-DD] release-readiness | outcome: OK | note: App Store submission checklist passed | track: mobile
[YYYY-MM-DD] performance-reliability-engineering | outcome: OK | note: cold-start budget verified at 1.1s | track: mobile
```
