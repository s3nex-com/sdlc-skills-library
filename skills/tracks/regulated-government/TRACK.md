---
name: regulated-government
description: >
  Activates when the user mentions FedRAMP, StateRAMP, authority to operate, ATO,
  SOC 2, Type I, Type II, trust services criteria, ISO 27001, ISMS, statement of
  applicability, CMMC, defense contractor, CUI, government contract, public sector,
  or FISMA. Also triggers on explicit declaration: "Regulated track" or "Government
  track".
---

# Regulated / government track

## Purpose

This track covers products operating under a formal regulatory framework — FedRAMP Low or Moderate, SOC 2 Type I or Type II, ISO 27001, StateRAMP, CMMC Level 1-3, or equivalents like UK Cyber Essentials Plus. These frameworks share one structural demand the generic library does not enforce: every control needs written evidence, evidence must be tied to a specific control ID, and assessors must be able to walk the trail from policy to implementation to test result without you narrating it. This track elevates security, architecture governance, documentation, and change management from "do it well" to "do it and leave the evidence in a predictable place." It tightens gates so a release cannot ship without control mappings, evidence artifacts, and an approval trail that passes separation-of-duties muster. No ceremony beyond what the frameworks actually require — but every control that applies gets mapped, implemented, tested, and recorded.

The failure mode this track prevents: a team ships a compliant system but cannot prove it during fieldwork. The auditor asks "show me evidence that access is reviewed quarterly" and the answer is a Slack thread. The evidence existed; the trail did not. This track makes the trail a first-class output of every stage.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "FedRAMP", "StateRAMP", "authority to operate", "ATO", "P-ATO"
- "SOC 2", "Type I", "Type II", "trust services criteria", "CC controls"
- "ISO 27001", "ISMS", "statement of applicability", "SoA", "Annex A"
- "CMMC", "defense contractor", "CUI", "controlled unclassified information", "DFARS 7012"
- "government contract", "public sector", "FISMA", "NIST 800-53", "NIST 800-171"

Or when the system under discussion has these properties:

- A contractual obligation to deliver an audit report (SOC 2 Type II, ISO 27001 certificate, FedRAMP ATO letter) to customers or a prime contractor.
- Customer data subject to federal controls — US federal agency data, CUI, or data covered by a CJIS / IRS 1075 / CMS MARS-E agreement.
- A third-party assessor (3PAO, auditor, certification body) scheduled or anticipated within the next 12 months.
- An existing control framework inherited from a parent company or a prime contractor.
- Production hosting in a FedRAMP-authorized environment (AWS GovCloud, Azure Government, GCP Assured Workloads) where the customer is relying on your inheritance chain.

Multi-framework products — a SaaS platform pursuing both SOC 2 Type II and FedRAMP Moderate simultaneously, for example — run this track once. The overlay handles the union of evidence demands; frameworks are fingerprints on a common control vocabulary, not separate tracks.

---

## When NOT to activate

Do NOT activate this track when:

- The product handles Protected Health Information — use the Healthcare / HIPAA track. Regulated and Healthcare compose when both apply (e.g., FedRAMP Moderate for a federal health agency).
- The product handles card data — use the Fintech / Payments track. PCI DSS is its own framework and carries different evidence mechanics.
- You have a marketing commitment to "be SOC 2 ready" but no audit on the calendar and no customer requiring it — that is roadmap noise, not a track signal. Revisit when an assessor is booked.
- The compliance need is purely privacy-law driven (GDPR, CCPA, LGPD) with no control framework — use `data-governance-privacy` standalone; a track is too heavy.
- The product targets a regulated industry but your engineering team does not own any in-scope system (you write documentation, integrate read-only, or build a marketing microsite).
- An internal-only tool used by a dozen employees to do back-office work, with no customer data, no regulated data, and no audit requirement. Internal tools get the generic library.

