"""
sdlc-skills-library Track Elevation Checker

Verifies that every skill named in a TRACK.md's "Skill elevations" table maps
to a real skill directory under skills/phase1, skills/phase2, skills/phase3,
skills/phase4, or skills/workflow.

Also surfaces skill names mentioned in the "Reference injection map" section
that do not resolve to real skills.

Usage:
    python scripts/check_track_elevations.py
    python scripts/check_track_elevations.py --path skills/tracks
    python scripts/check_track_elevations.py --json
    python scripts/check_track_elevations.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEPARATOR = "-" * 60


def discover_skills(repo_root: Path) -> set[str]:
    """Return the set of skill directory names under skills/phaseN and skills/workflow."""
    skills = set()
    for phase in ("phase1", "phase2", "phase3", "phase4", "workflow"):
        phase_dir = repo_root / "skills" / phase
        if not phase_dir.exists():
            continue
        for entry in phase_dir.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").exists():
                skills.add(entry.name)
    return skills


def extract_section(content: str, heading_regex: str) -> str:
    """Return the text under a given `## Heading`, up to the next `## ` or end of file."""
    match = re.search(heading_regex, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_section = re.search(r"\n##\s+", content[start:])
    end = start + next_section.start() if next_section else len(content)
    return content[start:end]


# Only kebab-case identifiers with at least two segments (foo-bar or foo-bar-baz)
# surrounded by word boundaries. This is the canonical skill name shape.
SKILL_NAME_RE = re.compile(r"(?<![A-Za-z0-9_`/])([a-z][a-z0-9]+(?:-[a-z0-9]+){1,})(?![A-Za-z0-9_\-\./])")


def extract_first_column_cells(section: str) -> set[str]:
    """
    Walk the markdown table(s) inside `section` and return every first-cell value.
    Skips header row, separator row (| --- | --- |), and non-table lines.
    Also strips formatting like backticks.
    """
    cells = set()
    header_seen = False
    separator_seen = False

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if line.startswith("|") and line.endswith("|"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if not parts:
                continue
            # Separator row: | --- | --- |
            if all(re.fullmatch(r":?-+:?", p) for p in parts if p):
                separator_seen = True
                continue
            if not header_seen:
                header_seen = True
                continue
            # This is a data row (after header, regardless of whether we saw separator)
            if not separator_seen:
                # We haven't crossed the separator yet; treat as header, skip
                continue
            first = parts[0].strip("`* ")
            if first:
                cells.add(first)
        else:
            # Non-table line resets table state if we had one
            if header_seen:
                header_seen = False
                separator_seen = False

    return cells


def extract_injection_skills(section: str) -> set[str]:
    """
    Skill names in the injection map come in two shapes:
      - Markdown table first-column cells
      - Bullet list: `- skill-name → ...` or `- skill-name (when ...) → ...`
    """
    skills = set(extract_first_column_cells(section))

    # Bullets with an arrow — the token before the arrow is the skill.
    bullet_arrow = re.compile(r"^\s*-\s+`?([a-z][a-z0-9]+(?:-[a-z0-9]+){1,})`?", re.MULTILINE)
    for m in bullet_arrow.finditer(section):
        # Only keep if the line contains an arrow or "→" or "when ... fires"
        # (otherwise bullets may not be skill references). We accept loosely.
        skills.add(m.group(1))

    return skills


def filter_skill_candidates(tokens: set[str]) -> set[str]:
    """Remove tokens that clearly aren't skill names."""
    filtered = set()
    for t in tokens:
        # Strip trailing punctuation, pipe remnants
        t = t.strip().strip(",.:;()*`")
        if not t:
            continue
        # Must match kebab-case shape
        if not re.fullmatch(r"[a-z][a-z0-9]+(?:-[a-z0-9]+){1,}", t):
            continue
        filtered.add(t)
    return filtered


def check_track(track_path: Path, known_skills: set[str]) -> dict:
    content = track_path.read_text(encoding="utf-8")

    elevations_section = extract_section(content, r"^##\s+Skill elevations")
    injection_section = extract_section(content, r"^##\s+Reference injection")

    elevations = filter_skill_candidates(extract_first_column_cells(elevations_section))
    injection = filter_skill_candidates(extract_injection_skills(injection_section))

    elevation_misses = sorted(c for c in elevations if c not in known_skills)
    injection_misses = sorted(c for c in injection if c not in known_skills)

    status = "FAIL" if (elevation_misses or injection_misses) else "PASS"

    return {
        "path": str(track_path),
        "name": track_path.parent.name,
        "elevations_found": sorted(elevations),
        "injection_found": sorted(injection),
        "elevation_misses": elevation_misses,
        "injection_misses": injection_misses,
        "status": status,
    }


def format_text(results: list[dict]) -> str:
    lines = [f"Track elevation check — {len(results)} tracks scanned", SEPARATOR]
    passes = fails = 0
    for r in results:
        if r["status"] == "PASS":
            passes += 1
            lines.append(f"PASS  {r['name']:<30} all referenced skills resolved")
        else:
            fails += 1
            lines.append(f"FAIL  {r['name']}")
            if r["elevation_misses"]:
                lines.append(
                    f"      unresolved in elevations: {', '.join(r['elevation_misses'])}"
                )
            if r["injection_misses"]:
                lines.append(
                    f"      unresolved in injection map: {', '.join(r['injection_misses'])}"
                )
    lines.append("")
    lines.append(f"Results: {passes} PASS, {fails} FAIL")
    return "\n".join(lines)


def format_json(results: list[dict]) -> str:
    passes = sum(1 for r in results if r["status"] == "PASS")
    fails = sum(1 for r in results if r["status"] == "FAIL")
    return json.dumps(
        {
            "total": len(results),
            "pass": passes,
            "fail": fails,
            "results": results,
        },
        indent=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Track Elevation Checker — verify skill names in TRACK.md resolve to real skills.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/check_track_elevations.py
  python scripts/check_track_elevations.py --path skills/tracks
  python scripts/check_track_elevations.py --json
        """,
    )
    parser.add_argument("--path", default=None, help="Directory to scan for TRACK.md files")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    tracks_root = Path(args.path).resolve() if args.path else repo_root / "skills" / "tracks"

    known_skills = discover_skills(repo_root)
    if not known_skills:
        print("No skills found — cannot validate elevations.", file=sys.stderr)
        sys.exit(2)

    tracks = sorted(
        p for p in tracks_root.rglob("TRACK.md") if p.name == "TRACK.md"
    )
    if not tracks:
        print(f"No TRACK.md files found under {tracks_root}", file=sys.stderr)
        sys.exit(0)

    results = [check_track(p, known_skills) for p in tracks]

    if args.json:
        print(format_json(results))
    else:
        print(format_text(results))

    fails = sum(1 for r in results if r["status"] == "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
