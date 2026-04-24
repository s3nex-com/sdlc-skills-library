---
name: dependency-health-management
description: >
  Activate when auditing the health of third-party dependencies across services, evaluating
  whether a partner company's codebase has unacceptable dependency risks, defining a dependency
  update policy for the engagement, investigating a CVE that affects a delivered system,
  planning a major framework or runtime upgrade, assessing the impact of a dependency reaching
  end-of-life, reviewing an SBOM for a delivered artefact, or establishing the dependency
  governance process that both companies must follow. Use when outdated dependencies are
  creating security, compatibility, or operational risk, or when a framework version is
  approaching end-of-support and an upgrade must be planned.
---

# Dependency health management

## Purpose

Every third-party dependency is a liability as well as an asset. Dependencies become vulnerabilities when they are abandoned, when CVEs are disclosed, or when they fall so far behind the current version that upgrading becomes a major project. In a cross-company engagement, both companies share the risk of each other's dependency choices — a critical CVE in Company B's runtime affects Company A's production platform.

---

## When to use

- The monthly dependency audit is due — run CVE triage, version currency check, and maintenance health check across all services
- A CVE has been disclosed that may affect a delivered system — assess impact and determine remediation timeline
- A framework or runtime is approaching end-of-life — plan the upgrade project with enough lead time
- Taking over a codebase and needing to assess dependency health as part of a brownfield assessment
- A new team member or partner company needs a dependency governance policy to follow
- An SBOM needs to be generated and attached to a release artefact
- A dependency has not been updated in several sprints and its current security and maintenance status needs to be evaluated

## When NOT to use

- **Reviewing a newly introduced dependency at PR time** — use `security-audit-secure-sdlc`. New-dep gating happens at the review gate; this skill handles the installed base over time.
- **Application-level or architectural debt** — use `technical-debt-tracker`. Dep-health is about third-party currency; app debt is first-party.
- **CI/CD integration of scanning tools (SCA, secret scanning wiring)** — use `devops-pipeline-governance`. This skill defines the policy; pipeline governance implements the automation.
- **Incident response to an actively exploited CVE in production** — run `incident-postmortem` after remediation; dependency-health handles proactive audit, not live incident command.
- **Licence compatibility for first-party code or open-sourcing decisions** — requires legal review, not a dep audit.

---

## Process

### Monthly dependency audit

1. Generate the dependency inventory for each service (pip list, npm list, go list, syft for container images).
2. Run a CVE scan against the inventory (pip-audit, npm audit, govulncheck, grype). Collect all findings.
3. Triage each CVE: severity, reachability, and required action timeline. Apply the triage table.
4. Check maintenance health: any direct dependency with no release in the last 12 months — assess whether it is abandoned and needs replacement.
5. Check version currency: any dependency more than 2 major versions behind — estimate migration effort and schedule.
6. Check EOL calendar: any runtime or framework within 12 months of end-of-life — create an upgrade project.
7. Produce the dependency health report in the output format.

### CVE response (immediate)

8. For a Critical CVE with a reachable code path: update within 24 hours. Do not wait for the next sprint.
9. Confirm the fix by re-running the CVE scan after the update.
10. If the update introduces a breaking change: create an ADR for the migration approach.

### SBOM management

11. Generate the SBOM on every release build: `syft IMAGE:TAG -o cyclonedx-json=sbom.json`.
12. Attach the SBOM to the release artefact.
13. For new CVE disclosures: query the SBOM with grype to assess impact before any scanning of live containers.

### All sub-tasks

14. Append the execution log entry.

## Dependency health dimensions

Evaluate every significant dependency across four dimensions:

| Dimension | Healthy | At risk | Critical |
|-----------|---------|---------|---------|
| **Security** | No known CVEs; actively patched | High CVEs with known fix | Critical CVEs unpatched |
| **Maintenance** | Active releases; issues responded to | Slowing releases; maintainer inactive | Abandoned; no security patches |
| **Version currency** | Within 2 major versions of current | 3–4 major versions behind | 5+ versions behind or end-of-life |
| **Licence** | Permissive (MIT, Apache 2.0, BSD) | Weak copyleft (LGPL) | Strong copyleft (GPL, AGPL) without legal clearance |

