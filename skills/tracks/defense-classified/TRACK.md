---
name: defense-classified
description: >
  classified system, classified network, CUI, Controlled Unclassified Information,
  ITAR, International Traffic in Arms Regulations, EAR, Export Administration Regulations,
  DoD, Department of Defense, DISA STIG, Security Technical Implementation Guide,
  RMF, Risk Management Framework, ATO, authority to operate, IATT,
  Interim Authority to Test, air-gapped, air gap, sneakernet,
  SCI, Sensitive Compartmented Information, SAP, Special Access Program,
  DFARS 252.204-7012, cleared personnel, security clearance, TS/SCI,
  NIST SP 800-171, CMMC Level 2, CMMC Level 3, CMMC advanced,
  classified cloud, IL4, IL5, IL6, impact level,
  GovCloud, JWICS, SIPRNet, NIPRNet, cross-domain solution,
  data diode, one-way transfer, removable media control,
  deemed export, export control, ECCN, EAR99
---

# Defense / Classified track

## Purpose

Classified and export-controlled systems operate under constraints that no other domain shares: the system itself may not be discussed externally, personnel must hold clearances to access it, the codebase may be ITAR-controlled (which means foreign nationals on the team need export licenses), and releases require formal government authorization rather than a team go/no-go. Unlike the Regulated / government track — which covers civilian compliance frameworks (FedRAMP, SOC 2, CMMC Level 1–2 for contractors) — this track covers systems where the data classification or technology itself is restricted: classified networks, CUI-intensive environments, air-gapped deployments, and ITAR/EAR-controlled technology.

The failure mode here is not a production outage. It is a spillage (classified data on an unclassified system), an export violation (source code reaching a non-authorized country or person), or an ATO revocation (loss of the government's authorization to operate). These consequences are irreversible and legally significant.

---

## When to activate

**Keyword signals:**
- "classified", "CUI", "ITAR", "EAR", "export control", "ECCN"
- "DoD", "DISA STIG", "RMF", "ATO", "IATT"
- "air-gapped", "air gap", "JWICS", "SIPRNet", "IL5", "IL6"
- "SCI", "SAP", "TS/SCI", "security clearance"
- "DFARS 252.204-7012", "NIST 800-171", "CMMC Level 3"
- "data diode", "cross-domain solution", "removable media control"

**Architectural signals:**
- System processes or stores data classified above Unclassified
- System or its components are subject to ITAR or EAR export controls
- Deployment environment is an air-gapped or classified network
- Personnel accessing the system must hold government clearances
- System requires government ATO or IATT before operating

---

## When NOT to activate

- FedRAMP, SOC 2, or CMMC Level 1–2 compliance for a standard government contractor with no classified data — use Regulated / government track
- HIPAA with no defense nexus — use Healthcare track
- Civilian government agency project with no classified systems or ITAR technology
- Internal security tooling that handles sensitive-but-unclassified data but does not touch a classified network

---

## Skill elevations

| Skill | In Lean | In Standard | In Rigorous |
|-------|---------|-------------|-------------|
| security-audit-secure-sdlc | Mandatory + STIG scan + export classification | Mandatory + STIG scan + penetration test | Mandatory + STIG scan + government-authorized penetration test + red team |
| architecture-review-governance | Mandatory | Mandatory + government reviewer | Mandatory + formal government architecture review |
| documentation-system-design | Mandatory (air-gapped teams cannot use cloud docs; all docs must be accessible offline) | Mandatory | Mandatory + evidence packaging for ATO artifacts |
| data-governance-privacy | Mandatory + CUI identification and handling | Mandatory + CUI registry and handling procedures | Mandatory + classification authority review |
| devops-pipeline-governance | Mandatory + classified CI/CD environment | Mandatory + classified pipeline audit | Mandatory + accredited pipeline |
| disaster-recovery | Mandatory + air-gapped backup procedures | Mandatory + backup tested in classified environment | Mandatory + multi-site classified backup |
| architecture-decision-records | Mandatory (upgrade and configuration changes must be documented for ATO maintenance) | Mandatory | Mandatory |
| formal-verification | N/A | Conditional (cryptographic protocols) | Mandatory for any custom cryptographic implementation |

Note: Nano mode is not appropriate for this track. Minimum mode is Lean; Rigorous is strongly recommended for any system touching classified data.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | Perform ITAR/EAR classification determination for all technology components; identify which personnel require clearances; define classification level of the system and its data; verify team members are cleared for the required level |
| Stage 2 (Design) | Data classification scheme documented (Unclassified / CUI / Classified); network boundary and cross-domain solution defined if required; encryption at rest and in transit specified to NSA-approved algorithms (CNSA Suite); key management designed for classified environment |
| Stage 3 (Build) | No development on unaccredited systems; source code must not leave authorized environments; STIG hardening applied to all OS and middleware configurations |
| Stage 4 (Verify) | DISA STIG scan run and findings resolved or risk-accepted by Authorizing Official; penetration test conducted by cleared personnel; all findings documented in POA&M (Plan of Action and Milestones) |
| Stage 5 (Ship) | ATO (or IATT for testing) obtained from Authorizing Official before system goes operational; classified release packaging procedure followed; change log maintained in classified environment |
| Phase 3 (Ongoing) | Continuous STIG compliance monitoring; annual RMF reassessment; ITAR/EAR export license review when team composition changes; POA&M milestone tracking |

---

## Reference injection map

| When this skill fires | Also load these references |
|-----------------------|---------------------------|
| security-audit-secure-sdlc | `references/itar-ear-controls.md`, `references/rmf-authorization-guide.md` |
| architecture-review-governance | `references/rmf-authorization-guide.md` |
| devops-pipeline-governance | `references/air-gapped-deployment-patterns.md` |
| disaster-recovery | `references/air-gapped-deployment-patterns.md` |
| documentation-system-design | `references/air-gapped-deployment-patterns.md` |
| data-governance-privacy | `references/itar-ear-controls.md` |

---

## Reference files

- `references/itar-ear-controls.md` — what triggers ITAR vs EAR, jurisdiction determination, ECCN classification, export license process, deemed export rules for foreign national team members, practical controls (repo access lists, export screening checklist)
- `references/rmf-authorization-guide.md` — RMF six-step process (Categorize → Select → Implement → Assess → Authorize → Monitor), ATO vs IATT differences, POA&M format, continuous monitoring requirements, evidence artifacts required per step
- `references/air-gapped-deployment-patterns.md` — transfer station procedures, one-way data diodes, removable media controls and sanitization, offline software update packaging, classified development environment setup, document handling in air-gapped environments

---

## Skill execution log

Track activation:
```
[YYYY-MM-DD] track-activated: defense-classified | mode: [Mode] | duration: project
```

Skill firings under this track:
```
[YYYY-MM-DD] security-audit-secure-sdlc | outcome: OK | note: STIG scan complete; 3 CAT-II findings; POA&M updated | track: defense-classified
```
