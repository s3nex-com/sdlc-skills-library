"""
sdlc-skills-library INDEX.md Consistency Checker

Verifies two-way consistency between skills/INDEX.md and the actual skill
and track directories on disk:

  1. Every directory listed in INDEX.md must exist under skills/
  2. Every skills/**/SKILL.md must have its parent directory listed in INDEX.md
  3. Every skills/tracks/**/TRACK.md must have its parent directory listed in INDEX.md

Usage:
    python scripts/check_index.py
    python scripts/check_index.py --json
    python scripts/check_index.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "skills" / "INDEX.md"
SKILLS_ROOT = ROOT / "skills"

DIR_CELL = re.compile(r"`((?:phase\d|workflow|tracks)/[^`/]+/)`")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library INDEX.md Consistency Checker."
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="output JSON")
    args = parser.parse_args()

    errors: list[str] = []

    indexed: set[str] = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        for m in DIR_CELL.finditer(line):
            indexed.add(m.group(1).rstrip("/"))

    for rel in sorted(indexed):
        if not (SKILLS_ROOT / rel).is_dir():
            errors.append(f"INDEX.md lists `{rel}/` but directory does not exist")

    for skill_md in sorted(SKILLS_ROOT.glob("**/SKILL.md")):
        rel = str(skill_md.parent.relative_to(SKILLS_ROOT))
        if rel not in indexed:
            errors.append(f"skills/{rel}/SKILL.md exists but is not listed in INDEX.md")

    for track_md in sorted(SKILLS_ROOT.glob("tracks/**/TRACK.md")):
        rel = str(track_md.parent.relative_to(SKILLS_ROOT))
        if rel not in indexed:
            errors.append(f"skills/{rel}/TRACK.md exists but is not listed in INDEX.md")

    if args.as_json:
        print(json.dumps({"indexed": len(indexed), "errors": errors}, indent=2))
        sys.exit(1 if errors else 0)

    if errors:
        print(f"FAIL — {len(errors)} INDEX inconsistency(ies):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    print(f"PASS — INDEX.md consistent ({len(indexed)} directories verified)")


if __name__ == "__main__":
    main()
