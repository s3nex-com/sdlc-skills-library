# App store approval cycles

The store review is the one gate your CI cannot skip. Treat it as an external dependency with a variable SLA and plan around it. This reference covers typical review timelines, how to request an expedited review, the common rejection reasons that actually hit teams, and the guideline traps that blindside first-time submitters.

---

## Typical review timelines

| Store | Typical | P90 | Worst case | Notes |
|-------|---------|-----|-----------|-------|
| App Store (Apple) | 24–48 hours | 2–3 days | 7+ days | New apps and first submissions skew longer. Holidays (Christmas week, Chinese New Year) freeze review entirely — plan submissions accordingly. |
| Play Store (Google) | 2–7 days | 3 days | 14+ days | Was near-instant pre-2020; now fully human-reviewed for new apps and major updates. Internal testing track pushes within an hour. |

**Plan with P90, not typical.** A release plan that assumes 24-hour App Store review and 24-hour Play Store review will break on its first submission that lands on a weekend or during a holiday freeze. Pad the release plan by 3 business days per store.

**Internal testing tracks bypass external review.** TestFlight internal testers (up to 100 members of your team) get builds within ~30 minutes of upload and processing. Play Console internal testing track pushes within an hour. Use them aggressively — they are the only way to close the CI-to-user loop faster than a day.

---

## Expedited review

### App Store

Apple allows expedited review requests through App Store Connect → Contact Us → App Review → Request Expedited Review. Grant rate is high when the justification is real. Valid reasons:

- Critical bug affecting many users (crash on launch, data loss)
- Fix for a security issue already disclosed or under embargo
- Time-sensitive event tie-in (live sports, elections, major product launch coordinated with marketing)
- Response to an Apple rejection where the team believes the rejection was in error and needs re-review before a deadline

Invalid reasons that get declined:

- "We want to release on Friday"
- "A competitor just launched"
- "Our investor meeting is tomorrow"

Expedited review is a one-shot. Apple tracks abuse and future requests get deprioritised or denied if a team cries wolf. Use it for genuine user-impacting issues only.

### Play Store

No formal expedited path. Escalation is through the Play Console support contact form. In practice Google reviews are faster on average than Apple, and the internal / closed testing tracks let you get to production faster via promotion once reviewed.

If a production release is stuck in review beyond 7 days on Play, open a support case citing the ticket number from the Play Console review queue.

---

## Common rejection reasons

The top rejections are almost always one of these. Check every one before submitting.

### Apple

**Guideline 3.1.1 — IAP bypass.** Selling digital goods or services consumed inside the app through any payment method other than Apple's IAP. This includes linking to a web page to buy a subscription from inside a login-walled app ("reader apps" are a narrow exception — see the recent Reader App rules). External payment links for digital goods remain risky even under the EU Digital Markets Act changes; follow the current guideline text.

**Guideline 5.1.2 — tracking without permission.** Calling `ATTrackingManager.requestTrackingAuthorization` too late, or tracking the user's IDFA before the prompt, or claiming in the privacy manifest that you do not track when an embedded SDK does. Apple uses static analysis to spot tracking SDKs that are not declared.

**Guideline 1.1.6 — misleading screenshots.** Screenshots that show features not in the app, use marketing text overlays that misrepresent functionality, or show a device frame that implies a different form factor. The current test: a reviewer launching the app must see something materially similar to each screenshot.

**Guideline 4.3 — spam / duplicate apps.** Multiple apps from one developer that differ only in branding or content (think: 50 versions of a flashlight app). Combine into one app with in-app switching or stop submitting duplicates.

**Guideline 1.1 — objectionable content.** Offensive imagery, hate speech, realistic depictions of violence against specific groups, or content that encourages harm. Also hits apps that ship with user-generated content but no moderation system — see Guideline 1.2 for the UGC-specific rules (report mechanism, block user, EULA, publish moderation policy).

