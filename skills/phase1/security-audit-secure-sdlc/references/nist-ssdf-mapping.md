# NIST SSDF mapping

## Reference

NIST Special Publication 800-218: Secure Software Development Framework (SSDF) Version 1.1.
Available at: https://doi.org/10.6028/NIST.SP.800-218

---

## SSDF practice groups

The SSDF organises practices into four groups:

| Group | Code | Focus |
|-------|------|-------|
| Prepare the Organisation | PO | Policies, roles, tools, processes, training |
| Protect the Software | PS | Protect code, builds, and artefacts from tampering |
| Produce Well-Secured Software | PW | Design, code, review, test |
| Respond to Vulnerabilities | RV | Disclose, respond, fix |

---

## Practice mapping

The table below maps each SSDF practice to the specific controls implemented in this engagement. Evidence columns point to documents and tooling that demonstrate implementation.

### PO — Prepare the Organisation

| Practice ID | Practice name | Implementation | Evidence |
|-------------|---------------|----------------|---------|
| PO.1.1 | Create and maintain a security requirements baseline | Security requirements documented in API contract and architecture review checklist | `specification-driven-development/references/contract-review-checklist.md`; `architecture-review-governance/references/review-checklist.md` |
| PO.1.2 | Identify and document all security requirements that apply to the software | STRIDE threat model identifies threats; security gates define CI/CD controls | `references/threat-modeling-guide.md`; `references/security-gates.md` |
| PO.2.1 | Create policies governing how the organisation manages secure development | Secure coding standards documented and referenced in code review process | `references/secure-coding-standards.md` |
| PO.3.1 | Identify and use security tools to protect software | SAST (Semgrep), DAST (OWASP ZAP), SCA (Snyk), secret scanning (gitleaks), IaC scanning (Checkov) | `references/security-gates.md` |
| PO.3.2 | Maintain and update security tooling | Tool versions pinned in CI configuration; reviewed quarterly | CI pipeline configuration |
| PO.4.1 | Define criteria for making security trade-off decisions | Risk rating matrix and residual risk acceptance process | `technical-risk-management/references/risk-rating-matrix.md`; `references/threat-modeling-guide.md` |
| PO.5.1 | Implement and maintain secure development environments | Developer environments must have pre-commit hooks installed; CI enforces all gates | `references/security-gates.md` (Gate 2); developer onboarding checklist |

### PS — Protect the Software

| Practice ID | Practice name | Implementation | Evidence |
|-------------|---------------|----------------|---------|
| PS.1.1 | Protect all code from unauthorised access and tampering | All code in version-controlled repositories; branch protection enabled; signed commits required on main | Repository configuration; `.github/branch-protection.json` |
| PS.1.2 | Provide a means for verifying the integrity of software releases | Container images signed with cosign; SBOM generated and stored; checksums published | Release pipeline; `sbom.json` per release |
| PS.2.1 | Protect all forms of code from unauthorised access | Least-privilege repository access; dependency supply chain protected via lock files and SCA | Repository access control; `references/dependency-hygiene.md` |
| PS.3.1 | Archive and protect each software release | Container images stored in private registry with immutable tags; releases tagged in git | Container registry; git tag policy |
| PS.3.2 | Collect, safeguard, and maintain provenance data for all components | SBOM per release; dependency provenance via lock files | Release pipeline; SBOM artefacts |

### PW — Produce Well-Secured Software

