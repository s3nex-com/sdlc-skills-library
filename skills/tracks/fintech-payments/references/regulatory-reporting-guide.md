# Regulatory reporting — when and what to file

Money-movement products have mandatory government reports. Missing a filing is a per-violation civil penalty in the US (FinCEN Title 31) and a supervisory action in the EU. This guide tells engineers what to capture, when to file, and how to automate data collection so compliance does not chase you for screenshots.

Scope: US CTR/SAR (FinCEN), EU AML/STR and PSD2 SCA. If your product operates in other jurisdictions (UK FCA, Canada FINTRAC, Singapore MAS), the shape is similar but thresholds differ — extend the capture schema per jurisdiction.

---

## United States — FinCEN

### CTR — Currency Transaction Report

- **Trigger:** Cash transaction(s) > $10,000 by or on behalf of a single customer in one business day.
- **Who files:** Financial institutions (banks, MSBs). If your product is not a regulated FI, CTR may not apply — confirm with counsel. If you facilitate cash-equivalent transactions (crypto-to-cash), it likely applies.
- **Filing window:** 15 calendar days after the triggering transaction. E-filed via BSA E-Filing System (FinCEN Form 112).
- **Aggregation:** Multiple transactions aggregating to > $10,000 in one day by the same customer count as one CTR. Structuring (intentionally splitting to avoid the threshold) is a separate criminal offense and itself SAR-reportable.

### SAR — Suspicious Activity Report

- **Trigger:** Any transaction or pattern suggesting money laundering, structuring, fraud, terrorism financing, or other illicit activity. Thresholds vary (typically $5,000 for MSBs, $2,000 for money transmitters) but there is no floor if the activity itself is suspicious.
- **Filing window:** 30 days after initial detection. Extendable to 60 days if a suspect needs to be identified. E-filed via FinCEN Form 111.
- **Confidentiality:** Hard rule — it is a crime to disclose to the subject that a SAR was filed. Systems must hide SAR status from all customer-facing surfaces.

### What to capture automatically

For any transaction above $3,000 (or the full record set in money-movement products, which is cheaper than conditional capture):

| Field | Source |
|-------|--------|
| Customer legal name | KYC profile |
| DOB, SSN/ITIN (or foreign equivalent) | KYC profile |
| Primary address, occupation | KYC profile |
| Government ID type, number, issuing state/country, expiry | KYC profile |
| Transaction amount, currency, timestamp (UTC) | Ledger |
| Counterparty name, institution, account identifier | Transaction metadata |
| Funding source (cash / wire / ACH / card / crypto address) | Payment method |
| Originating IP, device fingerprint, geolocation | Session log |
| Fraud score from provider (if scored) | Fraud integration |

Store these with the transaction, not fetched at filing time. Customer records mutate; regulators want point-in-time snapshots.

---

## European Union

### PSD2 — Strong Customer Authentication (SCA)

Not a report — an authentication requirement. Transactions that fail to satisfy SCA are rejectable by the issuer. Capture evidence that SCA was performed or that an exemption applied.

- **Authentication elements:** two of three — knowledge (password), possession (phone, hardware token), inherence (biometric).
- **Exemptions engineers must implement:** low-value (< €30, cumulative rules apply), trusted beneficiary, recurring transactions with same amount, merchant-initiated transactions, transaction risk analysis (TRA) below threshold.

Store for each card-not-present transaction:

```json
{
  "sca_status": "authenticated | exempted | failed",
  "exemption_code": "low_value | recurring | trusted_beneficiary | tra | null",
  "authentication_method": "3ds2 | otp | biometric | null",
  "eci": "05 | 06 | 07",
  "transaction_id_3ds": "xsi:..."
}
```

### AML Directive and STR

- **STR — Suspicious Transaction Report:** 6th AML Directive requires obliged entities to file with the national FIU (e.g., TRACFIN in France, BaFin in Germany). Trigger language is "knowledge, suspicion, or reasonable grounds to suspect" — subjective and intentionally broad.
- **Filing window:** Without delay; national rules range from immediate to 30 days. Check the jurisdiction you operate in.
- **Threshold-based reports:** Some member states require reports above €10,000 (EU cash payment limit coming into force). Automate the trigger rather than relying on memory.

### Transaction monitoring and reporting (EBA Guidelines)

For payment service providers, the EBA requires periodic transaction reporting including fraud rates. Capture monthly:

- Total authorized transactions, volume and count
- Fraudulent transactions, volume and count, by authentication method (SCA vs exempted)
- Per-type fraud categorisation (lost/stolen card, card-not-present, phishing, account takeover)

Automate the monthly CSV export directly from your fraud and ledger tables so the compliance team does not request it by email.

---

## Data retention windows

| Obligation | Minimum retention | Common real-world retention |
|------------|-------------------|-----------------------------|
| US BSA records (CTR, SAR, supporting docs) | 5 years from filing | 7 years |
| EU AML records (KYC, transactions, STRs) | 5 years after relationship ends | 7 years |
| PSD2 SCA evidence | 2 years | 7 years (aligns with AML) |
| PCI DSS access logs | 1 year (90d immediate) | 1 year |
| Tax records (US IRS) | 7 years | 7 years |
| Crypto travel rule records (FATF) | 5 years | 7 years |

Rule of thumb: retain transactional and KYC data for **7 years post customer-relationship closure**. Delete earlier only when a specific regime or customer-right request (GDPR erasure) requires it — and even then, transaction records on legal hold override erasure rights.

---

## Automation — where engineers actually do the work

1. **Immutable capture at transaction creation.** Every money-movement transaction inserts a row into `transaction_audit` with all the fields above. Do not rely on joins to mutable customer tables at report time.
2. **Threshold detection job.** Hourly job scans `transaction_audit` for CTR/STR/€10k triggers over rolling windows (daily for CTR, per-transaction + daily aggregation for STRs). Writes a `report_queue` row per trigger.
3. **SAR/STR manual-decision queue.** Automated triggers create draft reports; a human reviews before filing. Never auto-file a SAR — false positives create regulatory friction.
4. **Filing integration.** CTRs can be batch-submitted to BSA E-Filing. STR submission is jurisdiction-specific; most teams manually submit via FIU portal with the auto-generated payload.
5. **Retention lifecycle.** Archive transactions older than 1 year to cheaper storage (S3 Glacier, GCS Archive). Enforce legal hold tags so erasure jobs skip held records. Delete only after the retention window expires AND no hold is active.

Example threshold-detection query (daily aggregation for US CTR):

```sql
SELECT customer_id, SUM(amount_cents) AS daily_total_cents, ARRAY_AGG(transaction_id) AS ids
FROM transaction_audit
WHERE funding_source IN ('cash', 'crypto_to_fiat')
  AND jurisdiction = 'US'
  AND created_at >= $start_of_day_utc
  AND created_at < $end_of_day_utc
GROUP BY customer_id
HAVING SUM(amount_cents) > 1000000;  -- $10,000.00
```

Any row returned queues a CTR draft, attaches the snapshot, and notifies the compliance operator.

---

## What to log every time

- Every threshold breach detected, whether filed or not (keeps an audit trail that detection worked).
- Every SAR/STR draft, reviewer, decision (file / don't file / escalate), and rationale. File confidentially — access is logged separately.
- Every PSD2 SCA result per transaction, including exemption decision and which rule fired.
- Every retention-policy-driven deletion, including the record types and row counts. Regulators sometimes want to see you enforce retention both ways.
