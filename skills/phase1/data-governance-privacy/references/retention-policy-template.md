# Data retention policy template

Retention is enforced by the data store, not by a human intention. Every data store the team runs gets one row in the retention register. Every row names a mechanism (TTL, S3 lifecycle rule, scheduled deletion job, etc.) — never "we will delete it manually".

---

## Default retention periods

Use these defaults unless a legal requirement overrides. Shorter is almost always better; justify any extension.

### By tier

| Tier | Default retention | Rationale |
|------|-------------------|-----------|
| Public | No limit | No sensitivity |
| Internal | 7 years or business-need-based | Align with financial/tax records if relevant |
| Confidential | Per contractual obligation; default 7 years for financial data | Contract, tax, audit |
| Restricted/PII | Minimum needed for declared purpose; default "account lifetime + 30 days" | GDPR minimisation, CCPA |

### By system type

| System | Contains PII? | Default retention | Mechanism |
|--------|---------------|-------------------|-----------|
| Application logs | No | 90 days | Log pipeline TTL |
| Application logs | Yes (IP, user ID, session) | 30 days raw; then IP truncated / user ID hashed | Log pipeline rule |
| Security / audit logs | Yes | 12 months | SIEM retention config |
| Error tracking (Sentry etc.) | Often yes | 90 days | Tool setting; PII scrubbing rules on capture |
| Application DB — core records | Yes | Account lifetime + 30 days | Scheduled nullification job |
| Application DB — derived/analytics FKs | Pseudonymised | Account lifetime (retain pseudonym) | Keep after account deletion |
| Analytics warehouse (Snowflake / BigQuery) | Pseudonymised | 24 months | dbt partition drop |
| Data lake (raw events) | May contain PII | 30 days raw; then pseudonymised | S3 lifecycle + ETL |
| Backups | Mirror source | 35 days rolling | Backup tool retention |
| Support tickets | Yes | 24 months after ticket closure | Helpdesk tool setting + scheduled purge |
| Email archives (transactional) | Yes | 12 months | Mail provider retention |
| CI/CD artefacts | No | 90 days | Artifactory TTL |
| ML training datasets | Often yes | Per model lifecycle + 1 release | Document in model card |
| ML prompt/response logs (LLM features) | Yes | 30 days with PII redaction | Log pipeline rule |

---

## Legal overrides — retain longer than default

These override the default **upward** when applicable. Document the override in the retention register.

| Obligation | Data | Retention |
|------------|------|-----------|
| EU tax / invoicing | Invoices, tax records | 7–10 years (varies by state: DE 10y, FR 10y, UK 6y) |
| US IRS | Tax records | 7 years |
| AML / KYC (EU 5AMLD, FATF) | Customer ID records for regulated entities | 5 years post relationship end |
| HIPAA (US) | Protected health info | 6 years from creation or last use |
| PCI-DSS | Cardholder data | Minimum necessary; usually tokenised → retain token, not PAN |
| Employment records (most jurisdictions) | HR records | 3–7 years post-termination |
| Product liability | Safety-related records | 10 years typical |
| Litigation hold | Any relevant data | Until hold lifted |

Legal hold always overrides normal retention. The engineering team needs a named owner who can suspend TTL on a data store when a hold is issued.

---

## Legal overrides — retain shorter than default

These override the default **downward**. Respect them even when the business wants longer.

| Rule | Requirement |
|------|-------------|
| GDPR Article 5(1)(e) — storage limitation | No longer than necessary for declared purpose |
| GDPR right to erasure (Article 17) | Delete within 30 days of valid request |
| CCPA right to delete | Delete within 45 days of verified request |
| Children's data (COPPA / UK children's code) | Minimum necessary; parental consent-dependent |
| Consent-revocation | On revocation, delete or anonymise data collected under that consent |

---

## Deletion mechanism patterns

### TTL in the data store
Preferred when supported. DynamoDB TTL, Redis EXPIRE, MongoDB TTL index, Elasticsearch ILM. The store deletes without human intervention.

