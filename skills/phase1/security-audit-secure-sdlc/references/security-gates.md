# Security gates

## Overview

Security gates are explicit pass/fail checkpoints in the delivery lifecycle. They prevent insecure code from advancing to the next stage. Gates are automated wherever possible; manual review gates have defined reviewers, SLAs, and documented rationale for the outcome.

A gate that is bypassed invalidates the security assurance. Gates may only be bypassed with documented approval from both companies' engineering leads and a time-bounded remediation plan.

---

## Gate 1: Design review gate

**Trigger:** Before coding begins on any new service, significant feature, or cross-company integration point.

**Who reviews:** Senior engineer from each company; security engineer if available.

**Blocking criteria (all must pass to proceed):**

| Check | Blocking? | Notes |
|-------|-----------|-------|
| Threat model completed and reviewed | Yes | Must cover all data flows crossing trust boundaries |
| Data classification documented for all new data fields | Yes | PII, credentials, sensitive business data must be flagged |
| Authentication and authorisation model explicitly designed | Yes | "We'll add auth later" is not acceptable |
| Cross-company data flows have agreed ownership and encryption | Yes | Which company owns the key? What data crosses the boundary? |
| NFRs defined for the security-sensitive operations | No | Latency SLA for auth operations; rate limits designed |
| Threat model residual risks accepted in writing | Yes (if any residual risks exist) | Both companies must acknowledge |

**Output:** Design review sign-off record stored alongside the design document.

---

## Gate 2: Pull request merge gate

**Trigger:** Every PR targeting main/trunk or a release branch.

**Automated checks (CI must pass before merge):**

### Secret scanning
```yaml
# GitHub Actions — gitleaks
- name: Detect secrets
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

**Blocking:** Any detected secret blocks merge immediately. No exceptions without rotation of the exposed secret and documented RCA.

### SAST (static analysis security testing)
```yaml
# GitHub Actions — Semgrep
- name: Run Semgrep SAST
  uses: returntocorp/semgrep-action@v1
  with:
    config: >-
      p/security-audit
      p/owasp-top-ten
      p/python
      p/golang
  env:
    SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
```

**Blocking:** Any Critical or High finding blocks merge. Medium findings generate a comment; they do not block but must be tracked. Findings may be suppressed with an inline comment (`# nosemgrep`) only if reviewed and accepted by a senior engineer within the PR.

### Code review checklist (manual)

Reviewers must confirm:
- [ ] Input validation present at all new trust boundary entry points
- [ ] No new SQL/NoSQL query string concatenation
- [ ] No new secrets committed (SAST catches most; human review catches context-specific issues)
- [ ] Error responses do not expose internal details
- [ ] New authentication/authorisation code follows established patterns
- [ ] New dependencies reviewed (see dependency-hygiene.md)

---

## Gate 3: Pre-deployment gate (CD pipeline)

**Trigger:** Before deployment to any environment accessed by real users (staging, pre-production, production).

**Automated checks:**

### SCA (software composition analysis)
```yaml
# Snyk SCA scan
- name: Snyk SCA scan
  run: snyk test --severity-threshold=critical --fail-on=all
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

**Blocking:** Any Critical CVE in direct dependencies blocks deployment. High CVEs in direct dependencies block deployment unless accepted with documented rationale. Transitive dependency Critical CVEs trigger a 24-hour remediation window before blocking.

### Container image scan
```yaml
- name: Trivy image scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE_REF }}
    format: table
    exit-code: '1'
    severity: 'CRITICAL'
    ignore-unfixed: false
```

**Blocking:** Any Critical CVE in the base image or installed packages blocks deployment.

### IaC security scan
```bash
# Checkov for Terraform / Kubernetes manifests
checkov -d ./infrastructure \
  --framework terraform,kubernetes \
  --check HIGH,CRITICAL \
  --compact \
  --output json
```

**Blocking:** Critical IaC misconfigurations (e.g., publicly accessible S3 bucket, no encryption at rest, permissive security group allowing 0.0.0.0/0 to internal ports) block deployment.

### DAST (dynamic application security testing) — staging only

Run against the staging environment on every deployment to staging:

```bash
# OWASP ZAP baseline scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.api.edgeflow.example.com \
  -r zap-report.html \
  -x zap-report.xml \
  -l WARN
```

**Blocking:** Critical and High DAST findings block promotion from staging to production. DAST does not block staging deployment itself (it IS the staging test).

### Secrets in environment configuration
```bash
# Verify no secrets in Helm values or Kubernetes manifests committed to the repo
git diff origin/main...HEAD -- "*.yaml" "*.yml" | grep -iE "(password|secret|token|key|credential)" | grep -v "secretRef\|secretName\|valueFrom"
# If output is non-empty, review and block if secrets are hardcoded
```

**Output:** Deployment gate report generated and stored as a CI artefact for audit purposes.

---

## Gate 4: Production readiness gate

**Trigger:** Before first deployment to production for a new service or major release.

**Manual review required by both companies' engineering leads:**

| Requirement | Blocking? | Evidence |
|-------------|-----------|---------|
| Penetration test completed (for new public-facing surface) | Yes | Pentest report; all Critical/High findings resolved or accepted |
| Incident response runbook exists | Yes | Link to runbook in PR description |
| Alerting configured for security events | Yes | Alert rules in PR; staged alert fire test passed |
| Data retention and deletion policies implemented | Yes | Code + IaC in PR |
| Backup and recovery tested for new data stores | Yes | Recovery test results |
| Threat model current (not from design review) | Yes | Threat model reflects actual implementation |
| Security gate results from prior gates attached | Yes | Links to CI reports |

**Output:** Production readiness sign-off record. Both engineering leads must sign off. Stored in the governance repository.

---

## Gate bypass procedure

Bypassing a gate must never happen silently. If a business emergency requires bypassing a gate:

1. Engineering lead from the requesting company documents: what gate, what check, what is being bypassed, why, what is the risk.
2. Engineering lead from the partner company must co-approve the bypass.
3. A time-bounded remediation plan is created (maximum 5 business days for Critical issues, 14 days for High).
4. The bypass is tracked in the risk register.
5. The bypassed check is run retroactively and any findings addressed within the agreed window.

**Bypasses involving secrets exposure require immediate rotation of the exposed secret regardless of other approvals.**

---

## Gate dashboard / reporting

Track gate outcomes per sprint and release. Key metrics:

| Metric | Target | Alert threshold |
|--------|--------|----------------|
| Gate 2 block rate (SAST) | < 5% of PRs blocked | > 15% signals systemic secure coding issues |
| Gate 3 Critical CVE rate | 0 per release | Any single occurrence |
| Mean time to resolve Critical security finding | < 24 hours | > 48 hours |
| Gate bypasses per quarter | 0 | Any bypass triggers review |
| DAST Critical findings per release | 0 | Any single occurrence |

Review gate metrics in the monthly security review meeting.