**Guideline 2.1 — completeness.** Broken login, broken core flows, placeholder content ("Lorem ipsum"), or features that cannot be tested because they require credentials the reviewer does not have. Always provide a demo account in the review notes.

### Google Play

**Deceptive behaviour policy.** Misleading metadata, fake reviews, or app behaviour that differs from the description. Metadata copy-paste from a different app is a fast ban.

**Permissions policy.** Requesting permissions (SMS, call log, location in background, accessibility services) without a clearly documented core use. Location in background and accessibility services get extra scrutiny and require a permissions declaration form in the Play Console.

**Subscription policy.** Auto-renewing subscriptions without clear pricing disclosure, without a free-trial terms disclosure, or that make cancellation intentionally hard. Google compares the subscription flow in the app to the screenshot in the listing.

**Data safety disclosure mismatch.** What the data safety form declares must match what the app does. Automated scans and third-party audits catch mismatches; mismatches trigger enforcement action (warning → removal on repeat).

**Malware or unwanted behaviour.** Usually triggered by an SDK the team did not vet. Before adding a third-party analytics, attribution, or ads SDK, check its reputation against Google's Unwanted Software Policy.

---

## Guideline traps

These are the rules that blindside teams because they are not obvious until enforcement hits.

**SKAdNetwork and privacy manifests (Apple).** Every SDK that does tracking must ship a privacy manifest (`PrivacyInfo.xcprivacy`) declaring what it accesses. Required API reasons codes must be present for APIs like `UserDefaults`, `systemBootTime`, `fileTimestamp`, `diskSpace`, `activeKeyboards`. Starting with iOS 17, Xcode emits warnings for missing manifests; starting with newer SDK requirements, the App Store rejects builds that call flagged APIs without a declared reason.

**App privacy labels (Apple) and data safety form (Google).** Both stores require a declaration of what data the app collects, how it is used, whether it is linked to the user, and whether it is used for tracking. The declaration covers first-party code AND every embedded SDK. Ads SDKs, analytics SDKs, attribution SDKs all count. Missing or incorrect labels are a common cause of post-launch enforcement actions — the app ships, then gets flagged weeks later.

**Kids category (Apple and Google).** Apps in the kids category or designed for children under 13 are subject to separate rules: no third-party analytics unless explicitly approved for children, no behavioural advertising, COPPA compliance in the US, GDPR-K in the EU. Mis-categorising a general app as "ages 4+" because it is cute is a fast rejection. Mis-categorising a kids app as general audience is an enforcement escalation.

**Account deletion requirement.** Both stores require an in-app path to delete the user account (and supporting data) if the app supports account creation. A link to a web page counts on Play; Apple requires the deletion to be initiated from inside the app.

**Login requirement parity.** Apple Guideline 4.8 — if the app offers third-party sign-in (Google, Facebook), it must also offer Sign in with Apple. Sign in with Apple must be at least as prominent. Exceptions exist for enterprise and education apps with dedicated IdP; document the exception in review notes.

**Background location.** Both stores want a compelling user-facing justification. "To show ads" is not one. "To log runs when the screen is off" is one. Document the justification in the permission prompt and in the store listing.

---

## Submission checklist

Before tapping Submit:

- Demo account credentials provided in review notes (Apple) or tester credentials set up (Google).
- Screenshots match current app UI for every listed language.
- Privacy labels / data safety form reviewed against every SDK in the build.
- Privacy manifest present and complete (iOS 17+).
- Release notes describe what changed in user-facing language (not commit subjects).
- Phased rollout configured (see `mobile-version-management.md`).
- Crash reporting and feature flag kill switches verified in the release build.
- If using IAP: pricing reviewed, localised in store listing, subscription terms disclosed.
- If new permissions: permission declaration form completed on Play, usage description strings reviewed on App Store.
- If first submission: expect 3–7 days of review; do not promise a release date narrower than that.
