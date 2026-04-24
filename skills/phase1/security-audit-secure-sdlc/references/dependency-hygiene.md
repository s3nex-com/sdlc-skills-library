# Dependency hygiene

## Why dependency hygiene matters

Third-party dependencies are the most common source of unplanned security vulnerabilities in modern software. A single vulnerable transitive dependency — one that your code does not even call directly — can expose your entire system. The XZ Utils backdoor (CVE-2024-3094), Log4Shell (CVE-2021-44228), and event-stream incident are canonical examples of how dependency compromise creates catastrophic impact.

In a cross-company engagement, each company's dependency choices affect the other. A Critical CVE in Company B's delivery must be treated as a Company A risk if Company A's platform depends on the output.

---

## Dependency minimisation policy

Before adding any new dependency, ask:

1. **Is this dependency genuinely necessary?** Can the functionality be implemented in 20 lines without importing a library?
2. **What is the maintenance health?** Check last commit date, open issues count, number of maintainers, and whether the project is actively maintained.
3. **What is the transitive dependency footprint?** Run `npm ls --depth=all` or `pip show --files` to understand what you are pulling in.
4. **What is the security history?** Check the package's CVE history on OSV.dev or Snyk.
5. **What is the license?** Copyleft licenses (GPL, AGPL) can create IP obligations. Permissive (MIT, Apache 2.0, BSD) are generally safe.

### Maintenance health signals (treat as warning if any apply)
- Last commit more than 12 months ago
- No response to open security issues within 30 days
- Single maintainer with no succession plan
- Downloaded millions of times but maintained by one unpaid volunteer (high bus-factor risk)
- Deprecated or superseded by a maintained alternative

---

## Pinning and lock file policy

| Package manager | Lock file | Policy |
|-----------------|-----------|--------|
| npm / yarn | `package-lock.json` / `yarn.lock` | Commit lock file; use `npm ci` (not `npm install`) in CI |
| pip | `requirements.txt` (pinned) + `requirements.in` | Use `pip-compile` to generate pinned requirements; commit both |
| Go | `go.sum` | Always commit `go.sum`; use `go mod verify` in CI |
| Maven | `pom.xml` with explicit versions | No version ranges in `<dependency>` blocks |
| Gradle | `gradle/wrapper/gradle-wrapper.properties` + `build.gradle` | Pin wrapper version; use dependency locking |
| Cargo (Rust) | `Cargo.lock` | Commit lock file for binaries; libraries may omit it |

**Never use floating version ranges in production builds.** `^1.0.0`, `~1.0.0`, `>=1.0.0 <2.0.0` all allow unexpected updates to break reproducibility.

---

## Automated dependency update process

Use Dependabot or Renovate to automate dependency update PRs. Do not merge dependency update PRs blindly.

### Review checklist for dependency update PRs

- [ ] Check the changelog between old and new version. Are there any breaking changes?
- [ ] If the change is a patch (1.0.x → 1.0.y), it is likely a bug fix. Auto-merge if CI passes.
- [ ] If the change is a minor version (1.x.0 → 1.y.0), review the changelog. Merge if CI passes and no breaking changes.
- [ ] If the change is a major version (1.x.x → 2.x.x), review carefully. Test. May require code changes.
- [ ] If the update is security-motivated (Dependabot labels it as a security update), escalate priority to within 5 business days.

### Update priority table

| CVE severity | Action | Timeline |
|--------------|--------|----------|
| Critical | Update immediately; if no fix available, remove or mitigate | Within 24 hours of disclosure |
| High | Update in next sprint | Within 7 days |
| Medium | Scheduled update | Within 30 days |
| Low | Track and batch | Next dependency update sprint |

---

## SCA tooling setup

### Snyk (recommended for SaaS integration)

```yaml
# .github/workflows/security.yml
- name: Run Snyk SCA scan
  uses: snyk/actions/python@master  # or node, golang, etc.
  with:
    args: --severity-threshold=high --fail-on=all
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### OWASP Dependency-Check (self-hosted alternative)

```bash
dependency-check \
  --project "EdgeFlow Ingestion Service" \
  --scan ./src \
  --format JSON \
  --out ./reports \
  --failOnCVSS 9  # Fail build on CVSS >= 9 (Critical)
```

### Container image scanning with Trivy

```yaml
# .github/workflows/container-scan.yml
- name: Scan container image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE_NAME }}:${{ env.IMAGE_TAG }}
    format: sarif
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
    ignore-unfixed: false
```

---

## SBOM (Software Bill of Materials)

Generate an SBOM for every production release. The SBOM is evidence of what is deployed and is required for:
- Rapid CVE impact assessment ("are we affected by CVE-X?")
- Regulatory compliance (EU Cyber Resilience Act, US Executive Order 14028)
- Contractual due diligence between companies

### SBOM generation

```bash
# For container images — generates CycloneDX SBOM
syft IMAGE_NAME:TAG -o cyclonedx-json > sbom.json

# For Python projects
pip-audit --format=cyclonedx-json > sbom.json

# For Go projects
cyclonedx-gomod app -output sbom.json
```

### SBOM storage policy
- Store SBOM alongside the release artefact (not in the container image)
- Version the SBOM with the same tag as the release
- Retain SBOMs for 3 years minimum (audit requirements)
- Make the SBOM available to partner company on request within 5 business days

---

## Incident response for newly disclosed CVEs

When a Critical CVE is disclosed that affects a dependency in production:

### 1. Impact assessment (within 4 hours)
- Identify all services using the affected dependency (query SBOM inventory)
- Determine if the vulnerable code path is reachable from production traffic
- Rate the effective risk: Critical if reachable, High if transitive and unclear, Medium if mitigating controls exist

### 2. Mitigation (within 24 hours for Critical)
- If a patched version is available: create PR, run full test suite, deploy to staging, deploy to production
- If no patched version is available:
  - Can the dependency be removed entirely?
  - Can the vulnerable code path be disabled via configuration?
  - Can a network-level control (WAF rule, rate limit) reduce exploitability?
  - If no mitigation: escalate to both companies' security leads immediately

### 3. Communication
- Notify partner company within 2 hours of confirming impact
- Include: CVE ID, affected service, effective risk rating, mitigation plan and ETA
- Do not wait for a fix to be deployed before notifying — early warning allows partners to apply independent compensating controls

### 4. Post-incident
- Document in the risk register if the mitigation required a code or config change
- Review whether the dependency update policy would have caught this sooner
- Update the SBOM after the fix is deployed

---

## Dependency hygiene audit checklist

Run quarterly or after any significant release:

- [ ] Lock files present and committed for all services
- [ ] No `latest` or floating version ranges in production dependency declarations
- [ ] SCA scan run within the last 30 days; no unresolved Critical or High CVEs
- [ ] Dependabot/Renovate configured and PRs being reviewed (not accumulating)
- [ ] SBOM generated for current production release
- [ ] Dependencies inactive for > 12 months reviewed for replacement
- [ ] No packages with known abandoned status in production
- [ ] License inventory reviewed; no copyleft licenses without legal clearance
