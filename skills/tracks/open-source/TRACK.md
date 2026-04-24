---
name: open-source
description: >
  Activates when the user mentions open source, open-sourcing, publishing a library,
  publishing to npm / PyPI / Crates.io / Maven Central / RubyGems / pkg.go.dev,
  GitHub public repo, semver, semantic versioning, breaking change policy,
  deprecation, sunset, migration guide, CONTRIBUTING.md, contributor guide,
  CLA, DCO, security advisory, CVE disclosure, security@, responsible disclosure,
  coordinated disclosure, SECURITY.md, license compliance, SPDX, OSI-approved,
  dual licensing, or SBOM for a public artifact. Also triggers on explicit
  declaration: "Open source track" or "OSS track".
---

# Open source track

## Purpose

This track covers libraries, frameworks, CLIs, and SDKs published publicly and consumed by external developers who are not on the team. Open source has a distinct shape the base library does not encode: the public API surface is a contract you cannot quietly change, the contributor pipeline is a real user-facing system that needs its own SLAs, security reports arrive in your inbox from strangers and must follow a coordinated disclosure process, and every dependency you pull in propagates its license to whoever uses your library. Running an OSS project in the default library leaves these concerns implicit. The track makes them explicit and blocks the pipeline if they are missed.

The track is designed for small teams (3–5 maintainers) publishing libraries consumed by hundreds or thousands of downstream users. It is not a foundation-scale governance framework; it is the minimum discipline required so that a small team can ship a library publicly without accumulating a support backlog, a license-contamination time bomb, or an exploit vector.

---

## When to activate

Activate this track when the user mentions or the PRD contains:

- "open source", "open-source this", "OSS", "publish publicly"
- "publish to npm", "publish to PyPI", "publish to Crates.io", "Maven Central", "pkg.go.dev", "RubyGems"
- "GitHub public", "make the repo public", "unfork into its own repo"
- "semver", "semantic versioning", "major / minor / patch bump"
- "breaking change policy", "API stability", "stable vs experimental"
- "deprecation", "deprecate this", "sunset this feature", "migration guide", "codemod"
- "CONTRIBUTING.md", "contributor guide", "first-time contributor", "good first issue"
- "CLA", "DCO", "sign-off", "contributor license agreement"
- "CVE", "security advisory", "security@", "responsible disclosure", "coordinated disclosure"
- "SECURITY.md", "vulnerability reporting", "safe harbor"
- "license", "MIT", "Apache 2.0", "GPL", "AGPL", "LGPL", "MPL", "SPDX", "OSI-approved"
- "SBOM for the release", "signed release", "Sigstore", "cosign"

Or when the system under discussion has these properties:

- A public API surface that external developers import, call, or extend
- A public issue tracker and pull request inbox open to the world
- A release cadence that produces versioned artifacts on a public registry
- Dependents the team does not control and cannot contact directly

---

## When NOT to activate

Do NOT activate this track when:

- The library is internal-only and will never be published outside the organisation — no track needed
- The project is a proprietary closed-source product that happens to live in GitHub — no track needed; this track is about public contracts, not source visibility
- You are forking an external project for internal patches where upstream carries the release obligations — contribute upstream or fork privately; no track needed
- The artifact is a private-registry package used only by sibling teams — treat it as an internal library with strong versioning discipline, not as OSS
- You are writing sample code, starter templates, or example snippets with no semver commitment — no track needed; document them as examples and move on

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| specification-driven-development | Mandatory | Mandatory + semver | Mandatory + semver + deprecation plan | Mandatory + semver + 12-month deprecation window |
| api-contract-enforcer | Standard | Mandatory | Mandatory + public contract tests | Mandatory + cross-version compatibility tests |
| documentation-system-design | Mandatory (README + CONTRIBUTING) | Mandatory | Mandatory + API docs generated | Mandatory + versioned docs site |
| dependency-health-management | Mandatory | Mandatory | Mandatory + license hygiene | Mandatory + license + SBOM published |
| security-audit-secure-sdlc | Standard | Mandatory + security policy | Mandatory + CVE disclosure process | Mandatory + SAST in public CI + Sigstore signing |
| developer-onboarding | N/A | N/A | Mandatory (CONTRIBUTING.md + contributor onboarding flow and issue triage SLA required) | Mandatory |

Skills not listed keep their default mode behaviour. A cell reading "Mandatory + X" means the skill fires AND X is required for the stage gate to pass.

Notes on the additional elevation:

