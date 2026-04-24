# SOC 2 controls mapping

SOC 2 evaluates controls against the AICPA Trust Services Criteria (TSC). Security is mandatory; the other four (Availability, Processing Integrity, Confidentiality, Privacy) are optional and selected based on what you tell customers you do. Most B2B SaaS audits target Security + Availability + Confidentiality. Privacy is added when you process personal data beyond "we have users with emails". Processing Integrity is added when you make numerical claims (financial, scientific, measurement).

Controls are numbered by category: CC (Common Criteria — the Security basis), A (Availability), C (Confidentiality), PI (Processing Integrity), P (Privacy).

This document maps each TSC to the engineering practice that produces its evidence. Ops-owned rows exist so engineers know what they do NOT have to write.

---

## Common Criteria (CC) — Security (mandatory)

### CC1 — Control Environment

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC1.1 Integrity and ethical values | Ops (HR) | — |
| CC1.2 Board oversight | Ops (exec) | — |
| CC1.3 Organizational structure | Ops (HR) | Org chart in onboarding doc if eng leads are in scope |
| CC1.4 Commitment to competence | Ops (HR) | Engineering role definitions, hiring criteria |
| CC1.5 Accountability | Ops | Engineering ownership (CODEOWNERS) doubles as accountability evidence |

### CC2 — Communication and Information

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC2.1 Quality information | Mixed | Monitoring dashboards, data classification doc |
| CC2.2 Internal communication | Ops | — |
| CC2.3 External communication | Ops | Public status page, security.txt, VDP |

### CC3 — Risk Assessment

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC3.1 Objectives | Ops | — |
| CC3.2 Risk identification | Engineering | Threat model output, risk register from `technical-risk-management` |
| CC3.3 Fraud risk | Mixed | Audit log of privileged actions, anomaly detection |
| CC3.4 Change in risk | Engineering | Risk register updated on architecture changes, per ADR |

### CC4 — Monitoring Activities

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC4.1 Ongoing evaluation | Engineering | Monitoring config, SLO dashboards |
| CC4.2 Communicating deficiencies | Mixed | Incident postmortems, ticket flow |

### CC5 — Control Activities

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC5.1 Control activities selected | Mixed | Control mapping table (per Stage 2 gate) |
| CC5.2 Technology controls | Engineering | IaC policy-as-code, CI gates, automated checks |
| CC5.3 Policies and procedures | Ops | Runbooks referenced from policies |

### CC6 — Logical and Physical Access (highest engineering density)

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC6.1 Logical access software | Engineering | IAM config, auth service config, RBAC policy files |
| CC6.2 User authentication | Engineering | MFA enforcement config, SSO/SAML/OIDC integration |
| CC6.3 Access removal | Mixed | Offboarding runbook, quarterly access review report |
| CC6.4 Physical access | Ops | Cloud provider inherited |
| CC6.5 Logical/physical boundaries | Engineering | Network segmentation diagram, VPC/subnet config |
| CC6.6 External system access | Engineering | API key management, partner IP allowlists |
| CC6.7 Data transmission | Engineering | TLS config, cert inventory, mTLS where applicable |
| CC6.8 Malicious software | Engineering | Container image scanning in CI, endpoint protection |

### CC7 — System Operations

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC7.1 Configuration vulnerabilities | Engineering | Vuln scan schedule, patch log |
| CC7.2 Monitoring events | Engineering | Log forwarding config, SIEM rules |
| CC7.3 Evaluating security events | Engineering | Alert runbooks, on-call rotation |
| CC7.4 Responding to incidents | Mixed | Incident response runbook, postmortem archive |
| CC7.5 Recovering from incidents | Engineering | DR runbook, backup restore test logs |

### CC8 — Change Management

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC8.1 Authorized changes | Engineering | PR approval workflow, CODEOWNERS, deploy approval log. See `change-management-approvals.md`. |

