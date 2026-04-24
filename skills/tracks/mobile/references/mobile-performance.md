# Mobile performance

Mobile performance is four budgets: **cold-start time**, **frame rate**, **memory footprint**, and **battery drain**. Each has a target, a measurement method, and a failure mode users will notice. This reference covers the budgets, the measurement tools, how to detect scroll jank, and how to run a battery impact audit.

---

## Cold-start budget

Cold start = process launch → first meaningful paint (the first screen the user can interact with, not a splash screen).

| Tier | Target | Rationale |
|------|--------|-----------|
| Flagship device, latest OS | < 800 ms | Users expect near-instant |
| Mid-range device, current OS - 1 | < 1.5 s | The standard budget |
| Low-end device, oldest supported OS | < 3.0 s | The hard ceiling; above this users bounce |

**Measurement baseline**: always measure cold start on a real device, not a simulator. Simulators use desktop-class CPUs and do not reflect startup cost of reading from flash, paging in shared libraries, or running JIT warmup.

### iOS measurement

Xcode Instruments → App Launch template. Run on a physical device in release config. Key metrics:

- `UIKit init` — system UI setup
- `Static runtime init` — loading shared libs, +load methods, static initialisers
- `Application init` — `application(_:didFinishLaunchingWithOptions:)`
- `Initial frame render` — time to first CA commit

Total = time from process exec to first frame.

The MetricKit framework (`MXMetricPayload`) reports launch time on real user devices and surfaces them to App Store Connect. Use `MXAppLaunchMetric` to track P50 and P95 across the install base.

### Android measurement

Android Studio Profiler → Startup profiling, OR `adb shell am start -W -n <package>/<activity>` which prints `TotalTime` and `WaitTime`.

Firebase Performance Monitoring reports `_app_start` trace across the install base without extra code.

For release builds specifically: the `StartupTracing` API (Android 10+) captures the critical path from `Application.onCreate` through first frame.

### Common cold-start regressions

- **Synchronous work on the main thread during app startup.** Any disk, network, or compute on startup blocks first frame. Defer non-essential work to after first frame, via `DispatchQueue.main.async` (iOS) or `Handler.post` (Android), or even to a background queue triggered after first render.
- **+load methods and static initialisers (iOS).** Objective-C `+load` and Swift static property initialisers run before main. Audit all dependencies for these.
- **Application.onCreate doing too much (Android).** Firebase, analytics, crash reporting, DI graph setup — measure each. Move non-critical paths to a WorkManager task or lazy-init.
- **Bundle size.** Every binary byte adds load time. Check bundle size at every release. The ~200 MB app is a ~200 MB problem.

Treat cold-start time as a regression metric. Fail CI if P50 cold start grows by > 10% vs the last release baseline.

---

## Frame rate

| Target | Device class |
|--------|-------------|
| 60 fps steady | Any modern device, standard displays |
| 120 fps steady | ProMotion iPhones (14 Pro+), high-refresh Androids |
| No frame drops during user interaction | All devices |

A frame budget at 60 fps is **16.67 ms** per frame. At 120 fps it is **8.33 ms**. Work that runs on the main thread and exceeds the budget causes a dropped frame. Users see it as jank.

### Scroll jank detection

Scroll jank is the dominant visible performance problem in mobile apps. It shows up as stuttering during a list scroll, especially on first view of rows that are loading images or laying out complex cells.

**iOS detection**: Instruments → Animation Hitches template (Xcode 12+). Reports hitch time ratio — milliseconds of hitches per second of scrolling. Target: < 5 ms/s. Above 50 ms/s is unacceptable.

**Android detection**: `adb shell dumpsys gfxinfo <package> framestats` gives per-frame timing. Play Console → Android vitals → "Slow rendering" reports the percentage of sessions with > 50% slow frames. Alert threshold: > 20% of sessions.

**Jetpack Compose**: use the Layout Inspector's recomposition counts. An item that recomposes every scroll frame is almost always a bug — usually a non-stable parameter to a composable, or a `remember` that is missing.

### Common causes

- Image decoding on the main thread. Use async image libraries (SDWebImage, Glide, Coil, Nuke) that decode off-main and cache.
- Layout cost per cell. Complex nested layouts, auto-layout constraints with multiple passes, Flutter widget trees that rebuild fully on each item. Flatten the layout; memoise expensive subtrees.
- Allocating per frame. Re-creating large objects inside a scroll callback. Profile for allocations inside `scrollViewDidScroll` / `onScroll`.
- Animating layout-affecting properties. Animating `width`/`height` forces relayout per frame; animating `transform` does not.
- Missing `shouldRasterize` / `RenderEffect` optimisations where appropriate (but test — rasterisation over-use can hurt).

---