If you are unsure, answer: will an assessor ask for evidence from this system in the next 12 months? If yes, activate. If no, skip the track and run `security-audit-secure-sdlc` + `data-governance-privacy` standalone.

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| security-audit-secure-sdlc | Mandatory | Mandatory + control mapping | Mandatory + control mapping + external audit prep | Mandatory + external audit |
| architecture-review-governance | Advisory | Mandatory | Mandatory + formal review | Mandatory + formal review + sign-off |
| documentation-system-design | Mandatory (audit docs) | Mandatory | Mandatory + evidence library | Mandatory + evidence library + annual review |
| data-governance-privacy | Mandatory | Mandatory | Mandatory | Mandatory |
| dependency-health-management | Mandatory | Mandatory | Mandatory | Mandatory + approved vendor list |
| devops-pipeline-governance | Standard | Change management | Change management + approval workflow | Change management + approval workflow + separation of duties |
| incident-postmortem | Standard | Standard | Standard + regulatory reporting | Standard + regulatory reporting + timeline requirements |
| disaster-recovery | N/A | Advisory | Mandatory (FedRAMP CP-9/CP-10 controls or equivalent; restore tested and evidence filed) | Mandatory + quarterly DR test + evidence filed under `docs/evidence/CP-10/<date>/` |
| architecture-fitness | N/A | N/A | Mandatory (separation-of-duties and least-privilege boundary rules enforced in CI) | Mandatory |
| formal-verification | N/A | N/A | Conditional (for custom auth or cryptographic protocols) | Mandatory for any custom authentication, key-management, or access-control protocol |
| chaos-engineering | N/A | N/A | Mandatory (DR test counts as a required resilience control; broaden to availability resilience experiments) | Mandatory + quarterly game day + evidence filed |

Only skills whose treatment differs from the default mode behaviour are listed. All other skills retain their mode defaults.

Notes on the additional elevations:

- `disaster-recovery` maps to FedRAMP control families CP-9 (Information System Backup) and CP-10 (Information System Recovery and Reconstitution), SOC 2 Availability criteria (A1.2), and ISO 27001 Annex A control A.17. All three frameworks require documented and tested recovery procedures. Evidence is filed under the framework's control ID.
- `architecture-fitness` at Standard+ enforces CI-level boundaries that make separation-of-duties and least-privilege architectural properties observable and provable to auditors — not just claimed in documentation.
- `formal-verification` is Conditional at Standard for custom auth or cryptographic protocols (OAuth2/OIDC implementations, custom key-derivation schemes) and Mandatory at Rigorous, where assessors increasingly accept formal proof artifacts as evidence for authentication control correctness.
- `chaos-engineering` at Standard maps to DR testing requirements common across frameworks (FedRAMP CP-4, SOC 2 CC7.5, ISO 27001 A.17.1.3). A DR test is a required control, not a nice-to-have. At Rigorous, quarterly game days produce evidence filed with the control ID.

Mode guidance:

- **Nano** is rare in this track — most regulated work cannot fit under Nano's acceptance criteria. Use Nano only for micro-changes to systems already fully in-scope where the evidence trail already exists and this change adds nothing new.
- **Lean** fits SOC 2 Type I prep and low-baseline internal tools.
- **Standard** is the default for active SOC 2 Type II, ISO 27001 certification, and FedRAMP Low / Moderate pursuit.
- **Rigorous** fits FedRAMP Moderate / High in active ATO pursuit, CMMC Level 3, and any framework where a 3PAO is actively engaged.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | Risk assessment written in the framework's language. FedRAMP = Low / Moderate / High categorization per FIPS 199. SOC 2 = Trust Services Criteria selection. ISO 27001 = scope statement and applicable Annex A controls. Output goes to `docs/evidence/risk-assessment/<date>/`. |
| Stage 2 (Design) | Control mapping table: every applicable control ID identified with its implementation approach. Named owner per control. Design doc references control IDs inline where the control is satisfied. Output goes to `docs/evidence/control-mapping/<feature>.md`. |
| Stage 3 (Build) | Evidence collected during implementation — CI log excerpts, unit test outputs, IaC plan outputs, screenshots where the framework mandates them (e.g., MFA enforcement screens). All artifacts filed under `docs/evidence/<control-id>/<YYYY-MM-DD>/`. |
| Stage 4 (Verify) | Formal test evidence per control, not just "tests passed". Penetration test for Standard mode and above, or whenever the framework requires it (FedRAMP Moderate annual pen test, SOC 2 Type II as the audit period demands). Test results archived with the control ID they cover. |
| Stage 5 (Ship) | Change approval workflow enforced: the engineer who authored the change cannot be the approver for production deployment. CODEOWNERS + branch protection must make this mechanical. Every production release logs an approval record per `references/change-management-approvals.md`. |
| Phase 3 (Ongoing) | Continuous monitoring: monthly vulnerability scans (scheduled and logged), quarterly access reviews (documented), annual risk assessment refresh, annual control re-test. Evidence filed with a date-stamped folder per cycle. |

