# Notification pipeline design

## Notification types

Three channels, three disciplines:

- **Push notifications** (APNs, FCM): highest reach, lowest noise tolerance. Users who mute or block push are lost permanently. Treat every push as a negotiation.
- **In-app notifications** (notification inbox, banners, badges): seen only when the user is active. Lower stakes, higher frequency tolerance.
- **Email** (transactional, digest, re-engagement): highest deliverability requirements (SPF/DKIM/DMARC), regulated by CAN-SPAM and GDPR.

---

## Consent and compliance first

Consent is a precondition, not an afterthought. Before the first notification ships:

- **Push**: OS-level permission prompt. Fire it at the right moment (after aha moment, not on first load). Permission rate is a product metric; treat permission denials as product failures.
- **Email marketing**: double opt-in for marketing; transactional email is implicit consent but must remain genuinely transactional.
- **All channels**: unsubscribe must be honoured within 24 hours max (GDPR Art. 7, CAN-SPAM within 10 days — honour the stricter). Preference centre should cover per-channel and per-category.

Under GDPR, analytics for notification performance (open rate, click rate) constitutes processing — it must be in the PIA with a lawful basis. Most teams use legitimate interest; document it.

---

## Delivery architecture

### Fanout patterns

| Pattern | When | Trade-off |
|---------|------|-----------|
| Direct write | < 10k recipients | Simple, synchronous |
| Pre-computed fanout | Read-heavy feeds (> 10k recipients) | Higher write cost, fast reads |
| Hybrid | Mix of high/low follower counts | Complexity; worth it at Instagram/Twitter scale |

### Idempotency

Every notification send must be idempotent. Design a deduplication key:
- For event-driven sends: `notification_type + user_id + event_id`
- For scheduled sends: `notification_type + user_id + period (YYYY-MM-DD)`

Store the dedup key in a delivery log with TTL matching the max retry window. A duplicate send costs user trust; it is not a recoverable error.

### Retry and DLQ

- Failed sends retry with exponential backoff (1s, 5s, 30s)
- After 3 retries, move to DLQ and alert
- DLQ drains must be idempotent — the notification will be attempted again

---

## Timing and frequency

- **Quiet hours**: respect device time zone by default; allow user override. 9pm–8am is the conventional quiet window.
- **Frequency cap**: hard cap per user per 24h per channel (e.g., max 3 push/day). Cap across notification types, not per type.
- **Batching**: digest notifications (weekly/daily summaries) reduce noise and unsubscribe rates for low-urgency updates.
- **Send-time personalisation**: per-user send-time optimisation reduces ignore rates. A simple heuristic ("time the user is usually active") outperforms global send times.

---

## A/B testing notifications

Notification content is an experiment surface. Apply consumer-track experiment discipline:

- Subject line / title variants
- CTA copy variants
- Delivery timing variants (morning vs evening)

Track the full funnel: send → delivered → opened → converted. The experiment does not end at open rate — measure downstream action.

Cache poisoning risk: A/B assignment must happen before notification content is generated, not at send time. If assignment is cached, the cache key must include the experiment assignment — not just content type.

---

## Metrics

| Signal | Definition | Health threshold |
|--------|-----------|-----------------|
| Delivery rate | Delivered / sent | > 95% (push); > 98% (email) |
| Open rate | Opened / delivered | > 5% push; > 20% email (varies by type) |
| Click-through rate | Clicked / opened | Track trend; no universal threshold |
| Unsubscribe rate | Unsubs / sent | < 0.5% per send (email) |
| Push opt-out rate | Push disabled / users prompted | < 30% healthy; > 60% is a signal problem |

---

## Common failure patterns

- Sending a notification and then sending a "we sent you a notification" email — double-touching the user on a single event
- Triggering a push when the user is actively in the app — use in-app instead
- No preference centre: users who cannot control notification frequency uninstall instead
- Missing unsubscribe link in marketing email — CAN-SPAM violation, deliverability penalty
