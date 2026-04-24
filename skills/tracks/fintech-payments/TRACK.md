---
name: fintech-payments
description: >
  Activates when the user mentions PCI DSS, cardholder data, card vault, tokenization,
  payment intent, charge flow, payout, reconciliation, fraud detection, chargeback,
  dispute handling, regulated financial service, money transmitter, KYC/AML, crypto
  custody, stablecoin integration, or on-chain settlement. Also triggers on explicit
  declaration: "Fintech track" or "Payments track".
---

# Fintech / Payments track

## Purpose

This track covers products that handle card data, bank account credentials, money movement, crypto custody, or regulated financial services. These systems have properties the generic library does not assume: a duplicate request is worse than a delayed one, a leaked card number is a reportable breach with regulatory timers, and the ledger must reconcile to the cent against external processors every day. The standard 41 skills plus a mode setting do not enforce these defaults. This track elevates idempotency, PCI scope discipline, reconciliation, fraud integration, and transaction-level observability from optional to load-bearing, and tightens stage gates so a payments build cannot ship without them.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "PCI DSS", "cardholder data", "PAN", "card vault", "tokenization"
- "payment intent", "charge", "authorize/capture", "payout", "refund", "reconciliation"
- "fraud detection", "chargeback", "dispute handling", "3DS", "SCA"
- "regulated financial service", "money transmitter license", "KYC", "AML", "OFAC"
- "crypto custody", "stablecoin integration", "on-chain settlement", "wallet", "custody keys"

Or when the system under discussion has these properties:

- Your service receives, stores, transmits, or processes card numbers (or any PCI-scoped element).
- Your service moves money between accounts — internal ledger entries that correspond to real-world settlement.
- Your service connects to a processor (Stripe, Adyen, Checkout.com, Worldpay) for authorization or payouts.
- Your service holds customer funds or crypto assets on their behalf.
- Your service must file regulatory reports (CTR, SAR, STR, PSD2 transaction reporting).

---

## When NOT to activate

Do NOT activate this track when:

- The product delegates the entire card capture flow to a hosted processor form (Stripe Checkout, Stripe Payment Element in iframe mode) and card data never touches your infrastructure — PCI scope is carried by the processor. `security-audit-secure-sdlc` still fires for the integration, but the fintech overlay is too heavy.
- The product only displays read-only pricing or invoice data without initiating payment.
- Payroll or expense-report systems where the actual money movement is handled by a third-party bureau and your system is strictly a data producer.
- Gift cards or loyalty points with no cash-out path — those are not money movement.

If you are unsure, answer this: does a bug in your code result in duplicate, lost, or misrouted money? If yes, activate. If no, don't.

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| security-audit-secure-sdlc | Mandatory | Mandatory + PCI checklist | Mandatory + threat model | Mandatory + threat model + external review |
| data-governance-privacy | Mandatory | Mandatory | Mandatory | Mandatory |
| distributed-systems-patterns | Advisory | Mandatory (idempotency) | Mandatory (idempotency + outbox) | Mandatory (all patterns reviewed) |
| formal-verification | N/A | N/A | Conditional (for critical protocols) | Mandatory for money-movement protocols |
| api-contract-enforcer | Advisory | Mandatory | Mandatory | Mandatory + runtime validation |
| observability-sre-practice | Standard | Standard | Transaction-level tracing required | Transaction-level tracing + anomaly alerting |
| disaster-recovery | N/A | Advisory | Mandatory (DR plan + tested restore documented) | Mandatory + quarterly DR test evidence filed |
| architecture-fitness | N/A | Mandatory (financial module boundary rules enforced in CI) | Mandatory | Mandatory |
| cloud-cost-governance | N/A | Advisory | Mandatory (per-feature transaction infrastructure cost attribution) | Mandatory |
| chaos-engineering | N/A | N/A | Conditional (payment path resilience experiments) | Mandatory + quarterly game day |
| incident-postmortem | Standard | Standard + reconciliation-incident process | Standard + reconciliation-incident + regulatory reporting | Standard + reconciliation + regulatory reporting + external notification checklist |

