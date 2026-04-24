# Push notification design

Push notifications are the most abused feature in mobile. Every app asks for permission. Users have learned to say no. The apps that still get meaningful push engagement are the ones that earned it — with clear value, restrained volume, and well-handled delivery failures. This reference covers APNS and FCM integration, topic vs per-user targeting, delivery guarantees, opt-in UX, iOS 15+ summary rules, token rotation, and silent push for data sync.

---

## APNS and FCM overview

| Dimension | APNS (Apple Push Notification Service) | FCM (Firebase Cloud Messaging) |
|-----------|---------------------------------------|-------------------------------|
| Platforms | iOS, iPadOS, macOS, watchOS, tvOS | Android primarily; can target iOS via APNS under the hood |
| Authentication | Token-based (.p8 key) or cert-based (deprecated in practice) | Firebase service account JSON |
| Device identifier | Device token (changes on app reinstall, restore from backup, iOS update) | FCM registration token (changes on reinstall, data clear, app update in some cases) |
| Delivery guarantee | Best effort. No guaranteed delivery, no delivery receipt for notifications. Silent pushes are especially lossy. | Same. FCM will drop pending messages after 4 weeks; priority and TTL affect delivery. |
| Rate limits | Soft limits per-device. Apple throttles apps that send high volumes of silent push. | Hard quota per project per minute. |
| Priority | 10 (immediate, user-visible) or 5 (conserve battery, may delay). | "high" (immediate) or "normal" (may delay for battery). |

Use FCM as the single server-side abstraction even for iOS — Google's FCM forwards to APNS for you and unifies the server API. Trade-off: one more dependency, one more vendor in the privacy review. Acceptable for most teams.

---

## Topic-based vs per-user

### Topic-based

Devices subscribe to topics (`news-weekly`, `orders-all`, `sports-premier-league`). Server sends one message to a topic; the push provider fans out.

Use when: broadcast is actually what you want. A news alert to everyone. A product launch. A scheduled daily digest.

Pros: server-side simplicity, one send covers millions of devices, no per-user list maintenance.

Cons: no targeting by state (cannot exclude users who just opened the app), no personalisation, topic subscription state lives on the device and is a sync problem of its own.

### Per-user (device-targeted)

Server maintains a mapping from user to device tokens. For a send, look up the tokens for the targeted users and send one message per token.

Use when: the content is personalised or the audience is specific ("your order shipped", "reply from @alice", "your rent is due").

Pros: precise targeting, full personalisation, can exclude users based on server-side state.

Cons: scales linearly with audience size, requires a tokens table with cleanup logic, needs batching to respect rate limits.

**In practice**: most apps need both. Topic-based for announcements and broadcast, per-user for everything transactional.

---

## Delivery is not guaranteed

Assume every push might not arrive. Do not use push as the sole delivery mechanism for anything important.

Scenarios where push is dropped:

- Device offline for more than the TTL window (default 4 weeks on FCM; APNS varies).
- Device in low power mode (throttles low-priority pushes).
- Device in a new focus mode or do-not-disturb window (APNS will not deliver user-visible notifications).
- App was force-quit on Android (some OEMs, notably Xiaomi, Huawei, Samsung One UI, kill FCM for force-quit apps).
- App is in the "Restricted" battery bucket on Android.
- Token has rotated and the server has not caught up — the push goes to the old token and is silently dropped.
- Silent push rate exceeds Apple's undocumented threshold and the app is throttled.

The corollary: **every push-carried piece of data must also be fetchable from the server.** If the user opens the app without having received the push, they still see the notification (as an in-app badge / inbox / feed entry). Push is a wake-up signal, not a data channel.

---

## Opt-in UX

The default iOS and Android dialog is one chance, and a "no" is hard to reverse — the user has to go into Settings and toggle it back on. Do not prompt at launch.

### The priming pattern

1. Let the user use the app for at least one meaningful action.
2. When the user hits a screen where push genuinely helps (after placing an order, after posting, after following a creator), show a **priming screen** that explains in plain language what notifications they will get.
3. The priming screen has two buttons: "Turn on notifications" (triggers the OS prompt) and "Not now" (no OS prompt; show again later).
4. If the user taps "Turn on notifications", THEN call the OS prompt.

This pattern consistently lifts opt-in rates by 2–3× versus prompting on launch.

### Granular opt-in

The single OS permission is all-or-nothing. Layer app-level preferences underneath: transactional (orders, DMs) vs marketing (promotions) vs social (likes, comments). Default transactional on, default marketing off. Honour a user who turns off marketing but keeps transactional — do not sneak a promo into the transactional channel.

### iOS 15+ notification summary and focus filters

