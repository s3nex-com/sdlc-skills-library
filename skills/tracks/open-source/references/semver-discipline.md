# Semver discipline

Semver is a contract between the library and every downstream consumer. The contract is simple on paper and violated constantly in practice because "breaking change" is narrower than people think. This reference fixes the definition and shows how to detect violations before release, not after.

---

## The contract

Given a version `MAJOR.MINOR.PATCH`:

- **MAJOR** — you broke the public API. Consumers must read the migration guide and possibly change code.
- **MINOR** — you added capability. Existing code keeps working without change.
- **PATCH** — you fixed a bug without changing behaviour of correct code.

The public API is everything documented, exported, and not marked internal or experimental. If it is reachable via the registry name and any supported language mechanism (import, require, `use`, `#include`), it is public.

---

## What counts as a breaking change

The obvious cases everyone gets right:

- Removing an exported function, class, type, constant, or module
- Renaming any of the above without an alias
- Changing a function's required parameters (adding a required parameter is breaking; removing an optional parameter is breaking)
- Changing a function's return type to something not assignable from the previous type
- Changing a class's constructor signature in an incompatible way
- Moving a symbol between modules without re-exporting from the old path

The non-obvious cases almost everyone gets wrong:

- **Changing an error type or error message that downstream parses.** If users pattern-match on `err.message === "not found"` and you change it to `"resource not found"`, you broke them. Error type changes always breaking; error message changes breaking if the message is documented or stable enough to be matched in practice.
- **Changing a default value.** `timeout` defaulting to 30s and now defaults to 5s is a breaking change even though the signature is identical.
- **Tightening a dependency range.** If your library declared `peerDependency: react ">=17"` and you tighten to `">=18"`, every React 17 consumer breaks on install.
- **Tightening runtime requirements.** Requiring Node 20 when you previously supported Node 18 is a breaking change. Requiring a new OS capability is a breaking change.
- **Removing a polyfill or internal shim that downstream code observably relied on.**
- **Changing iteration order where none was documented but consumers came to rely on stability.** Controversial — document the iteration guarantee explicitly to avoid this trap.
- **Changing the set of events emitted, their names, their payload shape, or their firing order.**
- **Changing log format or log levels if your library is used in log-parsing pipelines.** Usually not breaking, but call it out in the changelog.
- **Narrowing an input type.** `function f(x: string | number)` → `function f(x: string)` is breaking even if every current caller happens to pass strings.
- **Widening an output type.** `function f(): User` → `function f(): User | null` is breaking because callers now need to handle null.

When in doubt, treat it as breaking. A false-positive breaking-change label costs a MAJOR bump. A false-negative costs user trust.

---

## `0.x` versus `1.x+`

Under `0.x`, the semver spec permits breaking changes on any minor bump. In practice consumers still scream. Two workable policies:

- **Strict 0.x (preferred for pre-1.0 libraries with real users):** Treat `0.MINOR.PATCH` as if it were `MAJOR.MINOR.PATCH` — breaking changes bump MINOR, features bump PATCH. Document the convention in the README. This is what most modern registries and tools assume.
- **Spec-literal 0.x:** Breaking changes allowed on every minor bump. Only safe if the library is explicitly pre-release and the README says so in the first paragraph. Do not use this on a library that has entered production elsewhere.

Cross the `1.0.0` line when the public API is stable enough that you will commit to a MAJOR bump every time it breaks. Do not cross it to signal maturity or marketing — cross it when you are ready for the semver contract.

---

## Pre-releases

Pre-release tags (`-alpha.1`, `-beta.2`, `-rc.1`) carry no semver guarantees. They exist to publish work-in-progress to real users for feedback.

- **`alpha`** — internal-quality, may break on every publish, feedback welcome from early adopters
- **`beta`** — feature-complete for the target version, may still break on API feedback, no production use expected
- **`rc` (release candidate)** — API frozen, only blocking bugs fixed between `rc.N` and final release

On npm/PyPI/Crates, publish pre-releases to a separate dist-tag (`next`, `beta`) so `@latest` stays on the stable line. Consumers opt in by installing the tag.

Pre-release versioning: `1.2.0-beta.1` means "the upcoming 1.2.0, first beta". Do not use `1.1.0-beta` for something that will ship as `1.2.0`.

---

## Major versus minor — the judgment call

Cases where the rule is clear:

| Change | Bump |
|--------|------|
| Added a new exported function | MINOR |
| Fixed a bug without behaviour change | PATCH |
| Fixed a bug where behaviour change is part of the fix | MINOR at minimum, MAJOR if consumers likely depend on the broken behaviour |
| Deprecated a function (still works, emits warning) | MINOR |
| Removed a previously deprecated function | MAJOR |
| Added a new optional parameter | MINOR |
| Made a previously-required parameter optional | MINOR |

Cases where the judgment matters:

