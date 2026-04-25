# RMF authorization guide

## Overview of the Risk Management Framework

The Risk Management Framework (NIST SP 800-37) is the process the US federal government uses to authorize information systems to operate. You cannot operate a system that processes federal information without completing RMF and receiving an ATO (Authority to Operate) from an Authorizing Official (AO).

**RMF six steps:**

```
Step 1: Categorize → Step 2: Select → Step 3: Implement →
Step 4: Assess → Step 5: Authorize → Step 6: Monitor
```

---

## Step 1 — Categorize

Determine the system's security category based on the impact of a confidentiality, integrity, or availability breach.

**Impact levels (FIPS 199):**

| Impact level | Definition |
|-------------|-----------|
| Low | Adverse effect would be limited |
| Moderate | Adverse effect would be serious |
| High | Adverse effect would be severe or catastrophic |

**Security category format:** `SC = {(confidentiality, impact), (integrity, impact), (availability, impact)}`

Example: A system that handles CUI-Privacy with moderate impact to all three pillars: `SC = {(C, Moderate), (I, Moderate), (A, Moderate)}` → **Moderate system**

**Deliverable:** System Security Plan (SSP) Section 1 — System Identification and Categorization

---

## Step 2 — Select

Choose a baseline set of security controls from NIST SP 800-53 based on the system's impact level.

| Impact level | Baseline | Number of controls (approx) |
|-------------|---------|---------------------------|
| Low | Low Baseline | ~110 controls |
| Moderate | Moderate Baseline | ~310 controls |
| High | High Baseline | ~420 controls |

**Tailoring:** The baseline is a starting point. The system owner documents which controls are applied, inherited (from a cloud provider), or not applicable, and why.

**Deliverable:** System Security Plan (SSP) — complete control selection and tailoring documentation

---

## Step 3 — Implement

Implement the selected controls and document how they are implemented.

Each control in the SSP needs an implementation statement: who is responsible, how it is technically implemented, and what evidence proves implementation.

**Example (AC-2 Account Management):**
```
Implementation: All user accounts are provisioned via the identity provider (Okta).
Provisioning requires manager approval (workflow in ServiceNow ticket #).
Accounts are reviewed quarterly; inactive accounts disabled after 30 days.
Evidence: Okta provisioning logs, ServiceNow approval records, quarterly review report.
```

**Deliverable:** Completed SSP with implementation statements for all controls

---

## Step 4 — Assess

An independent assessor (or the system owner for low-impact systems) tests the controls to verify they are implemented correctly and effective.

**Who assesses:**

| System level | Assessor |
|-------------|---------|
| Low impact | System owner (self-assessment acceptable) |
| Moderate impact | Independent assessor (internal or contracted) |
| High impact | Third-Party Assessment Organization (3PAO) required for FedRAMP |

**Assessment methods:** Examine (review documentation), Interview (ask the implementers), Test (run technical tests — scan, penetration test, configuration review)

**Output:** Security Assessment Report (SAR) — list of findings with severity ratings

**POA&M (Plan of Action and Milestones):** Document all findings that are not immediately remediated, with owner, remediation plan, and milestone dates. The AO reviews the POA&M when making the authorization decision.

**Deliverable:** Security Assessment Report (SAR) + POA&M

---

## Step 5 — Authorize

The Authorizing Official (AO) reviews the SSP, SAR, and POA&M and makes one of three decisions:

| Decision | Meaning |
|---------|---------|
| ATO (Authority to Operate) | System is authorized to operate; typically 3-year term |
| IATT (Interim Authority to Test) | System may be used in a limited, controlled way for testing; not production |
| DATO (Denial of ATO) | System is not authorized; must remediate before reapplying |

**ATO package (what you give the AO):**
1. System Security Plan (SSP)
2. Security Assessment Report (SAR)
3. Plan of Action and Milestones (POA&M)
4. Executive summary

**Timeline:** Budget 4–12 months for a first ATO on a moderate system. High-impact systems can take longer. IATT can often be obtained in 4–8 weeks to start testing while full ATO is in progress.

---

## Step 6 — Monitor (Continuous Monitoring)

ATO is not permanent. The system must be continuously monitored to maintain authorization.

**Required activities:**

| Activity | Frequency |
|---------|---------|
| Vulnerability scanning | Monthly (Moderate); weekly (High) |
| STIG compliance check | Monthly |
| POA&M review and updates | Monthly |
| Security control review | Annually (sample of controls) |
| Full reassessment | Every 3 years or on significant change |

**Significant change trigger:** Any of the following require AO notification and may require a new assessment:
- New data types or sensitivity levels processed
- New external connections or interfaces
- Infrastructure changes (new cloud services, on-premises additions)
- Application code changes that affect security controls

**Deliverable:** Continuous Monitoring Plan (ConMon Plan) + monthly ConMon reports to AO

---

## ATO vs IATT — when to use each

| Use IATT when | Use ATO when |
|--------------|-------------|
| System is under development and needs real-environment testing before full assessment | System is production-ready |
| Testing non-production data in a classified environment | Processing live operational data |
| Urgency requires fielding before full ATO (with AO agreement and bounded risk) | Long-term operation is planned |

IATT is time-limited (typically 6 months) and must specify exactly what testing is permitted and what is not.
