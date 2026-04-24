# Mobile version management

Versioning a mobile app is not the same as versioning a service. A service runs one version at a time; a mobile app runs every version anyone ever installed, on every OS going back years, until the user updates. This reference covers semver for apps, the minimum supported version policy, forced-update UX patterns, phased rollout mechanics, and halt criteria.

---

## Semver for apps

Mobile version strings have two levels: the **marketing version** (user-visible, e.g. `4.12.0`) and the **build number** (monotonic, unique per upload, e.g. `4120034`).

| Bump | Trigger | Examples |
|------|---------|----------|
| Major (X.0.0) | Visual redesign, breaking data migration, dropping OS support | Full UI refresh, onboarding overhaul, minimum iOS bump from 15 to 16 |
| Minor (4.X.0) | New feature, new screen, new integration | "Share to X", new tab, new settings section |
| Patch (4.12.X) | Bug fix, crash fix, copy change, small visual tweak | Hotfixes, localization fix, color correction |

Build numbers increase with every submission, even for the same marketing version. A common convention: `<major><minor:02><patch:02><ci-build:04>` → `4 12 00 0034` → `4120034`. This makes the build number sortable across versions and traceable to a CI run.

Never reuse a build number within the same marketing version — App Store Connect and Play Console both reject it. Never reuse a marketing version with a lower build number than the last live one — phased rollout and update logic will misbehave.

---

## Minimum supported version policy

The default for a healthy consumer mobile app: **support the current and previous two major OS releases.** At the time of writing that means iOS 16, 17, 18 on Apple and Android 12, 13, 14 on Google.

Rationale:

- Each OS version back adds real engineering cost — API branches, test matrix rows, bug surface area.
- Every major OS dropped is a feature you can now use across the app.
- Users on very old OS versions are on very old devices and are disproportionately represented in crash reports.

Review quarterly. Drop the oldest supported OS when its install base falls below **2% of active users** for four consecutive weeks. Announce the drop in-app at least 30 days before the first release that enforces the new minimum.

### The drop sequence

1. **Month 0:** Install base on OS N drops below 2%.
2. **Month 0:** Ship a build that shows an in-app banner on OS N devices: "This is the last version supporting iOS N. Update your device to keep getting updates."
3. **Month 1–2:** Run that build for at least 30 days.
4. **Month 2:** Raise the minimum OS in the new build. Users on OS N stay on the last supported build — App Store and Play Store serve them the last version whose minimum OS they satisfy.

Do not try to be clever and drop an OS mid-release. Drop at a major version boundary, announce it, and move on.

---

## Forced update patterns

A force-update flow is a UX last resort. Most updates should be optional. A forced update is only justified when:

- A security issue is active and unpatched in older versions.
- A backend contract change breaks older clients.
- A regulatory or compliance requirement leaves no alternative.
- The older client is corrupting user data.

### The respectful forced-update ladder

**Level 1 — soft nudge.** New version available. Dismissable. Appears once per session, max twice per week. Shown to users whose installed version is more than 2 minor versions behind.

**Level 2 — firm prompt.** New version available with a deadline. Dismissable but shows every launch. Message: "We need you to update by [date]. After that this version will stop working." Appears 14 days before the hard cutover.

**Level 3 — hard gate.** Update required. Non-dismissable. The only action is "Update now" which opens the store listing. Appears after the deadline in Level 2 passes, OR immediately if the installed version is on the security-critical block list.

Implement the force-update flag via remote config (Firebase Remote Config, LaunchDarkly, Statsig). Flag schema:

```json
{
  "min_supported_version": "4.8.0",
  "recommended_version": "4.12.0",
  "force_update_deadline": "2026-06-01T00:00:00Z",
  "force_update_message_ios": "We've fixed important security issues. Please update to continue.",
  "force_update_message_android": "We've fixed important security issues. Please update to continue."
}
```

Client logic on launch:

```swift
let installedVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String
let config = await RemoteConfig.fetchConfig()
if semver(installedVersion) < semver(config.minSupportedVersion) {
    presentHardGateUpdateScreen(message: config.forceUpdateMessageIos, storeURL: appStoreURL)
} else if Date() > config.forceUpdateDeadline {
    presentHardGateUpdateScreen(message: config.forceUpdateMessageIos, storeURL: appStoreURL)
}
```

The force-update flag is a **distinct category** of feature flag — track it separately in the feature flag registry. It is not cleaned up with regular flag hygiene.

---

## Phased rollout

Both stores support phased rollout of a production release. Use it for every release.

### App Store Connect

- Phased release for automatic updates: 1% → 2% → 5% → 10% → 20% → 50% → 100% over 7 days.
- Users who manually update from the store get the new version immediately regardless of phase.
- Can be paused at any phase. Pausing holds current phase for up to 30 days.
- Phases resume on unpause; you do not lose progress.
- No target cohort selection — Apple picks the percentage randomly.

### Play Console

- Staged rollout percentage set manually (e.g. 5%, 10%, 25%, 50%, 100%).
- Advance at the pace of the crash-free rate signal — not on a fixed schedule.
- Can be halted and resumed, or halted and a new build promoted instead.
- Can target by country during early stages — good for a geo-staged rollout.

### The playbook

1. Upload. Internal testing track first (engineers only), run smoke tests.
2. Closed testing track (Google) / TestFlight external testers (Apple). 50–500 trusted users for 24–48 hours.
3. Production staged rollout at **5%**. Hold for 24 hours. Watch crash-free rate.
4. If crash-free rate is stable, advance to **20%**. Hold 24 hours.
5. Advance to **50%**. Hold 24 hours.
6. Advance to **100%**.

Do not advance faster than 24 hours between stages. Crashes take time to surface — some only appear after the first background launch, some after the first push notification, some after a specific user flow. An extra day per stage is cheap insurance.

---

## Halt criteria

Halt the rollout immediately when any of these fire:

| Signal | Threshold | Source |
|--------|-----------|--------|
| Crash-free users | Drops > 0.5 pp below the last stable release at the same phase | Crashlytics / Sentry / App Store Connect / Play Console |
| Crash-free sessions | Drops > 1 pp | Same |
| ANR rate (Android) | > 0.5% sessions with an ANR | Play Console Android vitals |
| New crash in top 5 | A crash not present in the previous release appears in the top 5 | Crash reporter |
| User reports spike | Support tickets referencing the release version > 2× baseline | Support tool |
| App Store / Play Store rating drops | 7-day average rating drops > 0.3 stars | Store console |

The decision to halt is made by the on-call engineer based on these signals; it does not require a meeting. Always halt first, investigate second.

### Halting mechanics

- **Play Console:** Halt rollout → choose "Halt rollout" from the release page. Existing installed version stays on the old version; new users get the last stable release.
- **App Store Connect:** Pause phased release. Users who already updated stay on the new version; users who have not yet rolled out stay on the old one. Pause can last up to 30 days.
- **Hotfix path:** Fix the regression, submit a new build, promote to production. This always takes > 24 hours because of review — plan for it by keeping one "rollback to the previous build" feature-flag path ready to disable the new feature without a new submission.
