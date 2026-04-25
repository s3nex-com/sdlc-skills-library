# ITAR / EAR export controls

## What triggers ITAR vs EAR

**ITAR (International Traffic in Arms Regulations):**
- Administered by the US State Department (Directorate of Defense Trade Controls — DDTC)
- Governs items on the US Munitions List (USML)
- Includes defense articles, defense services, and related technical data
- Once an item is ITAR-controlled, virtually all exports (including sharing with foreign nationals in the US) require a license
- **Software triggers:** Cryptography designed for military/surveillance use, software for weapons systems, technical data about USML items

**EAR (Export Administration Regulations):**
- Administered by the US Commerce Department (Bureau of Industry and Security — BIS)
- Governs dual-use items on the Commerce Control List (CCL)
- Less restrictive than ITAR; many items are EAR99 (no license required for most destinations)
- **Software triggers:** Encryption software (most commercial encryption is EAR-controlled), dual-use technology with military applications

**Decision tree:**
```
Is the item specifically designed or modified for military use?
  → Yes → Check USML → Likely ITAR
  → No → Check CCL for ECCN classification → Likely EAR

Is there no USML or CCL classification?
  → EAR99 (no license required for most non-embargoed countries)
```

---

## ECCN classification

Every software product or technology component subject to EAR has an Export Control Classification Number (ECCN) or is EAR99.

Common ECCNs for software teams:

| ECCN | Description | License required for? |
|------|-------------|----------------------|
| EAR99 | No specific classification; no license for most exports | Embargoed countries (Cuba, Iran, North Korea, Syria, Russia under current controls) |
| 5D002 | Encryption software | Broad; self-classify and notify BIS after classification |
| 5D992 | Mass-market encryption | Simplified process after classification |
| 4D001 | Software for computing (not encryption-specific) | Varies by end-user |
| 5E001 | Technology for command and control | Restricted; government review often needed |

**Action:** Have legal counsel classify your software before export or sharing with foreign nationals. Do not guess on ECCN.

---

## Deemed export rules

A **deemed export** is the release of export-controlled technology to a foreign national in the United States. This is treated the same as physically exporting the technology to that person's home country.

**Practical implications:**
- Sharing ITAR or EAR-controlled source code with a foreign national employee — even in the same US office — may require an export license
- Code reviews, documentation access, and technical discussions can all constitute deemed exports
- Cleared facilities (Special Facility Clearances) manage this with Personnel Clearance requirements and need-to-know controls

**Practical controls:**
- [ ] Maintain a list of ITAR/EAR-controlled projects with access lists
- [ ] Limit repository access to US Persons (US citizens, lawful permanent residents, protected individuals) for ITAR-controlled projects
- [ ] When adding a team member, verify citizenship/immigration status before granting access to ITAR repositories
- [ ] Consult legal before a foreign national attends a technical meeting about an ITAR-controlled system

---

## Export screening checklist

Before sharing any software, technical data, or hardware with a foreign person or entity:

- [ ] Verify the recipient is not on any denied party list:
  - BIS Denied Persons List
  - BIS Entity List
  - US Treasury OFAC SDN List
  - State Department Debarred List
- [ ] Verify the destination country is not embargoed (Cuba, Iran, North Korea, Syria, Russia under current controls — verify current list with legal)
- [ ] Confirm the item's ECCN or ITAR category
- [ ] Determine if a license is required for the destination country and end-use
- [ ] Obtain license if required; document the determination if no license required

**Tools:** BIS has a free Consolidated Screening List API for checking denied parties.

---

## Practical repository controls for ITAR projects

```
# .gitconfig or repo settings — limit to US Persons only
# Document this in the repo README:

## Access control
This repository contains ITAR-controlled technical data.
Access is restricted to US Persons (US citizens, lawful permanent residents,
and protected individuals as defined under 22 CFR 120.62).
Contact [ITAR Compliance Officer] before granting access to any team member.
```

- Store ITAR-controlled repositories in a US-only cloud region with access logging
- Enable audit logs for all repository access
- Review access quarterly; revoke promptly on team changes
