"""
sdlc-skills-library Reference Link Checker

Verifies that every file listed under the "Reference files" section of a
SKILL.md or TRACK.md actually exists on disk relative to that file.

Usage:
    python scripts/check_reference_links.py
    python scripts/check_reference_links.py --path skills/phase1
    python scripts/check_reference_links.py --json
    python scripts/check_reference_links.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REF_SECTION = re.compile(r"^##\s+Reference files", re.IGNORECASE)
NEXT_SECTION = re.compile(r"^##\s+", re.IGNORECASE)
REF_ENTRY = re.compile(r"^\s*-\s+`(references/[^`]+\.md)`")


def check_file(md_path: Path) -> list[dict]:
    errors = []
    base = md_path.parent
    in_ref_section = False
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if REF_SECTION.match(line):
            in_ref_section = True
            continue
        if in_ref_section and NEXT_SECTION.match(line):
            in_ref_section = False
        if in_ref_section:
            m = REF_ENTRY.match(line)
            if m:
                ref_rel = m.group(1)
                if not (base / ref_rel).exists():
                    errors.append({"file": str(md_path.relative_to(ROOT)), "missing": ref_rel})
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Reference Link Checker — verify all reference files exist."
    )
    parser.add_argument("--path", default="skills", help="root directory to scan (default: skills/)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="output JSON")
    args = parser.parse_args()

    scan_root = ROOT / args.path
    errors: list[dict] = []
    checked = 0

    for pattern in ("**/SKILL.md", "**/TRACK.md"):
        for md_path in sorted(scan_root.glob(pattern)):
            errors.extend(check_file(md_path))
            checked += 1

    if args.as_json:
        print(json.dumps({"checked": checked, "errors": errors}, indent=2))
        sys.exit(1 if errors else 0)

    if errors:
        print(f"FAIL — {len(errors)} broken reference link(s) across {checked} files:")
        for e in errors:
            print(f"  {e['file']}: missing {e['missing']}")
        sys.exit(1)

    print(f"PASS — {checked} files checked, all reference links resolve")


if __name__ == "__main__":
    main()
