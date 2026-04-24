---
name: healthcare-hipaa
description: >
  Activates when the user mentions HIPAA, PHI, protected health information, patient
  data, clinical notes, medical records, EHR integration, HL7, FHIR, HIE, BAA,
  business associate agreement, de-identification, Safe Harbor method, Expert
  Determination, medical device, FDA 510(k), or SaMD. Also triggers on explicit
  declaration: "Healthcare track" or "HIPAA track".
---

# Healthcare / HIPAA track

## Purpose

This track covers products that handle Protected Health Information (PHI) in the US, or equivalent regulated health data elsewhere (UK NHS, EU health data under GDPR Article 9). These systems have properties the generic library does not assume: every read of a patient record must be logged and attributable, a stolen laptop with an unencrypted database is a reportable breach with a 60-day regulatory timer, every vendor that sees PHI needs a signed Business Associate Agreement, and "delete this patient's data" is both a legal right and a technical problem that cascades across backups, logs, caches, and downstream analytics. The standard 41 skills plus a mode setting do not enforce these defaults. This track elevates PHI classification, tamper-evident audit logging, BAA coverage, and HIPAA Security Rule mapping from optional to load-bearing, and tightens stage gates so a clinical build cannot ship without them. The discipline is real; the ceremony is not — a 4-person team's "compliance officer sign-off" is a documented self-review posted to the PR.

HIPAA's Security Rule (§164.308–.316) organises safeguards into three categories: **administrative** (workforce training, access management, risk analysis), **physical** (facility access, device and media controls), and **technical** (access control, audit controls, integrity, transmission security). This track's skill elevations and reference files map directly onto that structure so a finding from `security-audit-secure-sdlc` lands in the right safeguard category on the first pass. The Privacy Rule (§164.500–.534) governs permitted uses and disclosures of PHI — minimum necessary, patient rights of access and accounting, authorisation requirements — and is enforced at the data layer via field-level minimum-necessary review and at the audit layer via purpose-of-use capture on every access.

Three practical realities shape every Healthcare-track decision: (1) an incident discovered on a Friday starts the breach-notification clock immediately, not on Monday; (2) every subcontractor in the chain needs its own BAA or the chain is broken; (3) "de-identified" is a specific legal term of art, not a vibe, and informal anonymization does not take data out of HIPAA scope. Designs and pipelines built without these in mind regularly fail late-stage review and force re-architecture. The reference files in this track exist to prevent that.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "HIPAA", "PHI", "protected health information", "covered entity", "business associate"
- "patient data", "clinical notes", "medical records", "EHR integration", "EMR"
- "HL7", "HL7 v2", "FHIR", "HIE", "CCDA", "DICOM"
- "BAA", "business associate agreement"
- "de-identification", "Safe Harbor method", "Expert Determination", "Limited Data Set"
- "medical device software", "FDA 510(k)", "SaMD", "Software as a Medical Device"

Or when the system under discussion has these properties:

- The system receives, stores, transmits, or displays any of the 18 HIPAA identifiers in combination with health or treatment information.
- The system integrates with an EHR (Epic, Cerner/Oracle Health, Athena, Meditech, Allscripts) or a health information exchange.
- A covered entity (hospital, clinic, insurer, pharmacy) is the customer and your system processes data on their behalf — you are a business associate.
- Clinical decision support, care coordination, patient portals, telehealth, remote monitoring, or claims processing is in scope.

If you are unsure, answer this: can a bug in your code expose a real person's medical condition to someone not authorized to see it? If yes, activate.

Typical activation examples:

- "Build a clinician-facing app that pulls a patient's medication list from Epic via FHIR." — activate.
- "Add a remote-monitoring device that reports heart rate back to the patient's care team." — activate.
- "Stand up a data warehouse that ingests claims data from our covered-entity customers." — activate.
- "Integrate a telehealth SDK so patients can video-call a clinician." — activate.
- "Add AI summarisation over clinical notes using an external LLM API." — activate, and scrutinise the LLM vendor's BAA-eligible offering before any PHI flows outward.
- "Replace our nightly backup provider with a new one." — activate a check; the backup vendor sees PHI and needs a BAA before cutover.
- "Move observability to a new logging vendor." — activate a check; if application logs ever contain PHI (and they almost always do accidentally), the logging vendor needs a BAA.