- `developer-onboarding` at Standard+ reflects that the contributor pipeline is a user-facing system for an open-source project. Contributor friction — an absent CONTRIBUTING.md, no good-first-issue labelling, no stated review SLA — is the primary reason external contributors stop contributing. The `developer-onboarding` skill structures the first-time contributor flow, response cadences, and maintainer workload distribution. At Standard, the output is a CONTRIBUTING.md that functions as contributor onboarding documentation, not just a governance document.

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan)     | No modification. |
| Stage 2 (Design)   | Public API surface is explicit in the design doc. Every exported symbol is classified stable / experimental / internal. Experimental APIs carry an `@experimental` marker and a stated review-by date. Internal APIs are marked and documented as out of the semver contract. |
| Stage 3 (Build)    | No modification. |
| Stage 4 (Verify)   | `diff_contracts.py` runs against the last released tag; any breaking-change diff fails the gate unless a major bump is already planned in the release PR. Public contract tests pass on at least one real downstream consumer pinned to the previous minor. |
| Stage 5 (Ship)     | `CHANGELOG.md` updated for this release with Added / Changed / Deprecated / Removed / Fixed / Security sections. Semver bump is justified in the release PR description. Release notes published to GitHub Releases and the registry. In Rigorous mode, artifacts are signed (Sigstore or equivalent) and an SBOM is published alongside the release. |
| Phase 3 (Ongoing)  | Published issue-triage SLA (default: first response within 5 business days). Published PR review SLA (default: first review within 10 business days, stale PRs triaged monthly). Release cadence published (e.g. "patch as needed, minor monthly, major at most annually"). Security advisory backlog reviewed weekly. |

Strictest-wins applies if another active track modifies the same gate.

---

## Reference injection map

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| specification-driven-development | `references/semver-discipline.md`, `references/deprecation-policy.md` |
| api-contract-enforcer | `references/semver-discipline.md`, `references/deprecation-policy.md` |
| documentation-system-design | `references/contributor-experience.md`, `references/deprecation-policy.md` |
| dependency-health-management | `references/license-compliance.md` |
| security-audit-secure-sdlc | `references/security-disclosure-policy.md` |
| pr-merge-orchestrator | `references/contributor-experience.md`, `references/license-compliance.md` |
| release-readiness | `references/semver-discipline.md`, `references/deprecation-policy.md` |
| code-review-quality-gates | `references/contributor-experience.md` |
| design-doc-generator | `references/semver-discipline.md` |

Specific guidance the injection encodes:

