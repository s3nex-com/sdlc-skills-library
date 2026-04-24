# Data classification schema

Four tiers. Every field the product touches must be tagged with exactly one tier. Tagging is enforced at two points: the OpenAPI/Protobuf spec (`x-classification` extension) and the database schema (column comment or a metadata table).

---

## The four tiers

### Public
Data deliberately made available to anyone. No confidentiality obligation. Leakage has zero material impact.

Examples: published marketing copy, public API docs, OSS release notes, company blog posts, publicly listed product pricing.

Controls: none beyond normal version control. No encryption at rest required.

### Internal
Non-public. No regulatory obligation. Harm from leakage is limited to reputation or minor competitive disadvantage.

Examples: roadmaps, internal Slack archives, non-customer product telemetry, team OKRs, internal runbooks.

Controls: access restricted to employees; encrypted in transit; default-deny on external sharing.

### Confidential
Non-public business data with contractual, competitive, or financial sensitivity. Harm from leakage is material.

Examples: customer contracts, pricing tiers not publicly listed, source code (pre-release), financial records, SLA breach records, incident postmortems, customer lists, vendor contracts, unpublished metrics.

Controls: access restricted on need-to-know; encrypted at rest and in transit; audit log on access; MFA for any console or DB access; no external sharing without NDA.

### Restricted / PII
Identifies a natural person directly or indirectly, OR is specifically regulated (health, payment, biometric, minors, government ID). Harm from leakage triggers regulatory notification obligations (GDPR 72h, many US state laws have similar).

Examples:
- **Direct identifiers**: email address, full name, phone, physical address, government ID, account number
- **Indirect identifiers**: IP address, device ID (IDFA, AAID, fingerprint), precise geo-location, user ID when linkable
- **Sensitive (special category)**: health data, racial/ethnic origin, political opinions, religious beliefs, trade-union membership, sex life, sexual orientation, biometric identifiers (face, fingerprint, voiceprint), genetic data, criminal convictions
- **Regulated by sector**: payment card (PCI-DSS), protected health info (HIPAA), children's data (COPPA, under 13 in US; under 16 in several EU states)

Controls: all Confidential controls, plus: encrypted at rest with a key dedicated to PII workloads; field-level masking in non-prod environments; quarterly access review; documented lawful basis per processing purpose; retention TTL enforced by the data store; deletion workflow in place.

---

## Ambiguous cases — decision rules

### Is IP address PII?
Yes. Per the CJEU Breyer ruling and consistent DPA guidance since, IP addresses (including dynamic ones) are PII when combined with any other identifier the controller or a third party can reasonably access. Default to Restricted/PII.

### Is a device ID or advertising ID PII?
Yes. Device IDs are persistent identifiers linkable to a person. Treat as Restricted/PII. Hashing alone does not change the tier if the hash is still linkable.

### Is a user ID (internal numeric ID) PII?
Yes, when linked to a user record containing other PII. The ID itself plus the mapping table is PII. A fully pseudonymised ID with no accessible mapping is Confidential.

### Is aggregated / anonymised data PII?
Only if anonymisation is irreversible. True anonymisation means no reasonable means (including auxiliary data) allows re-identification. Aggregates with small group sizes (k<5) are not anonymised. When in doubt, treat as Restricted/PII.

### Is free-text user-generated content (support ticket, chat message) PII?
Assume yes. Users paste emails, phone numbers, account numbers into free text routinely. Tag the field Restricted/PII and apply the same controls.

### Is a session cookie PII?
Yes when linked to an account. Apply Restricted/PII controls to session stores.

### Is telemetry PII?
Depends on content. If it contains user ID, IP, device ID, or precise location: Restricted/PII. If it is anonymous counts only: Internal. Most real telemetry leans PII.

### What about internal employee data?
Employee email, salary, performance records are Restricted/PII under GDPR (employees are data subjects). Do not tag as "Internal" just because the subject is staff.

---

## Tagging conventions

### OpenAPI / Protobuf

Add an `x-classification` extension to every schema property:

```yaml
User:
  type: object
  properties:
    id:
      type: string
      x-classification: restricted-pii
    email:
      type: string
      format: email
      x-classification: restricted-pii
    display_name:
      type: string
      x-classification: restricted-pii
    plan:
      type: string
      x-classification: confidential
    theme_pref:
      type: string
      x-classification: internal
```

`api-contract-enforcer` verifies every property carries a tag. Missing tag → CI failure.

### Database schema

Use a column comment or a metadata table:

```sql
COMMENT ON COLUMN users.email IS 'classification=restricted-pii; lawful-basis=contract; retention=account-lifetime+30d';
```

Or populate a `column_metadata` table and enforce via migration review.

### Log fields

Log records carry `_classification` on every event. Downstream log-pipeline rules drop or redact by tier.

---

## Worked example — ride-sharing app

| Field | Tier | Rationale |
|-------|------|-----------|
| user.email | Restricted/PII | Direct identifier |
| user.phone | Restricted/PII | Direct identifier; regulated in many jurisdictions |
| user.home_lat / home_lng | Restricted/PII (sensitive) | Precise location; GDPR special handling |
| user.rating_avg | Confidential | Business signal; not externally linkable alone |
| trip.pickup_lat / pickup_lng | Restricted/PII (sensitive) | Precise location tied to user |
| trip.fare_amount | Confidential | Financial; tied to user via FK |
| trip.route_polyline | Restricted/PII (sensitive) | Inferable home/work; linkable |
| driver.license_number | Restricted/PII | Government ID; regulated |
| review.text | Restricted/PII | Free text; assume contains identifiers |
| app.theme_preference | Internal | No subject-linkable sensitivity |
| pricing.surge_multiplier | Confidential | Business logic |
| marketing.blog_post_body | Public | Published |

---

## Re-classification triggers

Re-run classification when:

- A field's purpose changes (new feature uses it differently)
- A new third party will receive the field
- A regulation changes (e.g. a US state passes a new privacy law covering the field)
- The field is combined with another to create a new derived attribute

Re-classification is cheap. Mis-classification is expensive.