Strictest-wins when combined with another track. Regulated + Fintech means both control evidence and PCI scope discipline are mandatory at every gate. Regulated + Healthcare at FedRAMP Moderate adds HIPAA BAA coverage and clinical audit log requirements on top of the NIST 800-53 controls.

Evidence folder layout this track enforces:

```
docs/evidence/
  risk-assessment/<YYYY-MM-DD>/
  control-mapping/<feature>.md
  <control-id>/<YYYY-MM-DD>/
    ci-<run-id>.log
    terraform-plan.txt
    screenshot-<topic>.png
    README.md            — collector, cadence, source pointer
  AC-2/<YYYY-QN>/         — quarterly access review bundle
  CA-8/<YYYY>/            — annual pen test report
```

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| any skill (generic) | Append evidence collection to the skill's output. Evidence goes to `docs/evidence/<control-id>/<date>/`. |
| security-audit-secure-sdlc | `references/fedramp-evidence-checklist.md`; `references/soc2-controls-mapping.md` |
| architecture-review-governance | `references/fedramp-evidence-checklist.md` (architecture-bearing controls); `references/soc2-controls-mapping.md` (CC A-series availability controls) |
| documentation-system-design | `references/fedramp-evidence-checklist.md` (evidence location table); `references/soc2-controls-mapping.md` (artifact mapping) |
| devops-pipeline-governance | `references/change-management-approvals.md` — enforce separation of duties; approval workflow mechanics |
| dependency-health-management | `references/fedramp-evidence-checklist.md` (SI-2, SI-3 sections); approved vendor list discipline in Rigorous mode |
| incident-postmortem | `references/vulnerability-disclosure-policy.md` (public disclosure flow); trigger regulatory notification checklist — 72h GDPR, 30d HIPAA, 1h some federal contracts |
| data-governance-privacy | `references/soc2-controls-mapping.md` (Confidentiality and Privacy criteria); `references/fedramp-evidence-checklist.md` (AC and SC families) |
| formal-verification | `references/fedramp-evidence-checklist.md` (IA and SC families — authentication and cryptographic controls where TLA+ proofs are accepted as evidence); `references/soc2-controls-mapping.md` (CC6.1 logical access controls) — file the proof artifact under `docs/evidence/<control-id>/<YYYY-MM-DD>/` |

---

## Reference files

- `references/fedramp-evidence-checklist.md` — FedRAMP Low / Moderate controls mapped to engineering evidence sources. The 14 control families at summary level plus drill-downs for the families engineers actually implement (AC, AU, CM, CP, IA, SC, SI). Evidence location table.
- `references/soc2-controls-mapping.md` — SOC 2 Trust Services Criteria (Security, Availability, Processing Integrity, Confidentiality, Privacy) mapped to engineering practices and artifacts. Engineering-owned vs ops-owned controls. Evidence patterns.
- `references/change-management-approvals.md` — approval workflow for production changes. Separation of duties enforcement. Emergency change process. Approval logging. CODEOWNERS and branch protection integration.
- `references/vulnerability-disclosure-policy.md` — VDP template ready to paste into `SECURITY.md`. Safe harbor language. Triage SLAs by severity. Public security advisory process. CVE request flow. `security.txt` conventions.

