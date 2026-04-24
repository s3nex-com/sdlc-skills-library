---
name: example-track
description: >
  Activates when the user mentions [domain activation phrase 1], [phrase 2], [phrase 3],
  or when the PRD keywords indicate [domain signal]. Also triggers on explicit
  declaration: "X track" or "in the X domain".
---

# Example track

<!--
  This is the TRACK.md template. Copy this file to
  skills/tracks/<your-track-name>/TRACK.md and fill every section. The 8 sections
  below are required — track_validator.py fails if any are missing.

  Keep TRACK.md lean. Move heavy content (checklists, worked examples, decision
  tables) into references/. TRACK.md is the contract; references are the library.
-->

## Purpose

<!--
  One paragraph in plain English. What domain this track covers and why that domain
  needs a specialization layer. Name the class of product, not the tooling
  (e.g. "products handling card data" not "Stripe integrations").
-->

[One paragraph describing the domain, the signals that make this domain distinct,
and why the standard 41-skill library with modes alone is insufficient.]

---

## When to activate

<!--
  The specific signals that should activate this track. Explicit phrases the user
  says, keywords in a PRD, architectural patterns visible in existing code.
  Be concrete — activation is about matching, not vibes.
-->

Activate this track when the user mentions or the PRD contains:

- "[phrase 1]"
- "[phrase 2]"
- "[phrase 3]"

Or when the system under discussion has these properties:

- [architectural signal 1]
- [architectural signal 2]

---

## When NOT to activate

<!--
  Adjacent domains that look like this one but belong to a different track.
  Parallel to SKILL.md's "When NOT to use" — this keeps tracks from bleeding
  into each other. Non-negotiable.
-->

Do NOT activate this track when:

- [Adjacent scenario 1] — use [other track] instead
- [Adjacent scenario 2] — no track needed; standard mode is sufficient
- [Adjacent scenario 3] — this is a [workflow path], not a track

---

## Skill elevations

<!--
  Table of skills × modes. Cell values:
    - "Advisory"    — skill fires if conditions match but does not block the gate
    - "Mandatory"   — skill must fire; gate fails otherwise
    - "N/A"         — skill does not apply in this mode
    - Any text after Mandatory describes the additional requirement
      (e.g., "Mandatory + PCI checklist", "Mandatory + external review")

  Only list skills whose treatment differs from the default mode behaviour.
  Skills whose default is already correct for this domain do not need a row.
-->

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| [skill-name-1] | Advisory | Mandatory | Mandatory + [extra] | Mandatory + [extra] |
| [skill-name-2] | ... | ... | ... | ... |

---

## Gate modifications

<!--
  Stage × modification. Every modification is either a new required piece of
  evidence, a tightened acceptance criterion, or a new sign-off requirement.
  Strictest-wins when multiple tracks modify the same gate.
-->

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan)     | [new evidence or tightened criterion, if any] |
| Stage 2 (Design)   | [new evidence or tightened criterion, if any] |
| Stage 3 (Build)    | [new evidence or tightened criterion, if any] |
| Stage 4 (Verify)   | [new evidence or tightened criterion, if any] |
| Stage 5 (Ship)     | [new evidence or tightened criterion, if any] |
| Phase 3 (Ongoing)  | [new recurring cadence, if any] |

---

## Reference injection map

<!--
  When a given skill fires during this track, which track-specific references
  load alongside the skill's own references. This is how domain guidance reaches
  the skill without editing the skill.
-->

| When this skill fires | Also load these references |
|----------------------|----------------------------|
| [skill-name-1] | `references/[topic-1].md`, `references/[topic-2].md` |
| [skill-name-2] | `references/[topic-3].md` |

---

## Reference files

<!--
  List every file in references/ with a one-line description. The file names
  must match exactly — the reference injection map above refers to these files
  by name.
-->

- `references/[topic-1].md` — [one-line description]
- `references/[topic-2].md` — [one-line description]
- `references/[topic-3].md` — [one-line description]