iOS 15 introduced scheduled summary — users can opt to receive non-time-sensitive notifications as a digest at fixed times. Notifications marked `interruption-level: time-sensitive` bypass summary and focus filters, but that level is reserved for genuinely urgent items (package about to be delivered, ride is arriving, medication reminder). Abuse it and Apple will downrank the app's notifications.

- Use `interruption-level: active` (default) for normal notifications.
- Use `interruption-level: time-sensitive` only when the user would consider it an emergency to miss.
- Use `interruption-level: critical` almost never — requires special entitlement from Apple.
- Use `relevanceScore` (0.0–1.0) to help iOS rank your notifications in summary; higher = more likely to lead the digest.

### Android channels

Android 8+ requires every notification to go on a named channel. Each channel has its own importance (LOW, DEFAULT, HIGH, URGENT) and the user can disable channels individually without disabling all app notifications. Split channels by user-visible category — transactional / social / marketing — not by internal code pathways. Channels are created at first use and cannot be reconfigured (users only change them in settings).

---

## Token rotation

Device tokens change. The server cannot keep a stale token and assume delivery failures are transient — it must refresh.

### When tokens rotate

| Event | iOS | Android |
|-------|-----|---------|
| Fresh install | New token | New token |
| App reinstall | New token | New token |
| Restore from backup to new device | New token | New token |
| OS major version upgrade | Sometimes new token | Sometimes new token |
| App clears data (Android) | N/A | New token |
| Token expiry (rare) | Possible | Possible |

### Handling rotation

1. On every app launch (or at least every 24 hours), fetch the current token and compare against the last-registered token stored locally.
2. If different, POST the new token to the server along with the old one. Server atomically replaces the mapping.
3. On every push send, capture APNS/FCM's response. Specifically:
   - **APNS 410 Unregistered** → delete the token from the mapping; the app was uninstalled or its token is permanently invalid.
   - **APNS 400 BadDeviceToken** → delete the token.
   - **FCM `NotRegistered`** or `InvalidRegistration` → delete the token.
4. Run a periodic cleanup job that removes tokens that have been unreachable for > 30 days.

Skipping the cleanup is the #1 reason a push system accumulates bad tokens and silently loses engagement. A healthy token-to-active-user ratio is ~1.1:1; anything above 2:1 means the cleanup is broken.

---

## Silent push for data sync

A silent push (`content-available: 1` on APNS, `data`-only payload on FCM) wakes the app briefly in the background to fetch new data. The user sees nothing. Useful for:

- Pre-fetching a feed so the next open is instant.
- Triggering a sync when the server knows new data exists.
- Invalidating a local cache on a server-side change.

Constraints:

- Apple heavily throttles silent push. Budget: a few per hour per device, not dozens. Over-send and they get dropped.
- Background execution time on iOS is ~30 seconds. Finish the sync and call the completion handler, or the system reports a timeout and throttles harder.
- Silent push on Android works but battery-restricted apps do not wake. The "Dozing" state will delay delivery until the next maintenance window.
- Silent push is not a replacement for a proper sync engine (see `offline-first-patterns.md`). It is a nudge; the app must also sync on launch and periodically in the foreground.

### Payload shape

APNS silent push:

```json
{
  "aps": {
    "content-available": 1
  },
  "sync_hint": "notes:updated",
  "entity_id": "abc123"
}
```

FCM silent push:

```json
{
  "message": {
    "token": "<device-token>",
    "data": {
      "sync_hint": "notes:updated",
      "entity_id": "abc123"
    },
    "android": { "priority": "high" },
    "apns": {
      "headers": { "apns-priority": "5", "apns-push-type": "background" },
      "payload": { "aps": { "content-available": 1 } }
    }
  }
}
```

The payload carries a **hint**, not data. The app uses the hint to decide what to sync, then pulls the data from the server. Never trust payload contents as a data source — payloads are truncated (APNS limit is 4KB), reordered, and occasionally dropped.

---

## Handling delivery failures

On every send, log the result. Aggregate by error code and alert when any error rate exceeds 1%. Common failure categories:

| Code | Meaning | Action |
|------|---------|--------|
| APNS 410 / FCM NotRegistered | Token invalid | Remove token |
| APNS 429 / FCM quota exceeded | Rate limited | Backoff; batch; reduce volume |
| APNS 413 / FCM payload too large | Payload too big | Shrink payload; move data behind a fetch |
| APNS 403 / FCM mismatched credentials | Auth problem | Page on-call; rotate keys |
| APNS 5xx / FCM internal | Transient | Retry with backoff |

An end-to-end audit: send a test push to a known test device on every deploy, verify arrival via an instrumented test client. If the test device does not receive the push within 60 seconds, the alert fires.
