# FedRAMP evidence checklist

FedRAMP authorizations are built on NIST SP 800-53 control baselines. Low baseline = 125 controls. Moderate baseline = 325 controls. Most engineering work ships evidence for the same 40–60 controls across the seven families listed below. This checklist maps those engineer-owned controls to the artifact they produce and where that artifact lives.

Evidence location convention: `docs/evidence/<control-id>/<YYYY-MM-DD>/`. One folder per control per collection event. Never overwrite prior evidence; the audit trail is the sequence.

---

## The 14 control families at summary level

| Family | Name | Engineer-owned? |
|--------|------|-----------------|
| AC | Access Control | Yes — implemented in code and IAM config |
| AT | Awareness and Training | No — HR/security team |
| AU | Audit and Accountability | Yes — logging, retention, log integrity |
| CA | Assessment, Authorization, Monitoring | Mixed — CM output feeds CA |
| CM | Configuration Management | Yes — IaC, change control, baselines |
| CP | Contingency Planning | Yes — DR, backups, failover testing |
| IA | Identification and Authentication | Yes — MFA, auth flows, credential management |
| IR | Incident Response | Mixed — runbooks and detection are engineering |
| MA | Maintenance | No — facilities / ops |
| MP | Media Protection | No — facilities / procurement |
| PE | Physical and Environmental | No — cloud provider inheritance |
| PL | Planning | Mixed — SSP authoring |
| PS | Personnel Security | No — HR |
| RA | Risk Assessment | Mixed — technical risk feeds RA |
| SA | System and Services Acquisition | Mixed — supply chain controls |
| SC | System and Communications Protection | Yes — TLS, network segmentation, crypto |
| SI | System and Information Integrity | Yes — patching, malware, input validation |

For Low and Moderate baselines, the engineer-owned families AC, AU, CM, CP, IA, SC, and SI produce the majority of the evidence volume. The remainder is inherited from the cloud provider's FedRAMP package (AWS GovCloud, Azure Government, GCP Assured Workloads) or owned by non-engineering functions.

---

## AC — Access Control

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| AC-2 | Account management | IAM config export, user lifecycle runbook, JIT access logs |
| AC-3 | Access enforcement | Authz code (RBAC/ABAC policy files), integration test output |
| AC-4 | Information flow | Network policy YAML, security group config, VPC flow logs |
| AC-5 | Separation of duties | CODEOWNERS file, branch protection rules export, deploy approval log |
| AC-6 | Least privilege | IAM policy diff report, role scope review log |
| AC-7 | Unsuccessful logon | Auth service lockout config, test evidence of threshold trip |
| AC-11 | Session lock | Frontend session-timeout config, integration test |
| AC-12 | Session termination | Auth service session-max config, token expiry policy |
| AC-17 | Remote access | VPN config, bastion access log, MFA requirement screenshot |

Typical collection path: export IAM state via Terraform plan or cloud CLI, commit to `docs/evidence/AC-<N>/<date>/`. Supplement with a 1-line README naming the engineer who collected it.

---

## AU — Audit and Accountability

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| AU-2 | Auditable events | Logging config (what gets logged), sample log entries |
| AU-3 | Content of audit records | Log schema doc, sample entry showing required fields (who/what/when/where/outcome) |
| AU-4 | Log storage capacity | Log storage config, retention policy, alerting on storage threshold |
| AU-6 | Review and reporting | SIEM dashboard screenshot, weekly review log |
| AU-8 | Time stamps | NTP config, timestamp format evidence |
| AU-9 | Protection of audit info | Log bucket IAM policy (write-only for apps, read-only for reviewers), immutability config |
| AU-11 | Audit record retention | Retention policy in storage config (90d hot, 1y cold, or per framework) |
| AU-12 | Audit generation | Per-service logging verification, coverage report |

The audit trail itself is audit evidence. Logs must be tamper-evident — ideally an append-only store with write-once policy. Evidence shows both the policy and a sample of production-captured entries.

---

## CM — Configuration Management

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| CM-2 | Baseline configuration | Git tag or commit hash representing the current baseline; IaC state |
| CM-3 | Configuration change control | Change approval log (see `change-management-approvals.md`), PR history |
| CM-4 | Security impact analysis | Per-PR security review checklist output |
| CM-5 | Access restrictions for change | Branch protection export, deployer role IAM policy |
| CM-6 | Configuration settings | Hardening baseline doc, drift detection report |
| CM-7 | Least functionality | Service allowlist, disabled-feature inventory |
| CM-8 | Information system component inventory | Asset inventory export (ideally from IaC state) |
| CM-10 | Software usage restrictions | License inventory, approved software list |
| CM-11 | User-installed software | Endpoint policy, for dev workstations if in scope |

CM is where IaC pays off: if the infrastructure is fully described in Terraform/Pulumi/CloudFormation, the repo IS the CM-2 baseline and PRs ARE the CM-3 change control. Print the Terraform plan into the evidence folder for the release.

---

## CP — Contingency Planning

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| CP-2 | Contingency plan | DR runbook, RTO/RPO targets |
| CP-4 | Contingency plan testing | DR test report, last-run date, outcome |
| CP-6 | Alternate storage site | Backup config showing cross-region replication |
| CP-7 | Alternate processing site | Multi-region failover config, last failover drill log |
| CP-9 | Information system backup | Backup schedule, retention, last successful-restore test |
| CP-10 | Information system recovery | Runbook for restore-from-backup, last execution log |

