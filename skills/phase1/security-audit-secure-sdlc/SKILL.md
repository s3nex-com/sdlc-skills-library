---
name: security-audit-secure-sdlc
description: >
  Activate when assessing security posture, performing threat modelling, reviewing secure coding
  practices, evaluating dependency hygiene, auditing secrets management, designing security gates
  for CI/CD pipelines, or mapping practices to compliance frameworks (NIST SSDF, OWASP, SOC 2).
  Use for security architecture reviews, STRIDE analysis, SAST/DAST/SCA tool selection, secure
  design principle enforcement, vulnerability triage, penetration test scoping, supply chain
  security, build integrity, and producing security findings reports. Covers both proactive
  design-time security and reactive incident-response readiness.
---

# Security audit and secure SDLC

## Purpose

Embed security into every phase of the engineering lifecycle. Security posture must be explicitly agreed, measurable, and visible. A security finding is a shared problem — the earlier it is caught, the cheaper it is to fix.

---

## When to use

- A new service, API surface, or integration point is being designed — run STRIDE threat modelling before any code is written
- A PR touches authentication, authorisation, secrets handling, input validation, or cryptography — run the code review security gate
- A release is approaching — run the pre-deployment gate (SCA, container scan, DAST, SBOM)
- An existing system needs a security posture assessment
- The team asks "is this secure?", "what are the threats?", or "what security gates do we need in CI?"
- A new AI/LLM feature is being designed — add AI-specific attack surfaces to the threat model
- Compliance mapping is needed (NIST SSDF, OWASP, SOC 2)
- A penetration test scope needs to be defined or reviewed

## When NOT to use

- Ongoing CVE triage, SBOM generation, and dependency EOL tracking → `dependency-health-management`
- Post-incident forensics, root cause, and remediation tracking after a security event → `incident-postmortem`
- Non-security technical, delivery, and external risks → `technical-risk-management`
- Enforcing non-security architectural rules in CI (boundaries, coverage, drift) → `architecture-fitness`
- General API contract review unrelated to authn/authz/abuse → `specification-driven-development`
- Accessibility, privacy UX, or non-security compliance review → `accessibility` / `prd-creator` (non-functional requirements section)

---

## Process

### Threat modelling (Gate 1 — at design time)

1. Define scope: list all services, data stores, external actors, and trust boundaries.
2. Draw the data flow diagram (DFD) showing every flow that crosses a trust boundary.
3. Apply STRIDE per element — for each process, data store, data flow, and external entity, enumerate applicable threats.
4. Rate each threat: Probability (1–5) × Impact (1–5). Record in the threat inventory table.
5. For every threat above score 9: design a mitigation into the architecture. No implementation may begin on a component with an unmitigated threat above score 9.
6. Document residual risks (unmitigated threats) with an explicit acceptance sign-off from the engineering lead.
7. If the feature includes AI/LLM components: add the AI-specific attack surfaces (prompt injection, indirect prompt injection, LLM output execution) to the threat inventory.

### Code review gate (Gate 2 — at PR time)

1. Check for hardcoded secrets — run a secret scanner if not already in CI.
2. Verify input validation is present at every trust boundary entry point.
3. Check SQL/NoSQL queries use parameterised statements or safe ORM methods.
4. Verify error responses do not expose internal stack traces or system paths.
5. Check authentication and authorisation are applied to every new API surface.

### Pre-deployment gate (Gate 3 — before production)

1. Run SCA scan: no Critical CVEs in direct dependencies permitted.
2. Run container image scan: no Critical CVEs; base image is distroless or minimal; no root.
3. Generate SBOM: `syft packages . -o cyclonedx-json > sbom.json`.
4. Scan SBOM: `grype sbom:sbom.json` — block on Critical findings.
5. Sign container image: `cosign sign`; verify signature in deploy step.
6. Check CI/CD workflow files: actions pinned to full commit SHA.
7. Verify secrets management: no secrets in environment variables or image layers.

### Output

8. Produce the security findings report in the output format defined below.
9. Append the execution log entry.

## Core security principles

Apply these to every design and code review:

1. **Defence in depth** — no single control is the last line of defence. Layer authentication, authorisation, encryption, monitoring, and rate limiting.
2. **Least privilege** — every service, process, and user credential receives only the permissions it needs, nothing more.
3. **Fail closed** — when a security control fails or is unavailable, default to denying access, not allowing it.
4. **Validate at trust boundaries** — validate and sanitise ALL input that crosses a trust boundary (network edge, service boundary, database write path).
5. **Secrets are not configuration** — credentials, tokens, private keys, and API keys are never stored in source code, environment variable files checked in, or container images.
6. **Audit everything material** — all authentication events, privilege escalations, data access, and configuration changes must be logged with sufficient context to reconstruct an incident.
7. **Assume breach** — architect assuming the perimeter will be breached. Segment, encrypt in transit and at rest, and limit blast radius.