| Practice ID | Practice name | Implementation | Evidence |
|-------------|---------------|----------------|---------|
| PW.1.1 | Use architecture principles and design patterns for security | Security principles applied at architecture review; threat modelling at design time | `SKILL.md` (core principles); `architecture-review-governance/references/review-checklist.md` |
| PW.1.2 | Consider how well-secured software can reduce attack surface | Least privilege, minimal service permissions, input validation, schema-first API design | `references/secure-coding-standards.md`; `specification-driven-development/` |
| PW.2.1 | Follow coding practices to avoid or minimise vulnerabilities | Language-specific secure coding standards enforced in code review | `references/secure-coding-standards.md` |
| PW.4.1 | Reuse existing well-secured software where practical | Use of standard auth libraries (OAuth, OIDC); standard error envelopes from API contract | `references/secure-coding-standards.md` (authentication section) |
| PW.4.4 | Verify that third-party software follows secure coding practices | SCA scanning; dependency review policy; SBOM for all third-party components | `references/dependency-hygiene.md` |
| PW.5.1 | Test executable code to identify security vulnerabilities | SAST at PR merge; DAST at staging; pentest at production readiness gate | `references/security-gates.md` (Gates 2, 3, 4) |
| PW.6.1 | Conduct code reviews to check for security vulnerabilities | Security checklist mandatory in PR review template | `references/secure-coding-standards.md` (code review section) |
| PW.6.2 | Perform penetration testing for new public-facing surfaces | Required at Gate 4 (production readiness) | `references/security-gates.md` (Gate 4) |
| PW.7.1 | Remediate all security vulnerabilities found during testing | All Critical/High findings must be resolved before deployment; tracking in risk register | `references/security-gates.md`; `technical-risk-management/references/risk-register-template.md` |
| PW.8.2 | Collect, analyse, and share lessons learned from security findings | Post-incident reviews; security findings retrospective in quarterly security review | `incident-postmortem/` skill |

### RV — Respond to Vulnerabilities

| Practice ID | Practice name | Implementation | Evidence |
|-------------|---------------|----------------|---------|
| RV.1.1 | Establish a vulnerability disclosure policy | Security findings reporting process; responsible disclosure between companies | `SKILL.md` (security findings report format) |
| RV.1.2 | Establish a process to receive and respond to vulnerability reports | Security contact in API contract; external escalation process | `stakeholder-sync/` (escalation patterns) |
| RV.2.1 | Investigate all reported vulnerabilities | Finding triage process: severity rating, impact assessment, root cause | `SKILL.md` (STRIDE + findings report) |
| RV.2.2 | Fix all vulnerabilities that are within acceptable timeframes | SLA by severity: Critical 24 hrs, High 7 days, Medium 30 days | `references/security-gates.md` (timeline table) |
| RV.3.1 | Analyse the vulnerability to determine its root cause | Root cause analysis in post-incident review; SSDF gap identified | `incident-postmortem/` skill |
| RV.3.2 | Implement improvements to reduce recurrence | Security gate improvements based on post-incident findings | Gate retrospective process |

---

## OWASP Top 10 coverage

| OWASP Top 10 (2021) | Mitigations implemented |
|---------------------|------------------------|
| A01: Broken Access Control | Authorisation on every endpoint; resource ownership validation; RBAC |
| A02: Cryptographic Failures | TLS 1.2+ enforced; AES-256-GCM for at-rest encryption; key rotation policy |
| A03: Injection | Parameterised queries; input validation at trust boundaries; SAST rules for injection |
| A04: Insecure Design | Threat modelling at design gate; security architecture review checklist |
| A05: Security Misconfiguration | IaC security scanning (Checkov); security baseline for all services; secrets management |
| A06: Vulnerable and Outdated Components | SCA scanning (Snyk/Trivy); SBOM; dependency update policy |
| A07: Identification and Authentication Failures | Standard OAuth/OIDC/mTLS; no custom auth; JWT rotation; no default credentials |
| A08: Software and Data Integrity Failures | Signed container images; lock files; cosign image verification in deployment pipeline |
| A09: Security Logging and Monitoring Failures | Structured logging; audit log for all auth and data access events; alerting on anomalies |
| A10: Server-Side Request Forgery | Allowlist of permitted outbound endpoints; no user-controlled redirect targets |

---

## Compliance gap tracking

Use this format to track gaps against NIST SSDF:

```markdown
## SSDF compliance gap: {Practice ID} — {Practice name}

**Gap description:** {What is missing or only partially implemented}
**Risk:** {What risk this creates}
**Remediation:** {What needs to be done}
**Owner:** {Person responsible}
**Target date:** {Date}
**Status:** Open | In progress | Closed
```

Review open gaps quarterly. Any gap rated High or Critical risk blocks the annual compliance attestation.
