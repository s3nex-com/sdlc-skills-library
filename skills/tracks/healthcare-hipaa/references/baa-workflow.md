# BAA workflow — when it's required, how to track it, how to renew

A Business Associate Agreement (BAA) is the contract HIPAA requires between a covered entity (or business associate) and any third party that will create, receive, maintain, or transmit PHI on its behalf. No BAA, no PHI — send PHI to a vendor without one and you have a reportable breach before the first request completes.

The BAA is the legal lever that extends HIPAA obligations down the chain. Every vendor that touches PHI must sign one. Every sub-contractor that the vendor uses must, in turn, sign one with the vendor. The chain cannot have gaps.

---

## When a BAA is required

A BAA is required whenever a third party will **create, receive, maintain, or transmit PHI** on behalf of your organisation. Concretely:

- **Cloud infrastructure providers** holding PHI: AWS, GCP, Azure, Oracle Cloud. These vendors sign BAAs covering specific HIPAA-eligible services — not every service in the catalogue is in scope. Check the current eligibility list.
- **SaaS vendors** that process PHI: EHR integrators, clinical decision support, patient engagement, telehealth platforms, medical billing.
- **Observability and operational tools** that ingest PHI-containing data: Datadog, Sentry, New Relic, Splunk, Elastic, PagerDuty. All sign BAAs on their HIPAA-eligible tiers.
- **Email and communication** tools that carry PHI: secure email, fax-to-email, SMS for appointment reminders if the content includes PHI, patient portal push notification vendors.
- **Data warehouses and analytics** receiving any PHI: Snowflake, BigQuery, Redshift, Databricks, Looker.
- **AI/ML providers** processing PHI: OpenAI, Anthropic, AWS Bedrock, Google Vertex — only their HIPAA-eligible offerings, only under BAA. Do not send PHI to a consumer-tier API.
- **Contractors and subcontractors** (human or company) who access PHI during development, support, or operations.
- **Managed service providers** administering infrastructure that holds PHI.

A BAA is **not** required when:

- The vendor never sees PHI. A CDN serving only static marketing assets does not need one. A feature-flag vendor that receives only a hashed opaque user ID and boolean flag values does not need one — provided no PHI is sent in payloads.
- The entity is a **conduit** that merely transports encrypted data without storing it meaningfully (very narrow — ISPs, the postal service). This exception is frequently misapplied; when in doubt, sign a BAA.
- The entity is another covered entity sharing PHI for treatment purposes under the treatment exception.

**Default posture:** assume BAA required. Justify exceptions in writing.

---

## Who counts as a "business associate"

The scope is broader than many teams expect:

- **Subcontractors** performing any function that involves PHI — outsourced support, offshore development, a transcription service.
- **Cloud providers** — even when the covered entity holds the encryption keys and the cloud provider claims it "cannot see" the data, a BAA is still required. The "no-view" exception has never been ratified in regulation.
- **SaaS vendors** — any multi-tenant software platform that ingests PHI from your service.
- **Individual contractors** — if a freelance engineer will have production access, they need to be under a BAA (either signed directly or through their LLC).
- **Storage and backup providers**.
- **Destruction and disposal services** — secure shredding vendors, drive destruction services.

If the person or company could see, copy, or touch PHI, they are a business associate.

---

## Standard BAA templates

Two starting points:

### HHS-provided sample BAA

HHS publishes sample BAA language that covers the regulatory minimum. It's a starting point, not a drop-in contract. Use it to sanity-check that a vendor's BAA contains the required provisions:

- Permitted and required uses/disclosures of PHI by the business associate.
- Prohibition on further use/disclosure beyond what the contract permits or the law requires.
- Appropriate safeguards (administrative, physical, technical).
- Reporting of breaches and security incidents to the covered entity (with a specific timeline — commonly 5-10 business days, sometimes tighter).
- Flow-down to subcontractors — the BA must obtain BAAs from its own subcontractors handling PHI.
- Availability of records to HHS for compliance audits.
- Return or destruction of PHI at contract termination, or continued protection if return/destruction is infeasible.
- Termination rights if the business associate materially violates the agreement.

### Vendor-provided BAA

