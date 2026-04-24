---
name: data-governance-privacy
description: >
  Activate when classifying data (PII, sensitive, internal, public), running a Privacy Impact
  Assessment (PIA/DPIA), defining retention or deletion policies, designing GDPR/CCPA compliance
  workflows, handling subject access requests (SAR) or right-to-erasure, evaluating cross-border
  data transfers (EU SCCs, adequacy decisions), scoping data minimisation, reviewing new third-party
  data sharing, or assessing EU AI Act Article 10/13 data transparency obligations for an ML/LLM
  feature that trains on user data. Use before a feature that collects, stores, shares, or trains
  on user data is shipped.
---

# Data governance and privacy

## Purpose

Make sure every byte of user data the team handles is classified, justified by a lawful basis, retained no longer than necessary, and auditable end-to-end. Security keeps data safe; privacy makes sure holding it was lawful in the first place. This skill produces the classification, the PIA, and the retention rules. Downstream skills enforce them.

---

## When to use

Fire this skill when any of the following is true:

- A new feature collects data from users, customers, or employees that was not collected before
- A new third party (SaaS vendor, sub-processor, analytics provider, LLM API) will receive user data
- A feature trains or fine-tunes an ML or LLM model on data that originated from users
- The team is scoping retention, deletion, or archival policies for a data store
- A subject access request, deletion request, or data-portability request has arrived and no workflow exists
- Data will cross a border (EU → US, EU → non-adequate jurisdiction, or vice versa)
- A new data flow crosses trust boundaries inside the product (e.g. replication to analytics warehouse, pushing to a third party)
- EU AI Act high-risk classification applies: the feature is biometric, scoring, or decisioning on individuals — Article 10 (data governance) and Article 13 (transparency) obligations trigger

---

## When NOT to use

- Security threats, STRIDE threat modelling, secure coding, encryption, secret management → `security-audit-secure-sdlc`
- Non-privacy technical or delivery risks (scope, schedule, tech-debt) → `technical-risk-management`
- Informing stakeholders or leadership about a privacy event, communicating handling decisions, or coordinating a cross-team response → `stakeholder-sync`
- Building the data dictionary, ERD, or schema documentation → `documentation-system-design`
- Designing the API contract that exposes personal data → `specification-driven-development`
- Post-incident breach response (once an incident is declared) → `incident-postmortem`

Privacy and security are complementary: security means "is this data locked down?"; privacy means "should we be holding it at all, and did we tell the subject?". Run both skills on any feature touching user data.

---

## Process or checklist

### Step 1 — Classify every data element

For every field the feature collects, stores, or transmits, assign one of four tiers:

| Tier | Definition | Examples |
|------|-----------|----------|
| Public | Intentionally public; no confidentiality obligation | Marketing copy, published docs, OSS release notes |
| Internal | Non-public, no regulatory obligation; damage if leaked is reputational only | Roadmaps, internal dashboards, non-customer telemetry |
| Confidential | Non-public business data; contractual or competitive obligation | Customer contracts, pricing, source code, financials, SLA breach records |
| Restricted / PII | Identifies a natural person directly or indirectly, OR is regulated (health, payment, minors) | Email, IP address, device ID, name, physical address, payment card, health data, government ID, precise geo-location, biometric data |

Output: a classification table (see `references/data-classification-schema.md` for field-level examples and the full tier rules).

### Step 2 — Run a Privacy Impact Assessment (PIA) if any trigger fires

A PIA is required when **any** of these are true:

- Any Restricted/PII field is newly collected, or an existing field is used for a new purpose
- A new third party will receive any Confidential or Restricted/PII data
- An ML or LLM model will be trained or fine-tuned on data originating from users
- Data will cross a border into a non-adequate jurisdiction
- Automated decisioning or profiling will occur (including AI Act high-risk systems)

Use `references/pia-template.md`. A PIA for a small team is 1–2 pages, not 40.

### Step 3 — Nail the lawful basis (GDPR Article 6)