### CC9 — Risk Mitigation

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| CC9.1 Business disruption risk | Engineering | DR plan, chaos test results |
| CC9.2 Vendor and business partner risk | Mixed | SBOM, vendor security review checklist, approved vendor list |

---

## A — Availability (commonly elected)

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| A1.1 Capacity planning | Engineering | Load test results, capacity forecasts, autoscaling config |
| A1.2 Environmental protection | Ops | Cloud provider inherited |
| A1.3 Recovery and continuity | Engineering | DR runbook, RTO/RPO evidence, backup test logs |

If Availability is elected, SLO definitions, error budget tracking, and DR test results become primary evidence. The `observability-sre-practice` skill output maps directly here.

---

## C — Confidentiality (commonly elected)

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| C1.1 Confidential information identified | Mixed | Data classification policy, tagged database schema |
| C1.2 Confidential information disposed | Engineering | Deletion runbook, retention enforcement cronjob logs |

Data classification needs to be machine-queryable — tags on buckets, columns, or tables. "We have a spreadsheet somewhere" fails C1.1.

---

## PI — Processing Integrity (elect when numbers matter)

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| PI1.1 Processing requirements | Engineering | Specification, acceptance test suite |
| PI1.2 System inputs | Engineering | Input validation tests, schema validation library |
| PI1.3 System processing | Engineering | Integration tests, reconciliation tests |
| PI1.4 System outputs | Engineering | Output contract tests, API contract enforcer output |
| PI1.5 System storage | Engineering | Database constraint definitions, integrity check jobs |

If you claim accuracy in marketing or contracts, elect Processing Integrity. Ledgers, analytics platforms, measurement products all need this.

---

## P — Privacy (elect when you process personal data beyond basic account info)

| Control | Owner | Engineering artifact |
|---------|-------|----------------------|
| P1.0–P8.0 | Mixed | Privacy policy (ops), DSAR runbook (engineering), data flow diagram (engineering), subprocessor list (ops), deletion verification (engineering) |

Privacy overlaps with GDPR/CCPA — if you already run `data-governance-privacy`, most of the artifact set is done. Map existing artifacts to the P-series criteria rather than writing new ones.

---

## Evidence patterns

| Evidence type | Typical source | How the auditor sees it |
|---------------|---------------|--------------------------|
| Configuration | IaC repo, git at a tagged release | Terraform plan output, screenshot of setting |
| Change approval | GitHub PR history | Export of PRs for a sample window, showing reviewer ≠ author |
| Access review | Periodic script output | CSV of users + roles + last-used date, reviewer sign-off comment |
| Logging | Log aggregator | Sample query showing event type was captured during the audit window |
| Incident response | Postmortem archive | Full postmortem doc with timeline, detection, response, root cause |
| Training completion | LMS / HR system | Roster — not engineering's concern |
| Vendor review | Approved vendor list | Spreadsheet + per-vendor review form |

Most SOC 2 evidence is pull-based during fieldwork. Auditors request a sample window (e.g., Q2 2026, Jan-Mar population) and ask for the artifacts for that window. Design evidence collection to produce a consistent, queryable record over time, not a spike of effort when the assessor shows up.

---

## Engineering-owned vs ops-owned at a glance

**Engineering owns outright:** CC6.1, CC6.2, CC6.5, CC6.6, CC6.7, CC6.8, CC7.1, CC7.2, CC7.5, CC8.1, A1.1, A1.3, C1.2, all PI controls.

**Engineering contributes to:** CC3.2, CC3.4, CC4.1, CC5.1, CC5.2, CC6.3, CC7.3, CC7.4, CC9.1, CC9.2, C1.1, P-series.

**Ops owns outright:** CC1 series, CC2.2, CC3.1, CC6.4, CC5.3, A1.2, the bulk of P-series policy-side controls.

The assessor interviews both sides. Engineering's job is to make the technical evidence hand-over frictionless — every in-scope control has a named owner, a stable artifact location, and a last-reviewed date.