Most HIPAA-eligible SaaS vendors (AWS, GCP, Azure, Datadog, Snowflake, OpenAI, Anthropic, etc.) have their own standard BAA. Usually fine to sign as-is for mid-sized teams; large customers negotiate. Key things to verify before signing:

- Does the BAA cover the specific services you will use? (E.g., AWS's BAA only covers HIPAA-eligible services — using a non-eligible service for PHI is a breach even under a signed BAA.)
- What is the breach notification timeline? 24 hours is tight and common from sophisticated customers; many vendor templates start at 60 days. Push to 10 business days or better.
- Does the BAA permit the vendor to use PHI for its own "product improvement" or model training? Many consumer-facing AI BAAs carve this out; reject that carve-out.
- Is there a subcontractor flow-down clause? Vendors that themselves use sub-processors must have BAAs down the chain.
- Who holds responsibility for breaches caused by subcontractors?

---

## Tracking BAA status per vendor

Maintain a simple, canonical vendor/BAA register. A spreadsheet or a table in your ops database is fine — a 4-person team does not need a GRC platform for this. The register must answer, for any vendor, at a glance: "do we have a current BAA, and when does it need to be re-examined?"

Minimum fields:

| Field | Purpose |
|-------|---------|
| Vendor name | The legal entity |
| Service / product | E.g., "Datadog Logs" (not just "Datadog") |
| Handles PHI? | Yes / No — if No, note why and when last verified |
| BAA required? | Yes / No / N/A with reason |
| BAA signed date | ISO date |
| BAA signed version / link | Link to the signed PDF in storage |
| Breach notification SLA | From the BAA — e.g., "10 business days" |
| Subcontractor flow-down clause present | Yes / No |
| PHI training-use carve-out accepted | Yes / No — No is normal |
| Next review date | Typically signed-date + 12 months |
| Vendor security contact | Email/phone for incident reporting |
| Internal owner | Which engineer on your team owns this relationship |
| Status | Active / Pending / Terminated |

Keep the signed PDFs in a single durable location (not someone's email). Link from the register. A BAA whose signed copy cannot be found when OCR asks for it effectively does not exist.

---

## Renewal cadence

BAAs rarely have hard expiry dates. They remain in force until terminated. That creates a trap: a BAA signed in 2019 can still be in force in 2026 with terms that are obsolete (no AI carve-out, generous breach timelines, no reference to current Security Rule guidance).

Cadence:

- **Annually**: review every BAA in the register. Re-examine the vendor's current published BAA. If the vendor has issued a newer version with materially better terms (tighter breach SLA, stronger flow-down), re-sign to the new version.
- **On material change**: if the service relationship changes (new services added to scope, data flow expands), re-examine whether the existing BAA covers the expanded scope.
- **On vendor acquisition**: if the vendor is acquired, the BAA typically survives but the counter-party changes. Update the register, verify the new parent entity's obligations.
- **On sub-processor change**: if the vendor announces a new sub-processor (most vendors publish a sub-processor list), confirm it is covered under the flow-down.

Put the annual review on the same calendar as the HIPAA risk assessment — bundle the work.

---

## Offboarding a BAA — return or destruction of PHI

When a vendor relationship ends, HIPAA requires PHI be returned or destroyed at contract termination, or — if that is infeasible — continued protections be maintained indefinitely. Document the path:

- Request a certificate of destruction from the vendor.
- Confirm the PHI is removed from production, backups, and any analytic derivatives.
- Record the termination in the register with date, evidence link, and destruction certificate.
- Revoke credentials, API keys, and network paths to the vendor.

---

## Checklist — adding a new PHI-handling vendor

- [ ] Confirmed the vendor will see PHI (identified the specific data flows).
- [ ] Confirmed the specific service/tier is HIPAA-eligible per the vendor's own list.
- [ ] Reviewed the vendor's BAA — breach SLA acceptable, flow-down present, no training/improvement carve-out for PHI.
- [ ] BAA countersigned and stored in the durable signed-documents location.
- [ ] Register updated with all fields including internal owner and next review date.
- [ ] The vendor is added to the annual review cadence.
- [ ] Security contact and incident reporting path documented.
- [ ] Only after all of the above: production traffic begins.

No BAA, no traffic. Put this check in the deployment pipeline or PR template for any change that introduces a new vendor integration in a PHI-handling service.