Pick exactly one lawful basis per processing purpose. If you cannot pick one cleanly, do not collect the data.

| Basis | Use when | Do not use when |
|-------|----------|----------------|
| Consent | Marketing, analytics cookies, optional profiling | Core product functionality (use contract instead) |
| Contract | Delivering the paid product or a free-tier service the user signed up for | Processing beyond what is needed to deliver the service |
| Legal obligation | Tax records, AML/KYC, regulated industry logging | Anything where you are choosing to process |
| Vital interests | Life-threatening situations only | Almost never applies to SaaS |
| Public task | Public authorities exercising official functions | Private companies (almost never) |
| Legitimate interests | Fraud prevention, security logs, B2B marketing to existing contacts | Anything involving children, sensitive data, or surprising the user |

Document the basis in the PIA. For CCPA, document the "business purpose" and whether any "sale" or "sharing" of personal information occurs.

### Step 4 — Apply data minimisation

For every field, answer: (a) why do we need it, (b) what is the minimum form we need it in (full value, hashed, truncated, aggregated), (c) how long do we need it for. If you cannot answer all three, drop the field. Document minimisation decisions in the PIA.

### Step 5 — Set a retention period per tier

Use defaults from `references/retention-policy-template.md` unless a legal requirement says otherwise:

| Tier / category | Default retention | Override trigger |
|-----------------|-------------------|------------------|
| Application logs (no PII) | 90 days | Security incident → extend 12 months |
| Application logs (contains IP/user ID) | 30 days, then hashed | Legal hold |
| Restricted/PII — core product data | Account lifetime + 30 days (delete after) | Legal obligation (tax: 7y; AML: 5y) |
| Restricted/PII — support tickets | 24 months after closure | Unresolved dispute |
| Analytics events (pseudonymised) | 24 months | Business need documented |
| Backup data | 35 days rolling | Disaster recovery SLO |

Configure retention as a TTL in the data store, not as a "we mean to delete it" policy.

### Step 6 — Design the deletion and access workflow

Every system holding Restricted/PII data must support:

- Subject access request (SAR): export all data for a subject within 30 days (GDPR), 45 days (CCPA)
- Right to erasure: delete all data for a subject within 30 days, including backups (tombstone + purge on next backup cycle)
- Data portability: machine-readable export (JSON or CSV)

Document the workflow (queue, owner, SLA, verification step) in the PIA. If backups cannot be purged per-subject, document the backup retention window so erasure completes when the oldest backup ages out.

### Step 7 — Cross-border transfer check

If any Restricted/PII leaves the origin jurisdiction:

- EU → adequate country (list: UK, Canada-commercial, Japan, South Korea, Switzerland, etc.): no extra paperwork
- EU → non-adequate (US, India, most others): Standard Contractual Clauses (SCCs) + Transfer Impact Assessment (TIA)
- US (CCPA) → anywhere: no specific paperwork, but contract terms must mirror CCPA obligations
- Any third party processing PII on your behalf: Data Processing Agreement (DPA) in place before production

### Step 8 — EU AI Act triggers (effective 2026)

If the feature is AI-based and operates on personal data:

- **Article 10 (high-risk systems)** — training, validation, and test data must be relevant, representative, free of errors, and complete for the intended purpose. Document the dataset: source, size, collection period, known biases, pre-processing steps.
- **Article 13 (transparency)** — users must be told that an AI system is in use, what it does, and what data it uses. Surface this in the UI, not only in the privacy policy.
- **Article 50 (general AI transparency)** — synthetic content must be labelled; interactions with AI systems must be disclosed.

High-risk systems include: biometric identification, critical infrastructure, education/vocational scoring, employment decisions, essential service access, law enforcement, migration, justice.

### Step 9 — Produce the artefacts and hand off

Outputs (attached to the design doc):

- Data classification table for the feature
- Completed PIA (if triggered)
- Retention policy entry (one row per data store)
- Lawful basis statement
- SAR/erasure workflow (if Restricted/PII is touched)

Handoffs:

