# Viral and referral mechanics

## Core concepts

Viral growth mechanics amplify organic acquisition. The k-factor (viral coefficient) measures new users generated per existing user:

```
k = (invites sent per user) × (invite conversion rate)
```

k > 1 means viral growth. k = 0.3 is realistic for most products. Engineering viral mechanics means maximising every component of this equation while preventing abuse.

---

## Invite flow design

Every invite flow has four components:

### 1. Invite creation
- Generate a unique invite token per sender (or per sender + recipient pair for targeted invites)
- Schema: `invite_id`, `sender_user_id`, `invited_email` (if email-targeted), `token`, `created_at`, `expires_at`, `status` (pending / accepted / expired)
- Idempotency: re-inviting the same email by the same sender must reuse the existing token (or extend its expiry), not create a duplicate

### 2. Invite distribution
- Email: transactional email (not marketing batch sender), include personalisation from sender
- Link sharing: deep link with invite token embedded; handle app-not-installed case (universal links / deferred deep links)
- Rate limit per sender: cap invites per user per 24h (e.g., 20 invites/day) to prevent spam abuse
- Track sends: `invite_sent_at`, `delivery_status`

### 3. Invite acceptance
- Token validation: check existence, expiry, and that it has not already been used
- Single-use enforcement: mark token consumed on first use; reject subsequent uses with a clear message
- Attribution: record `accepted_at`, `new_user_id` against the invite record
- Edge case — invited user already has an account: decide policy (deny attribution? allow with a note?). Document it.
- Idempotency: the acceptance endpoint must handle retries without creating duplicate users or duplicate attribution records

### 4. Reward distribution
- Trigger reward after the acceptance milestone is confirmed (never before — prevent early claims)
- Reward idempotency key: `invite_id + reward_type` — the reward can only be granted once per invite
- Rollback path: if a product uses claw-back (user churns within N days → reward reversed), design the reversal flow before shipping the forward flow

---

## Double attribution prevention

Double attribution is the most common correctness failure in referral mechanics:

- User A invites User B; User B also signs up via a paid ad → who gets credit?
- User A invites User B twice (token expired, resent) → User B accepts the second invite; both tokens must not both generate credit

Prevention rules:
1. One attribution per new user, enforced at the database level
2. Mark a user as "attributed" on their first accepted invite. Subsequent invite claims for this user are rejected silently (no error to sender)
3. Invite token consumed at acceptance; unique constraint on `(token, status='accepted')`

---

## Fraud and abuse vectors

| Vector | Description | Mitigation |
|--------|-------------|-----------|
| Self-referral | User creates second account to claim their own reward | Require email/phone verification; check device fingerprint or email domain overlap |
| Fake invite tree | User generates many fake accounts | Rate-limit invites; delay reward until new user completes a meaningful action beyond signup |
| Token enumeration | Attacker tries guessable tokens | Cryptographically random tokens (UUID v4 or 128-bit random); never sequential IDs |
| Reward harvesting | Bot creates many new accounts | CAPTCHA or SMS verification on signup; milestone action required before reward is unlocked |

---

## K-factor measurement

Track the full funnel weekly:

```sql
SELECT
  DATE_TRUNC('week', i.created_at) AS week,
  COUNT(DISTINCT i.sender_user_id) AS senders,
  COUNT(i.invite_id) AS invites_sent,
  COUNT(CASE WHEN i.status = 'accepted' THEN 1 END) AS accepted,
  ROUND(
    COUNT(i.invite_id)::numeric / NULLIF(COUNT(DISTINCT i.sender_user_id), 0), 2
  ) AS invites_per_sender,
  ROUND(
    COUNT(CASE WHEN i.status = 'accepted' THEN 1 END)::numeric / NULLIF(COUNT(i.invite_id), 0), 4
  ) AS conversion_rate,
  ROUND(
    COUNT(CASE WHEN i.status = 'accepted' THEN 1 END)::numeric / NULLIF(COUNT(DISTINCT i.sender_user_id), 0), 4
  ) AS k_factor
FROM invites i
GROUP BY 1
ORDER BY 1 DESC;
```

A week-over-week decline in k-factor signals: less compelling invite content, a drop in new user conversion (the product itself is less compelling to new arrivals), or fraud controls catching more abuse.

---

## Network effect activation

For social products, the network effect activation funnel:

1. User signs up (baseline)
2. User performs first social action (follow, connect, post)
3. User receives first social interaction (follower, like, comment)
4. User returns after receiving the social signal (network-effect retention)

Step 3→4 conversion is the network effect activation signal. A user who receives a social signal within their first session is typically 2–5× more likely to retain. Engineer for delivering step 3 as quickly as possible post-signup — consider "welcome connection" mechanics that ensure new users receive at least one interaction before their first session ends.

---

## DB schema (minimal)

```sql
CREATE TABLE invites (
  invite_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  token       CHAR(32) UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(16), 'hex'),
  sender_id   UUID NOT NULL REFERENCES users(id),
  invited_email TEXT,             -- null if open link (no target email)
  status      TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'accepted', 'expired')),
  new_user_id UUID REFERENCES users(id), -- set on acceptance
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at  TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '7 days',
  accepted_at TIMESTAMPTZ
);

-- Prevent double attribution: one accepted invite per new user
CREATE UNIQUE INDEX ON invites (new_user_id) WHERE status = 'accepted';

-- Idempotency: one pending invite per sender + email pair
CREATE UNIQUE INDEX ON invites (sender_id, invited_email) WHERE status = 'pending';
```