---

## STRIDE threat modelling

STRIDE is applied at architecture review time, before any code is written. Use it whenever a new service, integration point, data store, or external data flow is designed.

### Threat categories

| Letter | Threat | Mitigations |
|--------|--------|-------------|
| S | Spoofing — attacker pretends to be a legitimate entity | mTLS, signed JWTs, API keys with rotation, PKI |
| T | Tampering — attacker modifies data in transit or at rest | TLS 1.2+, request signing (HMAC), database checksums, audit logs |
| R | Repudiation — actor denies performing an action | Immutable audit logs, log signing, non-repudiation tokens |
| I | Information disclosure — data exposed to unauthorised parties | Encryption at rest and in transit, field-level masking, least-privilege data access |
| D | Denial of service — service rendered unavailable | Rate limiting, circuit breakers, auto-scaling, bulkheads, input size limits |
| E | Elevation of privilege — attacker gains higher privileges | RBAC, mandatory authorisation checks, no default admin credentials |

### Threat modelling process

1. **Define scope**: list all services, data stores, external actors, and trust boundaries in the design.
2. **Draw the data flow diagram (DFD)**: include every data flow that crosses a trust boundary.
3. **Apply STRIDE per element**: for each process, data store, data flow, and external entity, enumerate applicable threats.
4. **Rate each threat**: Probability (1–5) × Impact (1–5) = composite score.
5. **Define mitigations**: for each threat above score 9, a mitigation must be designed into the architecture.
6. **Residual risk sign-off**: any unmitigated threat above score 9 requires documented acceptance by the engineering lead.

See `references/threat-modeling-guide.md` for worked examples and DFD notation.

---

## Security review gates

Embed these gates in the development lifecycle so security findings are caught at the lowest-cost point:

### Gate 1: Design review (before coding)
- Threat model completed for any new service or significant integration change
- Security architecture principles explicitly addressed in the design doc
- Data classification for all fields handled (PII, credentials, sensitive business data)
- Authentication and authorisation model explicitly specified

### Gate 2: Code review (PR merge gate)
- SAST scan passes (no Critical or High findings without documented acceptance)
- No hardcoded secrets (detected by secret scanning tool)
- Input validation present at all trust boundary entry points
- SQL/NoSQL queries use parameterised statements or ORM safe methods
- Error messages do not expose internal stack traces or system paths to callers

### Gate 3: Pre-deployment (CD pipeline gate)
- SCA (software composition analysis) scan: no Critical CVEs in direct dependencies
- Container image scan: no Critical CVEs in base image; base image is distroless or minimal, no root
- DAST scan run against staging environment
- Secrets management verified: no secrets in environment variables or image layers
- Infrastructure-as-code security scan (e.g., Checkov, tfsec): no Critical findings
- SBOM generated and attached to release artefact (`syft packages . -o cyclonedx-json > sbom.json`)
- SBOM scanned for vulnerabilities (`grype sbom:sbom.json`)
- Container image signed (`cosign sign`) and signature verified in deploy step (`cosign verify`)
- CI/CD workflow files reviewed: actions pinned to full commit SHA, GITHUB_TOKEN scoped to minimum

### Gate 4: Production readiness
- Penetration test completed (for new public-facing surfaces or major releases)
- Incident response runbook exists for the new surface
- Alerting configured for authentication failures, anomalous access patterns, rate limit breaches
- Data retention and deletion policies implemented as designed
- Network policies: default deny applied; explicit allow rules documented and reviewed

See `references/security-gates.md` for gate definitions and CI/CD integration examples.

---

## Secure coding standards

Language-specific rules that code under review must comply with. Key areas:

### Input validation
- Validate type, length, format, and range at the service boundary
- Reject invalid input with a 400/422 response — do not attempt to coerce or clean dangerous input
- Use allowlists, not denylists, for permitted values

### Authentication and authorisation
- Never implement custom authentication schemes; use standard libraries and protocols (OAuth 2.0, OIDC, mTLS)
- Authorise every request — authentication confirms identity; authorisation confirms permission
- Check authorisation server-side on every call; never trust client-supplied role or permission claims