- When `specification-driven-development` fires, semver rules apply to every public interface. `diff_contracts.py` must run before every release and its output attached to the release PR. A deprecation plan for any removed symbol is linked in the release notes.
- When `api-contract-enforcer` fires, the public contract is exported to a checked-in snapshot (`api.snapshot.json` or equivalent). Changes to the snapshot require a release-PR label matching the intended semver bump.
- When `documentation-system-design` fires, the project has a `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, and (for Standard / Rigorous) a versioned docs site. Missing any of these fails the gate.
- When `dependency-health-management` fires, license compatibility is a hard gate, not advisory. A copyleft dependency creeping into a permissively-licensed project fails the gate until resolved. The license scanner allow-list is committed to the repo.
- When `pr-merge-orchestrator` fires for an external contributor (author is not a maintainer), DCO sign-off or CLA acceptance is checked before merge. Missing sign-off blocks the merge.
- When `security-audit-secure-sdlc` fires, a `SECURITY.md` matching the template in `references/security-disclosure-policy.md` must exist at the repo root. Vulnerability reports received outside the documented channel are redirected to it before triage begins.
- When `release-readiness` fires, the CHANGELOG is up to date, the semver bump is justified in the PR description, and the release notes draft is linked. In Rigorous mode, the release artifact is signed (Sigstore / cosign) and an SBOM (`sbom.cdx.json`) is attached.

---

## Reference files

- `references/semver-discipline.md` — semver rules with worked examples, non-obvious breaking changes, `0.x` vs `1.x+` behaviour, pre-release channels, detecting breakage in CI.
- `references/deprecation-policy.md` — the full deprecation lifecycle from mark to remove, migration-guide requirements, codemod expectations, handling transitive breaking changes.
- `references/security-disclosure-policy.md` — ready-to-use `SECURITY.md` template, safe harbor language, disclosure windows, CVE / GHSA workflow, PGP reporting option.
- `references/contributor-experience.md` — `CONTRIBUTING.md` structure, CLA vs DCO decision, first-time contributor support, PR template, issue labels, triage and review SLAs, maintainer burnout prevention.
- `references/license-compliance.md` — license selection trade-off table, dual licensing, mixed-license contributions, attribution requirements, SPDX identifiers, copyleft dependency exposure.

---

## Operating notes

**Mode choice.** This track is typically run in Standard mode. Lean mode works for pre-1.0 experimental libraries. Rigorous mode is reserved for libraries with contractual obligations (paid OSS support, foundation stewardship, or critical supply-chain exposure).

**Repo hygiene at minimum.** Every OSS repo in this track has: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, a PR template, at least one issue template, and a CI pipeline that runs tests, license scan, and `diff_contracts.py` on every PR. Missing any of these blocks the first public release.

**Release-PR conventions.** The release PR title contains the target version. The description contains: the semver bump justification, a summary of user-facing changes, a link to the migration guide for any breaking change, and the output of `diff_contracts.py`. The release PR is merged only after a maintainer other than the author approves it.

**Triage discipline.** Issue triage and PR review SLAs are published in `CONTRIBUTING.md` and tracked in the on-call rotation. Missing an SLA is not a catastrophe, but silence is. When backlog grows, post an acknowledgement banner in the repo README and keep moving — silence trains the community to stop reporting, and a project without reports is a dead project.

**First-release checklist.** Before the `0.1.0` or `1.0.0` tag that makes the project public:

1. `LICENSE` file matches the declared SPDX identifier in package metadata.
2. `README.md` names the project, its purpose in one paragraph, an install command, and a minimal code example that actually works on a clean machine.
3. `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` are present and pointed at a real contact address.
4. `SECURITY.md` is present with a working reporting channel.
5. `CHANGELOG.md` exists and has an entry for the first release.
6. CI runs tests, lints, license scan, and `diff_contracts.py` on every PR.
7. Every dependency license is on the allow-list.
8. A release candidate (`0.9.0-rc.1` or `1.0.0-rc.1`) has been published to the registry and installed from scratch in a clean container — confirming publish metadata, install steps, and basic usage work end-to-end.
9. A real downstream user has tried the RC and confirmed the documented install works for them on a machine the maintainers do not control.

**Composition with other tracks.** Open source composes cleanly with most other tracks but two interactions matter:

- **Open source + Fintech.** Rare but real (e.g. an open-source payments SDK). The fintech track's idempotency and reconciliation gates still apply, but the public-API stability of this track overrides fintech's willingness to make late-breaking changes. Semver discipline wins.
- **Open source + Regulated / government.** A library published publicly but used inside regulated environments. Run both. License-compliance gate tightens (some regulated contexts require specific licenses). SBOM publication becomes a hard requirement, not just Rigorous-only.

**What the track deliberately does not solve.** Project governance (who decides disputes, how maintainers are added, how the project handles a fork), commercial monetisation strategy, community management at foundation scale, and trademark / brand policy. These matter but are outside this track's scope. Small teams rarely need them until they hit thousands of contributors; at that point, foundation frameworks (CNCF, Apache, Eclipse) are the right fit and the track's role ends.

---

## Worked activation example

A three-person team runs a Rust library wrapping a payments API. Adoption is about 200 downloads per week on crates.io. The team declares:

> "Standard mode, Open source track — add retry-on-503 to the request layer"

The track fires. `specification-driven-development` is mandatory and loads `semver-discipline.md`. The design doc must classify every new export as stable or experimental. `dependency-health-management` inspects the new dependency (`backoff` crate) and confirms its license is MIT, on the allow-list. `diff_contracts.py` runs on the release PR and reports one ADDED export (a new `RetryPolicy` struct) with no CHANGED-BREAKING entries; the release is MINOR.

A week later an external contributor opens a PR adding a second retry strategy. `pr-merge-orchestrator` fires with the Open source reference injected. The PR lacks a DCO sign-off; the check fails. A maintainer comments the fix (`git commit --amend -s && git push --force-with-lease`). The contributor signs off, CI goes green, and the PR merges.

A month later a researcher emails `security@` about a credential-leak in a log line at debug level. `security-audit-secure-sdlc` fires with `security-disclosure-policy.md` loaded. The team acknowledges within 3 days, requests a CVE through the GitHub Security Advisory, fixes the issue in a private fork, releases `1.4.2`, and publishes the advisory on day 18 — well inside the 90-day window. The CHANGELOG gains a `### Security` entry referencing the advisory; the release-PR is marked as a patch bump.

---

## Health signals

A healthy OSS project running this track shows these signals over a quarter:

- `diff_contracts.py` catches at least one accidental breaking change before release (prevention, not theory).
- At least one external PR merges per month (the contributor pipeline is not a ghost town).
- Issue-response SLA met on 90%+ of new issues; PR-review SLA met on 80%+ of new PRs.
- Zero dependency license violations on the allow-list in the last quarter.
- At most one point release per week (if more, patch discipline has slipped — triage before shipping).
- Any security report has a documented trail from receipt to advisory, even if the outcome was "not a vulnerability".

If signals drift, the fix is usually to tighten one of: triage cadence, CI enforcement of `diff_contracts.py`, or the license allow-list. Do not loosen the gates — loosen the scope instead (reduce supported runtime versions, mark more surface as experimental, remove underused features through the deprecation lifecycle).

---

## Skill execution log

Track activation logs to `docs/skill-log.md`:

```
[YYYY-MM-DD] track-activated: open-source | mode: <Mode> | duration: project
```

Skill firings under this track append the track context:

```
[YYYY-MM-DD] api-contract-enforcer | outcome: OK | note: diff_contracts.py passed — minor bump | track: open-source
[YYYY-MM-DD] security-audit-secure-sdlc | outcome: OK | note: CVE triaged and patched; advisory drafted | track: open-source
```