- **A bug fix that changes documented behaviour.** If the docs said `X` and the code did `Y`, fixing the code to do `X` is a bug fix — but if users relied on `Y`, you broke them. Default: document it prominently in the changelog under Fixed, and if the broken behaviour was long-standing, bump MAJOR.
- **A performance improvement that changes observable timing.** Usually PATCH. Bump MINOR if the improvement changes ordering (e.g. parallel execution replaces sequential) in a way that leaks through the API.
- **A security fix that requires a config change.** MAJOR if old configs stop working. MINOR if old configs keep working but emit a warning.

---

## Detecting breakage in CI

Rely on three complementary checks. All three must be wired into the release pipeline, not optional.

### 1. Contract diff (`diff_contracts.py`)

Run `scripts/diff_contracts.py --from=<last-tag> --to=HEAD` as part of the release PR workflow. The script:

- Extracts the exported public API from the previous release tag
- Extracts the current public API from HEAD
- Diffs the two with awareness of signature changes, type narrowing, removed exports
- Classifies each diff as ADDED / CHANGED-SAFE / CHANGED-BREAKING / REMOVED
- Exits non-zero if any CHANGED-BREAKING or REMOVED entries exist and the release PR does not include a MAJOR bump

Hook this into CI as a required check on release PRs.

### 2. Integration tests against a real downstream

Pick one real downstream consumer (or a synthetic one you control). Pin it to the previous minor. On every release PR, build the candidate version and run the downstream's test suite against it. A passing suite is evidence of backwards compatibility. A failing suite on a non-MAJOR release PR blocks the merge.

Minimum viable version: a `tests/integration-downstream/` directory with a tiny project that imports your library, calls a representative subset of the public API, and asserts known-good output. Expand as incidents surface real gaps.

### 3. Cross-version compatibility matrix (Rigorous only)

For libraries where consumers pin to specific majors for long periods, maintain a matrix that tests the current release against the last N supported runtime versions (Node 18, 20, 22 for a JS library; Python 3.10, 3.11, 3.12 for a Python library). A failure in the matrix is a breakage in the supported range and blocks release.

---

## Worked example — non-obvious breaking change caught by the matrix

`my-http-client@2.3.0` documents a default timeout of 30 seconds. In PR #412, the author changes the default to 5 seconds to reduce tail latency in healthy networks. The test suite passes. `diff_contracts.py` reports CHANGED-SAFE because the signature is unchanged.

The downstream integration test pins `my-http-client@2.2.0` semantics and issues a request that takes 10 seconds on a slow CI agent. At 2.3.0 it fails with a timeout. The integration suite reports the regression. The release PR is blocked.

The author has two choices:
1. Bump MAJOR to `3.0.0`, call out the default-change in the changelog, and provide a migration note.
2. Keep the default at 30 seconds and add a `fastDefaults: true` option that opts into the new behaviour. Release as `2.4.0`.

Option 2 is almost always correct. The cost of forcing a MAJOR on every caller of a widely-used library is enormous. Only bump MAJOR when the new default is materially more correct for the overwhelming majority of callers.

---

## The release-PR checklist

Every release PR carries the following in its description. Release-readiness checks for all six.

1. **Semver bump justification.** One sentence per classification: "This is a MINOR bump because X, Y, Z were added and nothing was removed or behaviour-changed." The justification is written before the version is chosen, not after.
2. **`diff_contracts.py` output attached.** Paste the summary output into the PR. Reviewers scan it.
3. **CHANGELOG entry.** `### Added / Changed / Deprecated / Removed / Fixed / Security` sections per Keep-A-Changelog.
4. **Migration notes for any breaking change.** Link to the migration guide. If the guide does not exist yet, the release is not ready.
5. **Downstream integration test passed.** Green check from the integration workflow on the PR.
6. **Registry dry-run.** `npm pack` / `cargo publish --dry-run` / equivalent has been run locally and its output inspected for surprises (stray files, wrong license field, missing README).

A release PR missing any of the six is not merged. These are not aspirational — they are gate conditions.

---

## Anti-patterns to reject

- **"Chicken version" bumping.** Shipping `2.5.0` when the change is a bug fix because a stakeholder "expected a minor this quarter". Semver is a contract, not a marketing cadence.
- **Squatting on MAJOR forever.** Refusing to bump MAJOR because "we don't want to scare users". The scare is real; the contamination is worse. If the change is breaking, bump MAJOR and ship the migration guide.
- **Secret breaking changes in a patch.** "Just a bug fix" that alters the error type, default value, or iteration order. This destroys downstream trust faster than any other single mistake.
- **Re-tagging a release after publish.** Once `1.4.2` is on the registry, `1.4.2` is immutable. A fix to a bad release is `1.4.3`, not a re-push. Most registries forbid re-pushing by default; do not ask them to disable the safeguard.