Engineering feeds CP-2 and CP-9/10 directly. The `disaster-recovery` skill produces most of this evidence; in this track, the skill's output gets copied into `docs/evidence/CP-<N>/<date>/` with a pointer to the runbook in the main docs tree.

---

## IA — Identification and Authentication

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| IA-2 | Identification and authentication (users) | Auth service config, MFA enforcement screenshot, SAML/OIDC IdP config |
| IA-2(1) | MFA for privileged accounts | IAM policy requiring MFA for admin roles, enforcement test |
| IA-2(2) | MFA for non-privileged accounts | User MFA enrollment rate report |
| IA-4 | Identifier management | User provisioning flow, orphan-account scan output |
| IA-5 | Authenticator management | Password policy, key rotation log, secret expiry report |
| IA-5(1) | Password-based authentication | Password hashing config (argon2/bcrypt cost), complexity rules |
| IA-8 | Identification and authentication (non-org users) | Partner/customer auth config, external-user inventory |

MFA evidence is one of the most requested items in an assessment. Be prepared to show both the configuration (policy/enforcement setting) AND a sample showing a user actually going through MFA — often a redacted screenshot or an audit log entry.

---

## SC — System and Communications Protection

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| SC-4 | Information in shared resources | Tenant isolation design doc, per-tenant crypto key config |
| SC-5 | Denial of service protection | WAF rules, rate limit config, DDoS protection enabled evidence |
| SC-7 | Boundary protection | VPC/subnet diagram, security group export, WAF config |
| SC-8 | Transmission confidentiality and integrity | TLS version enforcement (min 1.2, prefer 1.3), cert inventory |
| SC-8(1) | Cryptographic protection | Cipher suite allowlist, HSTS config |
| SC-12 | Cryptographic key establishment | KMS config, key rotation policy, envelope encryption design |
| SC-13 | Cryptographic protection | FIPS 140-2 validated modules in use (relevant for FedRAMP Moderate+) |
| SC-23 | Session authenticity | Session token config, CSRF token config |
| SC-28 | Protection of information at rest | Storage encryption config (per-bucket, per-volume, per-db) |

For FedRAMP, FIPS 140-2 validation of cryptographic modules matters. Default cloud services are usually fine — document the service's FedRAMP inheritance status.

---

## SI — System and Information Integrity

| Control | What it means | Evidence source |
|---------|---------------|-----------------|
| SI-2 | Flaw remediation | Patch schedule, dependency update log, time-to-patch metrics |
| SI-3 | Malicious code protection | Endpoint protection config, container image scan results |
| SI-4 | Information system monitoring | IDS/IPS config, CloudTrail/audit event forwarding, alerting rules |
| SI-5 | Security alerts and advisories | CVE feed subscription, advisory response log |
| SI-7 | Software, firmware, and information integrity | SBOM, image signing config (cosign/notary), integrity check output |
| SI-10 | Information input validation | Input validation test suite, schema validation library in use |
| SI-11 | Error handling | Error handler config showing no stack traces in prod responses |
| SI-12 | Information handling and retention | Data retention policy, deletion job runbook |

SI-2 and SI-3 are continuous — the `dependency-health-management` skill produces monthly evidence, as do container image scans in CI. Archive the scan output on a monthly cadence even if nothing changed.

---

## Evidence location table

| Artifact type | Location |
|---------------|----------|
| Code (implementing a control) | The repo. Tag lines with the control ID in a comment: `// [AC-6] least privilege: deny-by-default` |
| CI log excerpts | `docs/evidence/<control-id>/<date>/ci-<run-id>.log` |
| IaC plan output | `docs/evidence/CM-2/<date>/terraform-plan.txt` |
| Architecture / design docs | `docs/evidence/<control-id>/<date>/design.md` with an anchor link to the main design doc |
| Runbooks | `docs/evidence/<control-id>/<date>/runbook.md` — full copy of the runbook at that point in time |
| Screenshots | `docs/evidence/<control-id>/<date>/screenshot-<topic>.png` |
| Scan results (vuln, image, SAST) | `docs/evidence/SI-2/<date>/<scanner>-<target>.json` |
| Access review | `docs/evidence/AC-2/<YYYY-QN>/access-review.md` (quarterly) |
| Penetration test report | `docs/evidence/CA-8/<date>/pentest-report.pdf` |

Rule: put it where an assessor can find it in one hop from the control ID. Never hide evidence in skill-specific folders.

---

## Collection cadence

| Cadence | What to collect |
|---------|-----------------|
| Per release | CM-2 (baseline), CM-3 (change log), CM-4 (security review), SI-2 (dep scan) |
| Monthly | SI-2 (vuln scan), SI-4 (monitoring health check), AU-6 (log review) |
| Quarterly | AC-2 (access review), IA-5 (credential rotation check) |
| Annually | CP-4 (DR test), CA-8 (pen test if Moderate+), RA-3 (risk assessment refresh), all controls re-test |

A missed cadence is a finding. Automate the reminder (calendar, scheduled job) so the cadence itself is not what fails.