Only skills whose treatment differs from the default mode behaviour are listed. All other skills retain their mode defaults.

Notes on the additional elevations:

- `disaster-recovery` becomes Mandatory at Standard because PCI DSS Requirement 12.3 (business continuity planning) and most card-brand operational requirements mandate a documented and tested restore path. Advisory at Lean covers non-PCI-scope financial features.
- `architecture-fitness` at Lean+ enforces CI-level import boundaries around financial calculation modules — preventing currency, rounding, and tax logic from leaking across module boundaries, which is the root cause of a class of regulatory bugs.
- `cloud-cost-governance` at Standard+ tracks per-feature transaction infrastructure costs, which are the dominant cost driver in payment systems and directly feed unit-economics reporting to finance and compliance.
- `chaos-engineering` elevates to Conditional at Standard (payment path resilience experiments: processor outage, DB slow query during charge, retry storm) and Mandatory at Rigorous (quarterly game day with post-mortem).
- `incident-postmortem` adds the reconciliation-incident process at Lean+ (any incident that could affect ledger accuracy triggers a reconciliation check as part of the post-mortem), and adds regulatory reporting (SAR/CTR/STR filing review) at Standard+.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 2 (Design) | PCI DSS in-scope component identification required. Data flow diagram must show cardholder data flow explicitly — where PAN enters, where it is tokenized, where it is stored, where it leaves. |
| Stage 4 (Verify) | Reconciliation test scenario required (ledger-vs-processor mismatch must be detected and surfaced). Fraud/dispute flow tested end-to-end including manual review queue. |
| Stage 5 (Ship) | External security review sign-off required for any release that expands PCI scope (new component that touches PAN). Compliance officer sign-off — for a 3-5 person team this means a documented self-review posted to the PR with the PCI checklist attached. |
| Phase 3 (Ongoing) | Quarterly PCI DSS compliance review added to the operational cadence. Runs against the current scope diagram; diffs scope additions since last review. |

Strictest-wins when combined with another track. A Fintech + Healthcare product at the Ship gate must satisfy both PCI scope review and BAA coverage.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| security-audit-secure-sdlc | `references/pci-dss-checklist.md` |
| distributed-systems-patterns | `references/idempotency-patterns-payments.md` |
| code-implementer (money-movement code paths) | `references/idempotency-patterns-payments.md`; in Rigorous mode, mandate that `formal-verification` has already run on the protocol before merge |
| observability-sre-practice | `references/reconciliation-runbook.md` (for the transaction-tracing and reconciliation-alert sections) |
| data-governance-privacy | `references/regulatory-reporting-guide.md` (for CTR/SAR/PSD2 data retention windows) |
| technical-risk-management | `references/fraud-signals-integration.md` (fraud score thresholds become risk register entries) |

---

## Reference files

- `references/pci-dss-checklist.md` — PCI DSS 4.0 requirements mapped to concrete engineering tasks: segmentation, encryption, access control, logging, vuln management, secure SDLC.
- `references/idempotency-patterns-payments.md` — idempotency key conventions for payment APIs: header naming, dedup table schema, TTL, retry semantics, Stripe-style worked example.
- `references/reconciliation-runbook.md` — daily/weekly reconciliation pattern, mismatch triage, escalation, and a worked Stripe-vs-Orders-table nightly batch.
- `references/regulatory-reporting-guide.md` — CTR/SAR triggers in the US, PSD2 SCA and AML reporting in the EU, automated data capture, retention windows.
- `references/fraud-signals-integration.md` — fraud provider integration (Sift, Stripe Radar, Signifyd), uncertain-verdict handling, manual review queue, feedback loops.

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: fintech-payments | mode: <Mode> | duration: project
```

Skill firings under this track append the track context:

```
[YYYY-MM-DD] security-audit-secure-sdlc | outcome: OK | note: PCI DSS threat model complete | track: fintech-payments
[YYYY-MM-DD] distributed-systems-patterns | outcome: OK | note: idempotency keys added to payment intent flow | track: fintech-payments
```