### Cryptography
- Use TLS 1.2 minimum (1.3 preferred) for all inter-service communication
- Use AES-256-GCM for symmetric encryption, RSA-2048 or ECDSA P-256 for asymmetric
- Never implement custom cryptographic algorithms
- Key rotation policy: API keys ≤ 90 days, JWT signing keys ≤ 365 days (or after any suspected compromise)
- **Post-quantum readiness:** build a crypto inventory, wrap crypto in an algorithm-agnostic abstraction, plan hybrid (classical + PQC) deployment by 2027, PQC-primary by 2030. See `references/post-quantum-crypto-migration.md` for the roadmap, NIST FIPS 203/204/205 standards, "harvest now, decrypt later" risk assessment, and library support status.

### Error handling
- Log the full error server-side; return a sanitised error response to the caller
- Error responses must not include stack traces, file paths, query strings, or internal service names
- Use a consistent error envelope (see the API contract spec for the ErrorResponse schema)

See `references/secure-coding-standards.md` for full checklists by language.

---

## Dependency hygiene

Minimise surface area; pin to exact versions; monitor continuously. Tooling:

| Tool | Purpose | Integration point |
|------|---------|-------------------|
| Dependabot / Renovate | Automated dependency update PRs | GitHub/GitLab |
| Snyk / OWASP Dependency-Check | SCA: CVE detection in dependencies | CI pipeline Gate 3 |
| Trivy / Grype | Container image vulnerability scanning | CI pipeline Gate 3 |
| syft | SBOM generation | Release pipeline (see Supply chain security) |
| pip-audit / npm audit | Language-native audit | Developer local + CI |

See `references/dependency-hygiene.md` for update policy and triage process.

---

## Supply chain security

Dependencies and build artefacts are attack surfaces. The steps below apply on every release:

### SBOM and vulnerability scanning
- Generate SBOM on every release build: `syft packages . -o cyclonedx-json > sbom.json`
- Scan the SBOM for CVEs: `grype sbom:sbom.json` — block on Critical findings
- Attach the SBOM to the release artefact and store it alongside the binary

### Dependency provenance
- Pin all dependencies to exact versions in lock files (`package-lock.json`, `poetry.lock`, `go.sum`, etc.)
- Commit lock files to version control — never gitignore them
- Before adding a new package, verify the package name against the registry to detect typosquatting (check downloads, publish date, maintainer count)

### Container image signing
- Sign images at build time: `cosign sign <image>:<tag>`
- Verify signature in the deploy step before the image is pulled: `cosign verify <image>:<tag>`
- Require signature verification in admission controllers (Kubernetes: Kyverno or OPA Gatekeeper policy)

See `references/supply-chain-security.md` for full command reference and Sigstore setup.

---

## AI-specific attack surfaces (2026)

If the product includes AI features or agentic components, add these to the threat model:

| Threat | Mitigation |
|--------|-----------|
| Prompt injection — user input hijacks system prompt | Treat user input as untrusted at all boundaries; never interpolate raw user text into system prompt strings |
| Indirect prompt injection — agent reads external content (web pages, files) that contains injected instructions | Mark all externally retrieved content as untrusted; sanitise before passing to next LLM call |
| LLM output used as trusted code or SQL | Never `eval()` or execute LLM output directly; always validate and sanitise against a schema before use |
| Training data poisoning (if fine-tuning) | Validate training data provenance; audit data pipeline for injected examples |

Add each applicable threat as a row in the STRIDE threat inventory with a corresponding mitigation entry.

---

## CI/CD pipeline security

### GitHub Actions hardening
- Use OIDC token exchange for cloud provider access — no long-lived secrets stored as GitHub secrets
- Pin every `uses:` step to a full commit SHA: `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af68` not `@v4`
- Restrict `permissions:` in every workflow file to the minimum required (principle of least privilege)
- Audit `run:` steps that interpolate GitHub context values (`${{ github.event.issue.title }}`, `${{ github.head_ref }}`): these are injection vectors via PR title or branch name

### Secret scanning
- Add `detect-secrets` or `gitleaks` as a pre-commit hook — blocks accidental secret commits locally
- Run secret scanning in CI (GitHub Advanced Security, or `gitleaks detect` as a CI step)
- Rotate any secret that has appeared in a commit, even briefly

---

## Container and infrastructure security

