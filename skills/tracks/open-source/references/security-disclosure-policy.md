# Security disclosure policy

Vulnerability reports from strangers will arrive once the project has any adoption. Without a documented channel, they land in public issues, email replies, or Twitter — all of which accelerate exploitation. This reference provides the policy, the `SECURITY.md` template, and the workflow from report to advisory publication.

---

## Core principles

1. **One documented channel** (`security@` or GitHub Security Advisory form). Multiple channels create race conditions.
2. **Safe harbor.** Researchers who follow the policy must not fear legal retaliation. Without it, reports go to Twitter.
3. **Coordinated disclosure.** Default 90 days private report → public advisory. Extend if fix is genuinely hard; shorten if exploitation observed.
4. **Reproducible triage.** Every report acknowledged, scored, tracked, closed with a documented outcome.

---

## `SECURITY.md` template — copy and adapt

Place the file at the repo root. GitHub surfaces it on the Security tab automatically.

```markdown
# Security policy

## Supported versions

The following versions receive security updates:

| Version | Supported |
|---------|-----------|
| 3.x     | Yes       |
| 2.x     | Until 2026-06-30 |
| < 2.0   | No        |

Users on unsupported versions should upgrade to receive security fixes.

## Reporting a vulnerability

**Please do not open public GitHub issues for security reports.** Public issues
accelerate exploitation before a fix is available.

Report privately via either:

1. **GitHub Security Advisories** — preferred. Visit
   https://github.com/ORG/REPO/security/advisories/new and submit a draft
   advisory. This gives us a private channel to collaborate on the fix.
2. **Email** — security@example.com. Include a description of the issue,
   steps to reproduce, and your disclosure timeline expectations. PGP key
   available at https://example.com/security-pgp.asc (fingerprint:
   `ABCD 1234 EFGH 5678 IJKL 9012 MNOP 3456 QRST 7890`).

What to include in the report:

- Affected version(s)
- A minimal reproduction (code, config, steps)
- Impact — what an attacker can do
- Suggested severity (CVSS if you can; low / medium / high / critical otherwise)
- Whether the issue is being actively exploited (if known)

## What you can expect from us

- **Acknowledgement** within 3 business days.
- **Initial triage and severity assessment** within 10 business days.
- **A fix or mitigation plan** shared with you within 30 days for high or
  critical issues; 60 days for medium or low.
- **Coordinated disclosure.** Default disclosure window is 90 days from
  the date of the initial acknowledgement. We will extend the window if the
  fix is genuinely hard and we are making steady progress; we will shorten
  it if we observe active exploitation in the wild.
- **Credit** for the reporter in the published advisory unless you prefer
  to remain anonymous.

## Safe harbor

We will not pursue legal action against researchers who:

- Make a good-faith effort to comply with this policy.
- Avoid privacy violations, destruction of data, and service disruption.
- Do not exploit the issue beyond what is necessary to demonstrate it.
- Give us a reasonable window to fix the issue before public disclosure.

Activity consistent with this policy is authorized and we consider it
legitimate security research. If legal action is initiated by a third party
against a researcher who complied with this policy, we will make it known
that their actions were authorized.

## Scope

In scope:
- The source code in this repository.
- Published artifacts under the package name `example-lib` on npm / PyPI / Crates.io.
- The project documentation site at https://example.com.

Out of scope:
- Third-party services that integrate with the library (report to them directly).
- Social engineering of maintainers.
- DoS through resource exhaustion without a software defect.

## Public advisory process

Once a fix is ready:

1. A patched version is released on the registry.
2. A GitHub Security Advisory is published at
   https://github.com/ORG/REPO/security/advisories listing affected versions,
   CVE identifier (if assigned), CVSS score, and upgrade instructions.
3. A CHANGELOG entry under `### Security` references the advisory.
4. If the issue is severe and affects a widely-used version, we notify
   known downstream maintainers ahead of public disclosure where feasible.
```

---

## Workflow — report to advisory

### 1. Receipt

Every report gets an acknowledgement within 3 business days. The ack is brief:

> Thanks for the report. We've received it and will triage this week.
> Tracking internally as SEC-2026-04-001. We'll follow up with an initial
> severity assessment by <date>.

If the reporter emailed and PGP is available, verify their PGP signature before treating any attached details as authenticated.

### 2. Triage

Within 10 business days:

- Reproduce the issue on a supported version.
- Score severity with CVSS 3.1 using https://www.first.org/cvss/calculator/3.1.
- Classify: vulnerability (requires fix) / defense-in-depth issue (improvement) / out-of-scope (declined).
- If declined, explain why to the reporter and close the thread.
- If accepted, create a private GitHub Security Advisory draft and invite the reporter as a collaborator.

### 3. CVE request

For any accepted vulnerability with CVSS >= 4.0, request a CVE ID. GitHub is a CNA for advisories published through GitHub Security Advisories — click "Request CVE" on the advisory draft (under 24 hours). Otherwise submit at https://cveform.mitre.org/ (days to weeks). Some language-specific CNAs (e.g. PSF for CPython) may claim jurisdiction. CVE IDs are public on assignment; details stay embargoed until publication.

### 4. Fix development

Develop in a private fork or the Security Advisory's private temporary fork. Do not push to a public branch — commit messages and diffs are searchable the moment they hit the public repo. Include the reporter in review if they opted in.

### 5. Release and advisory

1. Publish the patched version to the registry, backported to every supported minor line.
2. Publish the GitHub Security Advisory — it populates the Security tab and notifies Dependabot consumers.
3. Add a `### Security` CHANGELOG entry linking the advisory.
4. For critical issues with plausible exploitation, publish a short post explaining the issue and upgrade path; link from the advisory.

### 6. Post-disclosure

Credit the reporter unless they declined. Log the incident internally with a root-cause note. Add a regression test for the class of issue if one is new. Revisit severity if real-world impact differs from the estimate.

---

## Advisory publication format

The published advisory contains:

- **Title** — succinct, non-sensational. "Prototype pollution in mergeDeep() when called with user-controlled keys."
- **Affected versions** — specific ranges, not "all". Example: `>=2.0.0, <2.3.1` and `>=1.5.0, <1.8.7`.
- **Patched versions** — where the fix lands. `2.3.1, 1.8.7`.
- **Impact** — what an attacker can do. Clear, factual.
- **Workarounds** — if a configuration change mitigates without upgrade, list it. Users on pinned versions may not be able to upgrade immediately.
- **CVSS vector and score** — full vector, not just the number.
- **CVE ID** — if assigned.
- **Credits** — reporter name (or anonymous).
- **References** — commit SHA of the fix, related CWE, any public write-up if the reporter published one.

---

## PGP option

A PGP key is optional but cheap. Publish at a stable URL; include the fingerprint in `SECURITY.md`. Generate:

```bash
gpg --batch --full-generate-key <<EOF
%no-protection
Key-Type: EDDSA
Key-Curve: ed25519
Name-Real: Example Project Security
Name-Email: security@example.com
Expire-Date: 2y
EOF
gpg --armor --export security@example.com > security-pgp.asc
```

Rotate before expiry. Publish the new fingerprint in `SECURITY.md` and keep the old key available for decrypting historical reports through the overlap period.
