# License compliance

A license is a contract between the project and every consumer. Pick one deliberately, declare it in machine-readable form, track the licenses of every dependency, and refuse contributions under incompatible terms. Getting this wrong propagates quietly for years and is expensive to unwind.

---

## Picking a license — trade-off table

| License | Permissive / Copyleft | Patent grant | Can be used in closed source | Key property |
|---------|----------------------|--------------|------------------------------|--------------|
| MIT | Permissive | No explicit grant | Yes | Simplest permissive license. Short text. Widest ecosystem compatibility. |
| Apache 2.0 | Permissive | Explicit patent grant + defensive termination | Yes | MIT with teeth. Explicit patent protection. Longer text, boilerplate required in source files. |
| BSD-3-Clause | Permissive | No explicit grant | Yes | MIT-equivalent with a no-endorsement clause. Slightly less common. |
| MPL 2.0 | Weak copyleft (file-level) | Explicit patent grant | Yes (static or dynamic linking OK; modifications to MPL files must stay MPL) | Middle ground: copyleft on your files, not on the larger work. |
| LGPL 2.1 / 3.0 | Weak copyleft (library-level) | 3.0 has patent grant | Yes via dynamic linking | Users can link without copyleft exposure if they link dynamically and allow library replacement. Static linking or embedded use pulls in copyleft. Complex in practice. |
| GPL 2.0 / 3.0 | Strong copyleft | 3.0 has patent grant | No — combining triggers copyleft on the combined work | Anything that links to GPL code must itself be GPL on distribution. |
| AGPL 3.0 | Strong copyleft + network use clause | Explicit patent grant | No — SaaS use triggers copyleft disclosure | GPL plus: serving the software over a network counts as distribution. Used to prevent proprietary SaaS forks. |

### Decision rules

- **Default for a library you want widely adopted: MIT or Apache 2.0.** Pick MIT for simplicity. Pick Apache 2.0 if patent protection matters (ML models, hardware-adjacent work, or anywhere patent litigation is a real risk).
- **Default for a library where you want a commercial moat against SaaS resale: AGPL 3.0** paired with a commercial license offered separately (dual licensing — see below).
- **Default for a library mostly consumed by GPL projects: GPL 3.0** to reduce license-compatibility friction in your ecosystem.
- **Avoid for a new project: MPL, LGPL, BSD-3-Clause.** They are valid but carry edge cases that confuse downstream users. Only choose them if you have a specific reason the simpler options do not cover.
- **Avoid entirely for new OSS projects: custom or non-OSI-approved licenses.** "Source available" licenses like BUSL, SSPL, and Elastic License are not open source and will be rejected by most package registries' default policies, corporate procurement, and many distributions. If you want source-available-but-not-OSS, that is a valid business model, but do not call it open source.

---

## Dual licensing

Offering the same code under two licenses lets one group use it under permissive terms and another under terms that protect a commercial position.

**Common pattern 1: MIT + Apache 2.0** (increasingly standard for Rust and Go ecosystems). The dual grant lets consumers pick whichever they prefer. There is no commercial aspect — it is purely ecosystem compatibility. Declare in `README.md`:

> Licensed under either of Apache License, Version 2.0 or MIT license at your option.

Declare in `Cargo.toml` / equivalent:

```
license = "MIT OR Apache-2.0"
```

**Common pattern 2: AGPL + commercial.** The project is AGPL for OSS use. Commercial customers who cannot comply with AGPL's network-use clause buy a commercial license that removes the copyleft obligation. The project needs a Contributor License Agreement (CLA) rather than DCO for this to work — contributors must grant the project the right to relicense their contributions.

**Common pattern 3: Elastic / BUSL + time-delayed OSS.** The code is restricted for a period (typically 2–4 years), then automatically re-licensed to an OSI-approved license. Used when the commercial moat is short-term and the community benefit is long-term. Handle carefully — "source-available now, OSS later" confuses users about what they can do today.

---

## Handling contributions under different licenses

Contributions to an open source project default to the project's license unless the contributor explicitly states otherwise. But real-world contributions carry surprises.

Cases to watch for and how to handle each:

- **A PR imports code from another OSS project.** Check the source project's license:
  - If it is the same license as yours (e.g. both MIT), merge with attribution in a NOTICE or source header.
  - If it is compatible (permissive into your project), merge with attribution.
  - If it is incompatible (GPL code into an MIT project; AGPL code into an Apache project), reject. Do not sneak it in. License contamination is almost impossible to undo.