---

## Framework-specific notes

Different frameworks carry the same control vocabulary but different emphasis and cadence. Keep these differences in mind when the active framework is declared.

**FedRAMP** — NIST SP 800-53 as the control catalog. Low = 125 controls, Moderate = 325, High = 421. Authorization path is long (12-18 months typical for Moderate). Engineering evidence centers on the System Security Plan (SSP), with per-control implementation statements and continuous monitoring evidence thereafter. 3PAO involvement from day one. FedRAMP Moderate mandates annual pen test and monthly vulnerability scans — non-negotiable cadence.

**SOC 2** — AICPA Trust Services Criteria (TSC). Type I = design of controls at a point in time. Type II = operating effectiveness over a period, typically 6 or 12 months. Sample-based fieldwork: the auditor picks a date range and asks for artifacts produced during it. Evidence must exist at the time of the event, not be reconstructed later. A Type II audit with a 12-month population is the common target.

**ISO 27001** — ISMS-centric. Statement of Applicability (SoA) declares which Annex A controls apply. The ISMS processes (risk treatment, management review, internal audit) are the evidence spine. Engineering contributes to the A.8 (asset management), A.9 (access control), A.12 (operations), A.14 (development), and A.16 (incident management) controls. Surveillance audits annually, recertification every 3 years.

**CMMC** — Level 1 (Foundational) maps to FAR 52.204-21; Level 2 maps to NIST 800-171; Level 3 adds a subset of NIST 800-172. DoD contracts only. Self-assessment up through Level 1; third-party (C3PAO) for Level 2 and above. Scope is any system handling Federal Contract Information (FCI) or Controlled Unclassified Information (CUI).

**StateRAMP** — state-government analogue to FedRAMP. Same NIST 800-53 foundation with slightly lighter process. Evidence mechanics port directly.

When multiple frameworks are in play, build to the strictest. A SOC 2 Type II + FedRAMP Moderate product uses the FedRAMP evidence cadence and mapping; SOC 2 fieldwork is a near-free by-product.

---

## Skill execution log

Track activations append to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: regulated-government | mode: Standard | duration: project | framework: FedRAMP Moderate + SOC 2 Type II
```

Every skill firing under this track appends the track context:

```
[YYYY-MM-DD] security-audit-secure-sdlc | outcome: OK | next: code-implementer | track: regulated-government | evidence: docs/evidence/AC-6/2026-04-21/
```

Do not deactivate this track mid-project. A compliance scope that shrinks mid-flight is an incident, not a configuration change — run `incident-postmortem` and document the scope change explicitly.

---

## Regulatory notification timers

When `incident-postmortem` fires under this track, check these timers against the incident facts before closing the postmortem. Missing a notification window is a reportable deficiency in the next assessment.

| Regime | Trigger | Notify within |
|--------|---------|---------------|
| GDPR (EU personal data breach) | Risk to rights and freedoms of data subjects | 72 hours to supervisory authority |
| HIPAA (PHI breach) | Unsecured PHI disclosed | 60 days to HHS; 30 days to media if 500+ individuals in a state |
| FedRAMP | Any significant incident | 1 hour to AO (agency authorizing official) for US-CERT reporting |
| DFARS 7012 (CUI) | Cyber incident on covered defense information | 72 hours to DoD Cyber Crime Center |
| State breach notification laws (US) | Varies by state | Typically "without unreasonable delay"; some states fixed at 30-90 days |
| SOC 2 | No fixed regulatory timer | Customer contracts may specify — check MSAs |

These timers are legal floors. Customer contracts often tighten them further — check every affected customer's MSA / DPA for shorter obligations.