- `design-doc-generator` — incorporate the classification, retention, and workflow into the DESIGN.md
- `security-audit-secure-sdlc` — threat-model the privacy controls alongside the security controls
- `documentation-system-design` — update the public privacy policy and any data dictionary
- `api-contract-enforcer` — verify that PII fields carry the correct `x-classification` tag in the OpenAPI spec

---

## Output format with real examples

### Data classification table

```
## Data classification — feature: user profile export

| Field | Tier | Lawful basis | Retention | Minimised form | Cross-border? | Notes |
|-------|------|--------------|-----------|----------------|---------------|-------|
| email | Restricted/PII | Contract (Art 6(1)(b)) | Account lifetime + 30d | Full value | EU→US (SCCs) | Used for login |
| ip_address | Restricted/PII | Legitimate interest (security) | 30d, then SHA-256 | Truncated /24 after 30d | EU→US (SCCs) | Fraud detection |
| plan_tier | Confidential | Contract | Account lifetime | Full | EU→US (SCCs) | Billing |
| theme_pref | Internal | Contract | Account lifetime | Full | EU→US (SCCs) | UI preference |
| marketing_optin | Restricted/PII | Consent (Art 6(1)(a)) | Until revoked + 30d | Boolean | EU→US (SCCs) | Revocable in UI |
```

### PIA summary (first page)

```
## PIA — feature: AI-powered ticket summariser
**Date:** 2026-04-20  **Owner:** athanasios  **Reviewer:** eng-lead
**Trigger:** LLM processing of Restricted/PII (support ticket bodies)

**Purpose of processing:** Summarise a customer support thread for the agent using an external LLM.
**Data categories:** ticket body (may contain name, email, account details), ticket metadata.
**Lawful basis:** Legitimate interest (efficient support delivery); balanced against subject rights by (a) redacting PII pre-prompt, (b) no LLM training on submitted data (contract with provider), (c) opt-out flag per account.
**Third parties:** Anthropic (LLM provider) — DPA in place, SCCs signed, US hosting.
**Retention:** Prompt/response not persisted beyond the request. Summary persisted 90d then deleted.
**Residual risks:** Prompt-injection-driven data exfiltration (mitigation: output sanitisation; see security-audit).
**Decision:** APPROVED with conditions (PII redaction, opt-out, quarterly review).
```

### Retention policy entry

```
| Data store | Classification | Retention | Deletion mechanism | Owner |
|------------|---------------|-----------|-------------------|-------|
| postgres.users | Restricted/PII | Account lifetime + 30d | Scheduled job daily; nulls PII columns, keeps anonymised row for analytics FK | data-platform |
| s3://logs-raw | Restricted/PII | 30d | S3 lifecycle rule → delete | platform-eng |
| snowflake.events | Confidential (pseudonymised) | 24 months | dbt model; drops partitions older than 24m | analytics |
```

---

## Skill execution log

Every firing appends one line to `docs/skill-log.md`:
`[YYYY-MM-DD] data-governance-privacy | outcome: OK|BLOCKED|PARTIAL | next: <skill> | note: <brief>`

Example:
`[2026-04-20] data-governance-privacy | outcome: OK | next: design-doc-generator | note: PIA approved for ticket summariser with PII-redaction condition`

If `docs/skill-log.md` does not exist, create it per the header defined in `sdlc-orchestrator`.

---

## Reference files

- `references/data-classification-schema.md` — the four-tier classification scheme with concrete field-level examples, tagging conventions for OpenAPI and database columns, and decision rules for ambiguous cases (e.g. IP address, device ID, user-generated content).
- `references/pia-template.md` — the Privacy Impact Assessment template with triggers, scope, lawful-basis selector, risk matrix, mitigation design, AI Act Article 10/13 addendum, and sign-off block. One page for low-risk features; two for high-risk.
- `references/retention-policy-template.md` — default retention periods by data tier and system type, legal override table (tax, AML, health, employment), deletion mechanism patterns (TTL, lifecycle rule, tombstone-and-purge), and the SAR/erasure workflow template.