- **A PR is copy-pasted from Stack Overflow.** Stack Overflow answers are CC-BY-SA 4.0 by default (or CC-BY-SA 3.0 for older answers). Neither is compatible with most OSS licenses for substantive chunks. Small snippets are usually below the threshold of originality, but multi-line algorithmic code is not. When in doubt, ask the contributor to write an independent implementation.
- **A PR contains AI-generated code.** Current consensus: treat AI-generated code as authored by the contributor who prompted and reviewed it, provided they attest to ownership (which is what DCO sign-off certifies). If your CLA has stricter language, it still applies.
- **A contributor refuses DCO / CLA.** Close the PR. Policy is non-negotiable. A contributor who won't sign off is not contributing — they are dropping code in the yard.
- **A contributor is a corporate employee without employer sign-off.** For CLA projects, many CLAs require the employer to countersign. For DCO projects, the DCO attestation includes "I have the right to submit" which covers this only if the employer allows. Corporate contributors should confirm internally; maintainers are not in a position to verify.

---

## Attribution requirements

At minimum, every OSS project must ship:

- `LICENSE` file at the repo root containing the verbatim license text
- License identifier in package metadata (`license` field in `package.json`, `Cargo.toml`, `pyproject.toml`, etc.) using an SPDX identifier
- Copyright notice in `LICENSE` naming the copyright holders

For Apache 2.0 specifically, include a `NOTICE` file at the repo root if the project inherits NOTICE entries from dependencies. Apache 2.0 requires propagating NOTICE contents, not just the LICENSE.

For dependencies shipped as part of the release artifact (vendored code, bundled static binaries, compiled-in libraries), include their license text in a `third_party/licenses/` directory or equivalent. Permissive licenses typically require this; copyleft licenses require much more (see copyleft exposure below).

---

## SPDX identifiers

SPDX is the machine-readable license identifier standard. Use it everywhere license metadata is declared.

Common SPDX identifiers:

| License | SPDX identifier |
|---------|-----------------|
| MIT | `MIT` |
| Apache 2.0 | `Apache-2.0` |
| BSD-3-Clause | `BSD-3-Clause` |
| MPL 2.0 | `MPL-2.0` |
| LGPL 3.0 (only) | `LGPL-3.0-only` |
| LGPL 3.0 (or later) | `LGPL-3.0-or-later` |
| GPL 3.0 (only) | `GPL-3.0-only` |
| GPL 3.0 (or later) | `GPL-3.0-or-later` |
| AGPL 3.0 (or later) | `AGPL-3.0-or-later` |
| Dual MIT + Apache 2.0 | `MIT OR Apache-2.0` |

Declare in package metadata:

```json
// package.json
"license": "MIT"
```

```toml
# Cargo.toml
license = "MIT OR Apache-2.0"
```

```toml
# pyproject.toml
[project]
license = { text = "Apache-2.0" }
```

Per-file SPDX headers are optional but help automated license scanners. Format:

```
// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 The Example Project Authors
```

---

## Copyleft exposure in dependencies

A single GPL / AGPL dependency can relicense your permissively-licensed project. Guard the dependency boundary with a scanner and a policy.

### Scanning

Run a license scanner on every release:

- `license-checker` (npm)
- `pip-licenses` (Python)
- `cargo-license` (Rust)
- `go-licenses` (Go)
- `scancode-toolkit` (language-agnostic, thorough, slower)
- `Syft` (generates SBOMs with license metadata)

Fail the release if the scanner reports any dependency whose license is outside the project's allow-list.

### Policy

Declare the allow-list explicitly. A standard permissive allow-list:

```
ALLOWED_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
    "ISC", "0BSD", "Unlicense", "CC0-1.0", "MPL-2.0",
    "Python-2.0",  # Python standard library
}
```

Anything else requires explicit review. A GPL dependency is not automatically a crisis — it might be OK if the dependency is a build-time tool and not linked into the distributed artifact. But it must be reviewed, not accidentally merged.

### Exposure at the artifact boundary

The critical question is what ships in the final artifact consumers install:

- **Static binary or bundled JS:** dependencies are embedded. Their licenses propagate to the artifact. A GPL static dependency makes the artifact GPL.
- **Dynamic library / runtime dependency:** depends on the license. LGPL explicitly permits dynamic linking without copyleft propagation. GPL does not.
- **Build-time tooling (linter, test runner, codegen):** does not ship in the artifact. GPL is usually fine here, but check each license — some GPL variants affect build-time use too.
- **Transpilation-only use (a GPL tool that generates non-derivative output):** usually fine, but consult the specific license.

When in doubt, route the dependency through a reviewer who understands license compatibility, not through a developer who just wants the feature merged. License mistakes cost far more to fix later than they cost to prevent now.

---

## SBOM for the release artifact

In Rigorous mode the track mandates an SBOM published alongside each release. Generate with `syft` or `cyclonedx-bom`:

```bash
syft packages dir:. -o cyclonedx-json > sbom.cdx.json
```

Attach `sbom.cdx.json` to the GitHub Release. Sign with Sigstore / cosign if the track is set to Rigorous. Downstream consumers running supply-chain scanners will ingest the SBOM automatically.