---

## Dependency audit process

### Step 1: Inventory

Generate the complete dependency list for each service:

```bash
# Python
pip list --format=json > deps.json
pip-audit --format=json > audit.json

# Node.js
npm list --all --json > deps.json
npm audit --json > audit.json

# Go
go list -m all > deps.txt
govulncheck ./... > vulns.txt

# Container image
syft IMAGE:TAG -o json > sbom.json
grype IMAGE:TAG -o json > vulns.json
```

### Step 2: CVE triage

For each CVE found:

| Severity | Reachability | Action | Timeline |
|----------|-------------|--------|----------|
| Critical | Reachable | Update immediately | 24 hours |
| Critical | Not reachable | Update in next sprint; document why not reachable | 7 days |
| High | Reachable | Update in current sprint | 7 days |
| High | Not reachable | Track; update in next dependency sprint | 14 days |
| Medium | Any | Track; batch update | 30 days |
| Low | Any | Track | Next quarterly update |

**Determining reachability:** A CVE is reachable if the vulnerable code path is exercised by your application. Check:
- Does your code import the vulnerable module?
- Does it call the vulnerable function?
- Is the attack vector accessible (network, local, physical)?
- Are there mitigating controls (WAF, input validation, auth) that prevent exploitation?

### Step 3: Maintenance health check

For each direct dependency that has had no release in the last 12 months:

1. Check the GitHub/GitLab issues: are security issues being responded to?
2. Check for forks with active maintenance
3. Check for official successor projects
4. Assess migration cost to an alternative

Unmaintained dependencies with > 3 months of inactivity and known CVEs must be replaced. Do not carry unmaintained dependencies in production systems.

### Step 4: Version currency assessment

```bash
# Python: check what updates are available
pip list --outdated --format=json

# Node.js
npm outdated --json

# Go: check for newer versions
go list -u -m all
```

For each dependency more than 2 major versions behind:
- Review the upgrade path (are there breaking changes? How many?)
- Estimate migration effort
- Schedule the upgrade as a tracked debt item

---

## Framework and runtime end-of-life planning

Framework and runtime end-of-life (EOL) is the most common source of large, expensive dependency upgrades. Plan well in advance.

### EOL planning rule

Start the upgrade project when the current version has **12 months of support remaining**, not when support ends. Waiting until EOL means:
- Rushing a major upgrade under deadline pressure
- Upgrading multiple major versions at once (much harder than incremental upgrades)
- Extended exposure to unpatched security vulnerabilities

### Key EOL dates to track (as of 2024)

| Runtime/Framework | Version | EOL date | Action if in use |
|------------------|---------|---------|-----------------|
| Python | 3.8 | 2024-10-01 | Upgrade to 3.11+ now |
| Python | 3.9 | 2025-10-01 | Plan upgrade to 3.12+ |
| Node.js | 18 LTS | 2025-04-30 | Plan upgrade to Node 20 LTS |
| Node.js | 20 LTS | 2026-04-30 | Current; monitor |
| Go | < 1.21 | Rolling (2 versions) | Always stay on N or N-1 |
| Java | 11 LTS | 2026-09 (Oracle) | Plan upgrade to 21 LTS |
| PostgreSQL | 12 | 2024-11-14 | Upgrade immediately |
| PostgreSQL | 13 | 2025-11-13 | Plan upgrade to 16 |
| Redis | 6.x | 2024-03-31 | Upgrade to 7.x |

### Major version upgrade project template

```markdown
## Upgrade project: {Dependency} {old version} → {new version}

**Owner:** {name}
**Target completion:** {date — must be > 3 months before EOL}
**Estimated effort:** {story points / sprint allocation}

### Breaking changes
{List breaking changes from the migration guide}

### Affected services
{List every service using this dependency}

### Migration plan
Phase 1: Upgrade in service A (lowest risk; fewest usages)
Phase 2: Upgrade in service B, C
Phase 3: Upgrade in service D (highest complexity)
Phase 4: Remove compatibility shims and deprecated API usage

### Test plan
{How will correctness be verified after each phase?}

### Rollback plan
{Can services roll back independently? What are the constraints?}
```