- Use distroless or minimal base images (`gcr.io/distroless/*`, Alpine); no general-purpose OS in production containers
- Containers must not run as root (`USER nonroot` in Dockerfile; `runAsNonRoot: true` in pod spec)
- Network policies: default deny all ingress and egress; explicit allow rules for each required flow
- Apply network policies at both the Kubernetes layer and the cloud VPC/firewall layer
- These controls are verified at Gate 3 (pre-deployment), not just at design time

---

## Secrets management

No secrets in code, configuration files, container images, or environment variable files checked into version control. This is non-negotiable.

### Approved secrets storage
- **Vault (HashiCorp)** or cloud-native equivalents (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
- Application retrieves secrets at runtime via the secrets manager API or agent injection
- Secrets are never written to disk, logs, or passed as command-line arguments

### Secret rotation policy
| Secret type | Max lifetime | Rotation trigger |
|-------------|-------------|-----------------|
| API keys | 90 days | Rotation schedule + any suspected compromise |
| Database credentials | 90 days | Rotation schedule + any personnel change |
| JWT signing keys | 365 days | Rotation schedule + any suspected compromise |
| TLS certificates | Per CA validity / ≤ 1 year | Expiry approach (30 day warning) |
| Service account credentials | 180 days | Rotation schedule + service account changes |

See `references/secrets-management.md` for implementation patterns and rotation runbooks.

---

## NIST SSDF and compliance mapping

Practices map to NIST SSDF SP 800-218 (PO: governance; PS: supply chain/secrets/build; PW: design/code/test; RV: vulnerability response). See `references/nist-ssdf-mapping.md` for the full control mapping.

---

## Security findings report format

Produce a report when completing a security audit. Required fields: scope, review date, reviewer, status (PASS / PASS WITH CONDITIONS / FAIL), finding summary table (Critical/High/Medium/Low counts), Critical and High findings table (ID, severity, location, description, fix, due date), accepted risks table (ID, severity, rationale, accepted by), and resolution requirements (Critical: before deploy; High: ≤ 14 days; Medium: ≤ 30 days or accepted with rationale).

---

## Output format

### Threat model output

```
## Threat model: {System/component name}

**Scope:** {services and data flows included}
**Date:** {date}
**Authors:** {names}

### Data flow diagram
{ASCII or Mermaid DFD with trust boundaries marked}

### Threat inventory
| ID | Element | Threat type (STRIDE) | Description | P | I | Score | Mitigation | Status |
|----|---------|---------------------|-------------|---|---|-------|------------|--------|
| T-001 | API Gateway | S | Attacker sends forged requests... | 3 | 5 | 15 | mTLS between services | Mitigated |

### Residual risks
| Threat ID | Score | Rationale for acceptance | Accepted by |
|-----------|-------|-------------------------|-------------|
```

### Security gate checklist output

```
## Security gate: {Gate name} — {Service/PR/Release name}

**Date:** {date}
**Reviewer:** {name}
**Result:** PASS | FAIL | CONDITIONAL PASS

| Check | Result | Notes |
|-------|--------|-------|
| SAST scan | ✅ PASS | 0 Critical, 2 Medium (accepted, see SEC-012) |
| Secret scanning | ✅ PASS | No secrets detected |
| SCA scan | ❌ FAIL | CVE-2024-XXXXX in lodash 4.17.20 (Critical) |
| ...   | ...    | ...   |

**Blocking issues:** {list or "None"}
**Required actions before proceeding:** {list or "None"}
```

## Skill execution log
When this skill fires, append one line to `docs/skill-log.md`:
[YYYY-MM-DD] security-audit-secure-sdlc — [one-line description, e.g., "STRIDE threat model for device-registry service"]
If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

---

## Reference files

- `references/threat-modeling-guide.md` — STRIDE worked examples, DFD notation, trust boundary examples.
- `references/security-gates.md` — gate definitions and CI/CD integration examples for the four review gates.
- `references/secure-coding-standards.md` — language-specific secure coding checklists.
- `references/dependency-hygiene.md` — SCA tooling, update policy, CVE triage process.
- `references/supply-chain-security.md` — SBOM generation, image signing (cosign), Sigstore setup, full command reference.
- `references/secrets-management.md` — implementation patterns, rotation runbooks, approved secret stores.
- `references/nist-ssdf-mapping.md` — full NIST SSDF SP 800-218 control mapping (PO / PS / PW / RV).
- `references/post-quantum-crypto-migration.md` — PQC migration roadmap: NIST FIPS 203/204/205, crypto inventory process, crypto-agility design patterns, hybrid deployment phasing, library support status (OpenSSL 3.5+, BoringSSL, rustls, Go), NSA CNSA 2.0 deadlines.