## Memory footprint

Memory pressure kills the app — literally. iOS and Android aggressively terminate foreground apps that exceed their memory budget.

| Device tier | Target steady-state | Jetsam ceiling |
|-------------|---------------------|----------------|
| iPhone with 6 GB RAM | < 500 MB | Varies; often ~1 GB for foreground |
| iPhone with 3 GB RAM | < 300 MB | ~650 MB for foreground |
| Android high-end (8 GB+) | < 512 MB | Device-dependent |
| Android low-end (2 GB) | < 256 MB | 192 MB on many low-end devices |

### Measurement

- **iOS**: Instruments → Allocations + Leaks. For live tracking, use `os_proc_available_memory()` (iOS 13+) to read remaining allowance.
- **Android**: Android Studio Memory Profiler. `ActivityManager.getMemoryInfo()` for live tracking.
- **Firebase Performance**: reports `memory_usage` across the install base.

### Common leaks

- Retain cycles in closures (iOS). `[weak self]` capture in any closure stored on a long-lived object.
- Static references to Activity (Android). Any `static` holding an `Activity` or `View` will leak the entire activity tree.
- Image caches with no eviction. Every cache needs a cost limit (bytes or count) and eviction policy.
- Subscriptions not cancelled. Kotlin Flow collectors, RxJava subscriptions, Combine subscribers — cancel on lifecycle end, every time.
- Bitmap memory (Android). Load images at display size, not source size. A 4000×3000 photo at `ARGB_8888` is 48 MB.

---

## Battery impact audit

Battery is the budget users care about most. A single release that drains 5% extra per hour is a one-star review event.

### Measurement

- **iOS**: Xcode → Energy Gauge while running the app. Reports CPU, network, location, GPU cost. Settings → Battery on a user's device shows per-app hourly drain (can be read via MetricKit's `MXCPUMetric` and `MXDiskIOMetric`).
- **Android**: Android Studio Energy Profiler. `adb shell dumpsys batterystats --charged <package>` for cumulative stats. Battery Historian (a web tool) for visualisation.
- **Firebase Performance**: no direct battery metric; use CPU usage and network volume as proxies.

### Common battery drains

- **Background location.** Continuous "always" location is expensive. Switch to "while in use" unless there is a genuine need; when "always" is required, use significant-change location (iOS) / geofencing (Android) instead of continuous updates.
- **Wake-lock / background fetch abuse.** iOS background fetch and Android `WorkManager` both tolerate frequent scheduling but penalise apps that wake the device too often. Batch work; coalesce fetches.
- **Unbounded polling.** Any poll-every-5-seconds loop on a mobile client is a battery disaster. Replace with push (for server-state changes) or longer intervals with jitter.
- **Unnecessary Bluetooth / NFC scanning.** Both radios cost significant power. Scan only when the user-facing feature is active.
- **Video and audio in the background.** Some codecs hit the CPU hard. Hardware decode paths are much cheaper — verify the pipeline is hitting them.
- **Large sync payloads on cellular.** Radio stays hot after a transmission (the "tail energy" problem); many small transfers drain more than a batched transfer.

### Battery impact audit process

1. Charge a test device to 100%, disconnect charger, unplug all accessories.
2. Bring the app to the foreground and exercise a representative 10-minute user session. Measure remaining battery.
3. Background the app (do not kill). Leave the device idle for 1 hour. Measure remaining battery.
4. Compare to a baseline (previous release, or a competitor app for reference).
5. If foreground drain > 5% per 10 minutes, or background drain > 1% per hour, investigate before ship.

Run the audit on a mid-range device, not the team's flagship. Flagships hide power sins that low-end devices feel.

---

## Measurement tools summary

| Tool | Platform | What it measures | When to use |
|------|----------|-----------------|-------------|
| Xcode Instruments | iOS | Everything — CPU, memory, leaks, animations, energy | Deep dive from a developer machine |
| MetricKit | iOS | User-device launch / hang / CPU metrics | In-production reports to App Store Connect |
| Android Studio Profiler | Android | CPU, memory, energy, network | Deep dive from a developer machine |
| Firebase Performance | Both | Startup, HTTP, custom traces, across real users | Fleet-wide monitoring |
| Play Console Android vitals | Android | ANR rate, crash rate, slow rendering, stuck wake locks | Production baseline; alerts |
| App Store Connect Metrics | iOS | Hangs, launches, memory, disk | Production baseline; alerts |
| Sentry / Bugsnag / Crashlytics | Both | Crash-free rate, performance transactions | Real-user monitoring with drill-down |

Pick one fleet-wide tool (Firebase or Sentry) and one platform-native tool (Instruments + Android Studio). Do not run four competing RUM platforms — they all add overhead.
