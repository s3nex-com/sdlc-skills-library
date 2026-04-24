# Privacy Impact Assessment (PIA / DPIA) template

A PIA for a 3–5 engineer team is one page for low-risk features, two pages for high-risk or AI Act Article 10 systems. Fill in every field. If a field is "not applicable", say why.

---

## When a PIA is mandatory

Fire a PIA if **any** of these is true:

1. A new Restricted/PII field is collected, OR an existing field is used for a new purpose
2. A new third party (vendor, sub-processor, LLM provider, analytics provider) will receive Confidential or Restricted/PII data
3. An ML or LLM model will be trained, fine-tuned, or evaluated on data originating from users
4. Data will be transferred to a non-adequate jurisdiction
5. Automated decisioning or profiling will affect an individual (GDPR Article 22; EU AI Act high-risk)
6. Large-scale processing of special-category data (health, biometric, etc.)
7. Public-space systematic monitoring (CCTV, tracking)

If none apply but you are uncertain, write a one-paragraph "PIA lite" to document the reasoning.

---

## PIA template

```markdown
# PIA — {feature or system name}

**Date:** YYYY-MM-DD
**Owner:** {engineer driving the feature}
**Reviewer:** {engineering lead or designated privacy reviewer}
**Linked artefacts:** PRD #___, DESIGN.md #___, ADR #___

---

## 1. Trigger
Which of the PIA triggers applies? (1–7 from above). One sentence per applicable trigger.

## 2. Purpose of processing
In plain English: what problem are you solving, for whom? Why does this require processing personal data specifically?

## 3. Data inventory
| Field | Tier | Source | Purpose | Retention | Minimised form |
|-------|------|--------|---------|-----------|---------------|
| ... | ... | ... | ... | ... | ... |

## 4. Lawful basis (GDPR Art. 6)
State one basis per processing purpose. If consent: how is it collected, how is it revocable? If legitimate interests: attach a 3-line balancing test (purpose, necessity, subject rights impact).

For special-category data, also state the Article 9 basis (explicit consent, employment law, vital interests, public interest, legal claims).

For CCPA: state the business purpose. Confirm whether any processing counts as "sale" or "sharing" (broad definitions — check the California AG's regs).

## 5. Third parties and sub-processors
| Third party | Role | Data shared | Location | DPA? | SCCs? | Sub-processor list reviewed? |
|-------------|------|-------------|----------|------|-------|------------------------------|
| ... | processor | email, IP | US | yes | yes | yes |

## 6. Cross-border transfers
Source jurisdiction → destination jurisdiction. State the transfer mechanism (adequacy, SCCs + TIA, derogation). If SCCs, attach the Transfer Impact Assessment.

## 7. Data subject rights
- Access request workflow: how will a request be received, verified, fulfilled, within what SLA?
- Erasure workflow: which systems, including backups, must delete; what is the backup age-out window?
- Portability workflow: what format (JSON/CSV), delivery mechanism?
- Rectification workflow: who can correct, with what audit log?
- Objection / opt-out: for legitimate-interest and marketing processing, how does the subject opt out?

## 8. Security controls (delegate to security-audit-secure-sdlc)
Summarise: encryption at rest, encryption in transit, access controls, audit logging, key rotation. Cross-reference the threat model.

## 9. Risk assessment
| ID | Risk | Likelihood (1–5) | Impact (1–5) | Score | Mitigation | Residual risk |
|----|------|------------------|--------------|-------|------------|---------------|
| PR-001 | Third-party breach exposes email list | 2 | 4 | 8 | DPA, encryption, vendor SOC 2 audit | Acceptable |
| PR-002 | Over-retention beyond legal minimum | 3 | 3 | 9 | TTL enforced in DB | Acceptable |
| PR-003 | SAR cannot be fulfilled in 30d | 2 | 3 | 6 | Runbook, on-call rotation | Acceptable |

## 10. AI Act addendum (only if AI/ML feature processes personal data)

### Article 10 — Data governance (high-risk systems)
- Training dataset source(s): ...
- Dataset size and collection period: ...
- Known biases and steps to mitigate: ...
- Pre-processing steps (cleaning, labelling, augmentation): ...
- Data quality validation method: ...
- Personal data in training set: how was lawful basis established? was anonymisation attempted?

### Article 13 — Transparency
- How are users told an AI system is in use? (UI disclosure, not just privacy policy)
- What information is surfaced: purpose, data used, confidence/limitations, human override?
- Instructions for use provided to the deployer (if the team is the provider)?

### Article 50 — General transparency (all AI systems, not only high-risk)
- Is synthetic or AI-generated content labelled?
- Are users interacting with a chatbot explicitly informed?

### Article 22 GDPR — Automated decision-making
- Does the system make decisions producing legal or similarly significant effects on a person?
- If yes: human-in-the-loop process? right-to-explanation surface?

## 11. Decision

- [ ] APPROVED — proceed as designed
- [ ] APPROVED WITH CONDITIONS — list conditions; each condition must have an owner and due date
- [ ] BLOCKED — list blockers; escalate or redesign

**Conditions / blockers:**

**Re-review trigger:** Any material change to data categories, third parties, purpose, or retention triggers a re-PIA.

**Sign-off:** {engineering lead name}, {date}
```

---

## Worked example — see SKILL.md "Output format" section

The SKILL.md file includes a completed PIA for an AI-powered ticket summariser. Use it as the reference pattern for an AI feature that processes Restricted/PII via a third-party LLM.

---

## Common mistakes to avoid

- **Stating "consent" as lawful basis for core product functionality.** If the user cannot use the product without the processing, consent is not freely given. Use "contract".
- **Skipping the balancing test for legitimate interests.** Three lines minimum: purpose, necessity, why the subject's rights are not overridden.
- **Listing "security" as a retention justification for PII beyond log windows.** Security logs retain the minimum needed for detection; they do not justify indefinite raw-PII retention.
- **Assuming a US-based vendor with a DPA is enough for EU data.** You still need SCCs and a Transfer Impact Assessment.
- **Treating the privacy policy as the Article 13 AI disclosure.** Users must see the AI disclosure in-product, at the point of use.
- **Writing the PIA after the feature ships.** The PIA informs the design; running it after is paperwork, not governance.

---

## Output location

Save the completed PIA as `docs/pia/{feature-slug}.md`. Link it from the feature's DESIGN.md. Keep PIAs in version control — they are part of the audit trail.
