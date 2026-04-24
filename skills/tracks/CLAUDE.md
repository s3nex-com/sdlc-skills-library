# skills/tracks/ — domain specialization overlays

Tracks are curated overlays on the 41-skill library for specific domains. A track is not a skill — it is a lens that elevates mandatory skills, tightens gate criteria, and injects domain-specific reference material.

Full concept: `docs/tracks.md`. TRACK.md contract and template: `TRACK-TEMPLATE.md`.

---

## The 10 tracks

| Track | Directory | Covers | Min mode |
|-------|-----------|--------|----------|
| Fintech / Payments | `fintech-payments/` | Card data, money movement, PCI scope, regulated financial services | Lean |
| SaaS B2B | `saas-b2b/` | Multi-tenant products with SSO, RBAC, contractual SLAs, tenant-scoped caching | Lean |
| Web product | `web-product/` | Multi-user web apps: auth, RBAC, API + frontend, DB concurrency, subscription billing | Lean |
| Data platform / ML ops | `data-platform-mlops/` | Data pipelines, schema registries, ML/LLM production, compute cost governance | Lean |
| Healthcare / HIPAA | `healthcare-hipaa/` | PHI, HIPAA §164.308(a)(7) DR, HL7/FHIR, clinical data | Lean |
| Regulated / government | `regulated-government/` | FedRAMP, SOC 2, ISO 27001, CMMC, StateRAMP, DR testing as a control | Standard |
| Real-time / streaming | `real-time-streaming/` | Kafka/Kinesis/Pulsar, low-latency, stream processing, state-store caching | Lean |
| Consumer product | `consumer-product/` | B2C: experimentation, feed caching, notifications, viral mechanics, consumer-scale performance | Nano |
| Open source | `open-source/` | Public libraries with semver, contributor pipeline, CVE disclosure, contributor onboarding | Lean |
| Mobile | `mobile/` | iOS, Android, React Native, Flutter | Lean |

---

## Directory layout

```
tracks/
  <track-name>/
    TRACK.md              — the 8-section contract (parallel to SKILL.md)
    references/           — reference material loaded on demand
      <topic>.md
      ...
```

No `scripts/` directory in v1 — track-specific scripts are deferred until demand surfaces.

---

## How tracks compose with modes

Mode = how much rigor. Track = what domain.

- A session is always in exactly one **mode** (Nano / Lean / Standard / Rigorous).
- A session may be in **zero or more tracks**. Most projects run with zero. Multi-domain projects run with two or more.
- Multi-track composition: skill elevations union, gate modifications strictest-wins, reference injection additive.

See `docs/tracks.md` for the full mechanics and worked examples.

---

## Tracks vs workflow paths

Tracks (this directory) ≠ workflow paths (Hotfix / Spike / Brownfield, in `skills/workflow/`).

- A **track** modifies *how* a stage runs inside a given domain.
- A **workflow path** modifies *which* stages run (skip Stages 1–2 for Hotfix; skip Stages 3–5 for Spike; run an assessment pre-pipeline for Brownfield).

Workflow paths and tracks are orthogonal. `Lean + Fintech + Hotfix` is a valid combination — a payments hotfix where the hotfix path skips Stages 1–2 but fintech gate modifications still apply to Stages 3, 4, 5.

---

## Adding a new track

1. Copy `TRACK-TEMPLATE.md` to `<new-track-name>/TRACK.md`.
2. Fill all 8 sections. Every skill elevation must name a real skill in the library.
3. Write reference files under `<new-track-name>/references/`. Keep TRACK.md lean; references carry the weight.
4. Validate: `python scripts/track_validator.py` and `python scripts/check_track_elevations.py`.
5. Update `docs/tracks.md`, `docs/quickstart.md`, `docs/skill-triggers.md`, `skills/INDEX.md`, `README.md`, and this file.

---

## Mode-track minimum modes and conflict resolution

Every track has a minimum mode below which its gate requirements cannot be meaningfully satisfied. Operating below the minimum is not prohibited, but it requires an explicit scope declaration (e.g. "this Nano change does not touch the PHI path").

**Resolution rule:** Track elevations win over mode defaults. If a track mandates a skill at Nano that the Nano mode excludes, that skill runs. The orchestrator flags a mode below the track minimum and asks for confirmation or a scope declaration before proceeding.

Multi-track minimum: the highest minimum mode across all active tracks applies.

---

## Invariants — do not break these when editing a TRACK.md

**The 8-section contract is fixed.** Never collapse sections, never mark any as optional, never reorder. `track_validator.py` enforces this.

**Tracks never disable skills.** A track can elevate Advisory → Mandatory. It cannot turn a Mandatory skill off. If you think a skill should be suppressed for your domain, that is a mode decision, not a track decision.

**Elevations must reference real skills.** `check_track_elevations.py` walks every skill name in every TRACK.md and fails if it doesn't resolve to a real skill directory under `skills/phase1/`, `skills/phase2/`, `skills/phase3/`, `skills/phase4/`, or `skills/workflow/`.

**TRACK.md stays lean.** Reference material goes in `references/`. If your TRACK.md is over ~300 lines, move content to references.

**No enterprise ceremony.** Tracks add discipline, not bureaucracy. "Signed off by the compliance officer" in a 4-person team means a documented self-review in a PR comment — not a formal process.