---

## When NOT to activate

Do NOT activate this track when:

- The product is a health and fitness app that does NOT handle PHI (consumer wearables, workout trackers, nutrition logs stored client-side or in the vendor's consumer account system) — activate the Consumer track with `data-governance-privacy` emphasis instead.
- Research-only use of fully anonymized data where no HIPAA covered entity is involved and no re-identification path exists — this is research data, not PHI.
- A marketing site for a healthcare company that collects only name and email for a newsletter — that is PII, not PHI, and standard `data-governance-privacy` covers it.
- Provider directories and appointment slot listings with no patient-identifying information — these are business data, not PHI.
- Veterinary records — HIPAA protects humans; the same engineering discipline may still apply but HIPAA specifically does not.

If the data could be linked back to an individual's health status, treatment, or payment for care, you are in scope. If it genuinely cannot, you are not.

Deactivate (drop the track from the project) when scope changes remove all PHI from the system — for example, a product pivot where the clinical module is spun out to a separate service and the remaining code path handles only non-PHI practice-management data. Log the deactivation with a reason; do not silently drop.

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| data-governance-privacy | Mandatory | Mandatory + PHI classification | Mandatory + PIA + PHI classification | Mandatory + full risk assessment |
| security-audit-secure-sdlc | Mandatory | Mandatory + HIPAA Security Rule mapping | Mandatory + HIPAA + annual risk analysis | Mandatory + external audit |
| documentation-system-design | Mandatory (audit log) | Mandatory + audit log design | Mandatory + audit log + retention | Mandatory + tamper-evident audit log |
| dependency-health-management | Standard | Standard + BAA-covered vendors | Mandatory + BAA for every PHI-handling vendor | Mandatory + annual vendor review |
| incident-postmortem | Standard | + HIPAA breach notification (60d) | + HIPAA breach notification (60d) + OCR reporting | + HIPAA breach notification + state-specific |
| disaster-recovery | N/A | Mandatory (HIPAA §164.308(a)(7) contingency plan required) | Mandatory + tested restore procedure + HIPAA-compliant backup chain | Mandatory + quarterly DR drill + evidence filed |

Only skills whose treatment differs from the default mode behaviour are listed. All other skills retain their mode defaults.

Notes on the additional elevation:

- `disaster-recovery` is non-negotiable under the HIPAA Security Rule's Contingency Plan standard (§164.308(a)(7)): covered entities and business associates must maintain a data backup plan, disaster recovery plan, emergency mode operation plan, testing and revision procedures, and applications and data criticality analysis. The elevation starts at Lean — there is no HIPAA-compliant PHI system without a documented DR plan. N/A at Nano because Nano-scope changes to a PHI system should already inherit the project's existing DR plan; if no DR plan exists, the project is not Nano-scope.

Notes on the elevations:

- `data-governance-privacy` goes Mandatory even at Nano because classifying whether data is PHI is a prerequisite to every downstream control. A Nano-mode clinical feature still needs the 30-minute classification pass.
- `security-audit-secure-sdlc` at Lean and above maps findings to the specific HIPAA Security Rule safeguards, which is how the rule actually reads — "administrative safeguard: workforce authorisation", "technical safeguard: integrity controls". That phrasing is what an OCR investigator looks for.
- `documentation-system-design` at Nano still requires the audit log design — an EHR-integrated feature without an audit log is a non-starter, regardless of mode. The elevation to "tamper-evident" at Rigorous adds the cryptographic chain and WORM destination on top of append-only storage.
- `dependency-health-management` becomes Mandatory at Standard because every PHI-handling vendor must have a signed BAA before traffic flows — this is a gate check, not a cadence check.
- `incident-postmortem` adds HIPAA breach notification workflow at every mode above Nano. The 60-day statutory clock runs whether you have a process for it or not.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | PRD must declare whether PHI is in scope. If yes, the covered-entity relationship (direct covered entity, business associate, sub-business-associate) is named explicitly. |
| Stage 2 (Design) | PHI data flow diagram required. Every system that touches PHI is identified — storage, caches, logs, backups, analytics pipelines, third-party APIs. Minimum necessary principle applied: every read/write path justifies the fields it accesses. |
| Stage 3 (Build) | Audit logging for every PHI access (read and write). Encryption at rest (AES-256) and in transit (TLS 1.2+ with modern ciphers) mandatory. Access control enforced at the data layer, not only at the API layer. |
| Stage 4 (Verify) | Access control tested — a user without authorization cannot retrieve PHI through any code path (API, background job, export). Audit log tamper evidence tested — a modified log entry must be detectable. De-identification (if used) verified against the method declared (Safe Harbor or Expert Determination). |
| Stage 5 (Ship) | BAA confirmed for every third-party PHI-handling vendor. Any new vendor added since last ship must have a signed BAA before traffic flows. Release notes mention any change to the PHI data flow diagram. Backup and disaster-recovery path is confirmed HIPAA-compliant (encrypted, access-logged, in BAA scope). |
| Phase 3 (Ongoing) | Annual HIPAA risk assessment (administrative, physical, technical safeguards). Quarterly access review — list every human and service account with PHI access, confirm each is still justified. Drop what isn't. Annual BAA register re-examination bundled with the risk assessment. |

Strictest-wins when combined with another track. A Healthcare + Fintech product (e.g., a clinical billing SaaS) at the Ship gate must satisfy both BAA coverage and PCI scope review. A Healthcare + SaaS B2B product must produce both per-tenant isolation evidence and the PHI data flow diagram.

### Breach notification timeline (active during incident-postmortem)

HIPAA §164.404–410 requires the covered entity to notify affected individuals within **60 calendar days** of discovery of a breach of unsecured PHI. Business associates must notify the covered entity within the window specified in the BAA (often 10 business days or shorter; the BAA governs). If 500+ individuals are affected in a single state or jurisdiction, HHS/OCR must be notified concurrently and prominent media outlets in the affected area must be informed. Smaller breaches are reported to OCR annually by 1 March of the following year.

The 60-day clock starts at discovery, not at confirmation — guessing wrong delays the notification and compounds the violation. When `incident-postmortem` fires on a PHI-touching incident, the breach-notification workflow runs in parallel to the root-cause analysis, not after it. State-specific notification laws may add earlier deadlines and additional content requirements; in Rigorous mode those are checked on every breach.

### Minimum necessary — the principle that disciplines everything

The "minimum necessary" principle (§164.502(b)) applies to every use and disclosure of PHI except for treatment, requests by the individual, and a handful of other carve-outs. In engineering terms: a query should return the fewest PHI fields that satisfy the caller's actual need, a role should grant the fewest records that satisfy the job function, an export should include the fewest columns that answer the business question. At Stage 2, every PHI access path is justified against minimum necessary; at Stage 4, an access-control test confirms that roles cannot exceed their declared field set.

### Encryption requirements — not advisory

Encryption at rest (AES-256 or equivalent) and in transit (TLS 1.2+; TLS 1.3 preferred; no SSL, no TLS 1.0/1.1, no export ciphers) is non-negotiable under the HIPAA Security Rule's "addressable" specifications read together with the breach-notification safe harbor. Unencrypted PHI is not just a weak control — it turns an incident that might not have reached the reporting threshold into a reportable breach. Encryption failure, expired certs, misconfigured ciphers — each is a Stage 3 gate failure.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| data-governance-privacy | `references/phi-classification.md` — PHI classification takes precedence over general PII classification when the two conflict |
| data-governance-privacy (de-identification requested) | `references/de-identification-methods.md` |
| security-audit-secure-sdlc | `references/hipaa-audit-log-requirements.md` — findings are mapped to HIPAA Security Rule safeguards (administrative, physical, technical) |
| documentation-system-design (audit log design) | `references/hipaa-audit-log-requirements.md` |
| dependency-health-management (PHI-handling vendor) | `references/baa-workflow.md` |
| incident-postmortem (incident involves PHI) | trigger HIPAA breach notification workflow with 60-day statutory timeline; `references/baa-workflow.md` for sub-processor notification paths |
| code-implementer (any PHI access code path) | `references/phi-classification.md`, `references/hipaa-audit-log-requirements.md` |
| database-migration (touches a PHI table or derivative) | `references/phi-classification.md` — migration PR template must include the PHI classification checklist |
| api-contract-enforcer (endpoint returns PHI) | `references/phi-classification.md` — response schema must identify which fields are PHI; `references/hipaa-audit-log-requirements.md` for the `fields_accessed` trace |
| observability-sre-practice (logs or traces from a PHI-handling service) | `references/phi-classification.md` — log-scrubbing rules derived from the identifier list; `references/baa-workflow.md` for the observability vendor's BAA status |
| architecture-review-governance (any new service in scope) | `references/phi-classification.md`, `references/hipaa-audit-log-requirements.md`, `references/baa-workflow.md` |
| release-readiness (pre-Ship gate check) | `references/baa-workflow.md` — vendor register inspected for net-new vendors since last release |

---

## Reference files

- `references/phi-classification.md` — the 18 HIPAA identifiers, how datasets become PHI by combination (quasi-identifiers), and a worked example of stripping identifiers while preserving analytics utility.
- `references/hipaa-audit-log-requirements.md` — what must be logged, required fields, tamper evidence (append-only + cryptographic chain + WORM), 6-year retention, access patterns for log review, with a worked append-only audit log schema and queries.
- `references/de-identification-methods.md` — Safe Harbor vs Expert Determination vs Limited Data Set, when each applies, re-identification risk assessment, k-anonymity and l-diversity at a working level, worked transformation examples.
- `references/baa-workflow.md` — when a BAA is required, HHS-provided and vendor-provided templates, per-vendor BAA status tracking, renewal cadence, and what counts as a business associate (sub-contractor, cloud provider, SaaS vendor handling PHI).

---

## Composition with other tracks — what to do when they stack

| Combined with | Interaction |
|---------------|-------------|
| Fintech / Payments | Clinical billing, insurance claims processing, copay collection. Stage 5 requires both BAA coverage AND PCI scope review. Audit logs must cover both PHI access and money movement events. Reconciliation and audit log retention are both 6+ years — align the storage tier policy. |
| SaaS B2B | Multi-tenant clinical SaaS, hospital-tenanted patient portals. Tenant isolation tests (B2B) and per-tenant PHI flow diagrams (Healthcare) both required at Stage 4. A tenant's PHI leaking to another tenant is simultaneously a B2B isolation failure and a HIPAA breach — handle with both lenses. |
| Data platform / ML ops | Clinical analytics, model training on patient data, LLM-assisted clinical summarisation. Stage 2 design must show whether training data is PHI, Limited Data Set, or de-identified. If PHI flows to a model vendor, the vendor needs a BAA AND must contractually forbid training use of the data. |
| Regulated / government | Healthcare contracts with VA, IHS, or state Medicaid agencies. FedRAMP ATO stacks on top of HIPAA; strictest-wins applies to every gate. Evidence collection doubles — maintain a single evidence archive that satisfies both frameworks. |
| Real-time / streaming | Real-time vitals monitoring, alerting streams. Streaming pipeline stages must each log PHI access; audit log requirements apply to stream consumers, not just REST API endpoints. |

---

## Skill execution log

When this track activates, the line in `docs/skill-log.md` reads:

```
[YYYY-MM-DD] track-activated: healthcare-hipaa | mode: <mode> | duration: project | covered-entity: <direct|BA|sub-BA>
```

The covered-entity relationship is captured at activation because downstream gate checks (BAA flow-down, breach notification path) branch on it. A direct covered entity notifies patients and OCR. A business associate notifies the covered entity (who then notifies patients). A sub-business-associate notifies upstream. Know the position before the incident, not during it.

---

## Operating rhythm under this track

- **Every PR that touches a PHI code path**: the PR template pulls the checklists from `phi-classification.md` and `hipaa-audit-log-requirements.md`. Unchecked boxes block merge.
- **Every new vendor**: the `baa-workflow.md` checklist runs before any integration traffic begins. Register updated, BAA filed, annual review scheduled.
- **Every incident touching PHI**: breach-notification workflow kicks off in parallel to postmortem. 60-day clock from discovery.
- **Quarterly**: access review against the audit log — who has PHI access, who used it, who no longer needs it.
- **Annually**: HIPAA risk assessment (§164.308(a)(1)(ii)(A)), BAA register review, audit-log chain integrity verification, de-identification re-evaluation for any datasets claimed as de-identified.