---

## SBOM management

The Software Bill of Materials is the authoritative record of what is in a deployed artefact.

### SBOM generation (per release)

```bash
# Container image SBOM in CycloneDX format
syft IMAGE:TAG -o cyclonedx-json=sbom-v1.2.0.json

# Attach to the release in the registry
oras attach IMAGE:TAG \
  --artifact-type application/vnd.sbom+json \
  sbom-v1.2.0.json:application/vnd.sbom+json
```

### SBOM-driven CVE response

When a new CVE is disclosed:

```bash
# Query the SBOM to find which services are affected
# (using grype with the SBOM as input)
grype sbom:sbom-ingestion-service-v1.2.0.json \
  --output json \
  | jq '.matches[] | select(.vulnerability.severity == "Critical") | {
      package: .artifact.name,
      version: .artifact.version,
      cve: .vulnerability.id,
      fix: .vulnerability.fix.versions[0]
    }'
```

This allows immediate, accurate impact assessment across all services without re-scanning running containers.

---

## Dependency governance policy

### Policy for the cross-company engagement

```markdown
## Dependency governance policy

### New dependency approval
Before adding any new third-party dependency to a service delivered under this engagement:
1. Confirm the dependency is actively maintained (last release < 6 months ago)
2. Run a CVE scan; no Critical or High CVEs allowed at time of introduction
3. Verify the licence is compatible with the engagement IP obligations
4. Declare the dependency in the PR description with rationale

### Update schedule
- Security updates (Critical CVE): within 24 hours of disclosure
- Security updates (High CVE): within 7 days
- All other updates: monthly dependency sprint, first sprint of each month

### Prohibited dependencies
- Any package that is abandoned (last release > 18 months, no maintainer response)
- Any package with an AGPL or GPL licence without written legal clearance from both companies
- Any package with a known Critical CVE that has been unpatched for > 30 days

### Reporting
Both companies provide a monthly dependency health summary to the joint governance meeting.
The summary must include: new CVEs discovered, CVEs resolved, EOL dependencies, and
any new dependencies added.
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] dependency-health-management — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] dependency-health-management — Monthly dependency audit complete; CVE-2025-XXXXX patched
[2026-04-20] dependency-health-management — EOL watch: Python 3.10 EOL in 6 months; upgrade project created
```

---

## Output format

### Dependency health report

```
## Dependency health report: {Service name} v{version}

**Date:** {date}
**Generated from SBOM:** sbom-{version}.json

### Summary
| Dimension | Status | Detail |
|-----------|--------|--------|
| Security | ❌ Action required | 1 Critical CVE, 3 High CVEs |
| Maintenance | ✅ Healthy | All direct dependencies actively maintained |
| Version currency | ⚠️ Monitor | 2 dependencies 2 major versions behind |
| Licence | ✅ Healthy | All permissive licences |

### Critical and High CVEs
| Package | Version | CVE | Severity | Fix version | Reachable? | Action |
|---------|---------|-----|----------|-------------|-----------|--------|
| requests | 2.28.0 | CVE-2023-32681 | High | 2.31.0 | Yes | Update immediately |
| cryptography | 40.0.0 | CVE-2023-49083 | High | 41.0.6 | Yes | Update this sprint |
| setuptools | 65.5.0 | CVE-2022-40897 | High | 65.5.1 | No | Update next sprint |

### End-of-life watch
| Dependency | Current version | EOL date | Months remaining | Action |
|------------|----------------|---------|-----------------|--------|
| Python | 3.9.18 | 2025-10-01 | 10 months | Start upgrade planning |

### Recommended actions
1. [URGENT] Update requests to 2.31.0 — Critical path CVE — Owner: {name}, Due: {date}
2. [HIGH] Update cryptography to 41.0.6 — Owner: {name}, Due: {date}
3. [PLAN] Python 3.9 → 3.12 upgrade — Owner: {name}, Target: Q2 2025
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for SBOM generation guides, CVE triage runbooks, EOL planning templates, and dependency update policy examples as they are developed.