### Lifecycle rule
S3 lifecycle, GCS object lifecycle management, Azure blob lifecycle. Transitions and deletions are policy-driven. Audit the rules quarterly; drift is easy.

### Scheduled nullification job
For relational DBs where rows carry FKs that must be preserved but PII columns must be cleared. Daily job:

```sql
UPDATE users
SET email = NULL,
    name = NULL,
    phone = NULL,
    pii_nulled_at = NOW()
WHERE deleted_at < NOW() - INTERVAL '30 days'
  AND pii_nulled_at IS NULL;
```

The row survives; the PII does not.

### Tombstone-and-purge for backups
Backups cannot be updated in place. Workflow: record the erasure request in a tombstone table; on each backup ageing out, the subject's data ages out with it. State the backup window (e.g. 35 days) in the PIA so the total erasure SLA is transparent.

### Pseudonymisation
For analytics warehouses: replace direct identifiers with a stable pseudonym ID at ingestion. The mapping table lives in a restricted vault; the warehouse holds only pseudonyms. At retention end, drop partitions — no mapping lookup needed.

---

## Retention register format

Keep this as a single file, `docs/retention-register.md`, updated by the data-governance-privacy skill on every feature change.

```markdown
# Retention register

| Data store | Classification | Retention | Override (if any) | Mechanism | Owner | Last reviewed |
|------------|----------------|-----------|-------------------|-----------|-------|---------------|
| postgres.users | Restricted/PII | Account lifetime + 30d | — | Daily nullification job | data-platform | 2026-04-20 |
| postgres.invoices | Confidential | 10 years | EU tax law | Cold storage after 2y; delete at 10y | finance-eng | 2026-04-20 |
| s3://logs-raw | Restricted/PII | 30d | — | S3 lifecycle rule | platform-eng | 2026-04-20 |
| s3://backups | Mirror source | 35d rolling | — | Backup tool config | platform-eng | 2026-04-20 |
| snowflake.events | Pseudonymised | 24 months | — | dbt partition drop | analytics | 2026-04-20 |
| sentry | Restricted/PII | 90d | — | Sentry project setting | platform-eng | 2026-04-20 |
| zendesk | Restricted/PII | 24 months post-close | — | Zendesk automation + purge script | support-ops | 2026-04-20 |
| snowflake.llm_prompts | Restricted/PII (redacted) | 30d | — | dbt daily purge | ai-platform | 2026-04-20 |
```

---

## SAR / erasure workflow template

```markdown
# Subject rights workflow

**Receiving channel:** privacy@{domain} → auto-forwards to #privacy-requests Slack channel
**Verification:** require reply from account email + one of: 2FA confirmation, account ID, recent invoice number
**SLA:** 30 days (GDPR), 45 days (CCPA). Ack within 72h.

## Access (SAR)
1. Engineer-on-call receives request
2. Run `scripts/sar-export.py --user-id=<id>` — generates JSON from all stores listed in retention register
3. Review for third-party data that should not be disclosed (e.g. other user content in shared objects)
4. Deliver via secure link; link expires in 7 days
5. Log the fulfillment in `docs/subject-requests.md` (request date, fulfilment date, subject ID hash)

## Erasure
1. Engineer-on-call receives request; verify identity
2. Confirm no legal hold applies
3. Run `scripts/erasure.py --user-id=<id>` — tombstones the subject, nulls PII columns, removes from active caches, marks backups for age-out-deletion
4. Notify third-party processors per DPA (30-day propagation)
5. Confirm to subject with date of erasure and backup age-out date
6. Log in `docs/subject-requests.md`

## Rectification / portability / objection
Similar workflows. Rectification updates the record with audit log entry; portability returns the SAR JSON in machine-readable form; objection sets an opt-out flag and purges downstream processing that relied on legitimate interest.
```

---

## Review cadence

- Retention register: reviewed every quarter by the engineering lead
- Deletion mechanisms: tested every 6 months (simulated erasure on a test account; verify purge across all stores)
- Legal overrides: reviewed annually or on regulatory change
- AI Act Article 10 data governance reviews for high-risk systems: at every model retraining and at least annually
