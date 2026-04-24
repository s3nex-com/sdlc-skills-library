"""
sdlc-skills-library Track Validator

Validates every TRACK.md under skills/tracks/ has all 8 required sections.
Parallel to skill_health.py, but for tracks.

Required sections:
  1. YAML frontmatter (--- block with name: and description:)
  2. Purpose
  3. When to activate
  4. When NOT to activate
  5. Skill elevations
  6. Gate modifications
  7. Reference injection map
  8. Reference files

Usage:
    python scripts/track_validator.py                 # scan all TRACK.md files
    python scripts/track_validator.py --path skills/  # scan a specific directory
    python scripts/track_validator.py --json          # JSON output
    python scripts/track_validator.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEPARATOR = "-" * 60

# Each entry: (label, regex_pattern_or_None, description_for_error)
SECTION_CHECKS = [
    (
        "YAML frontmatter",
        None,
        "missing YAML frontmatter (file must start with --- and contain name: and description:)",
    ),
    (
        "Purpose",
        re.compile(r"^#{1,2}\s+Purpose", re.MULTILINE | re.IGNORECASE),
        'missing "Purpose" section',
    ),
    (
        "When to activate",
        re.compile(r"^#{1,3}\s+When to activate", re.MULTILINE | re.IGNORECASE),
        'missing "When to activate" section',
    ),
    (
        "When NOT to activate",
        re.compile(r"^#{1,3}\s+When not to activate", re.MULTILINE | re.IGNORECASE),
        'missing "When NOT to activate" section',
    ),
    (
        "Skill elevations",
        re.compile(r"^#{1,3}\s+Skill elevations", re.MULTILINE | re.IGNORECASE),
        'missing "Skill elevations" section',
    ),
    (
        "Gate modifications",
        re.compile(r"^#{1,3}\s+Gate modifications", re.MULTILINE | re.IGNORECASE),
        'missing "Gate modifications" section',
    ),
    (
        "Reference injection map",
        re.compile(r"^#{1,3}\s+Reference injection", re.MULTILINE | re.IGNORECASE),
        'missing "Reference injection map" section',
    ),
    (
        "Reference files",
        re.compile(r"^#{1,3}\s+Reference files", re.MULTILINE | re.IGNORECASE),
        'missing "Reference files" section',
    ),
]


def check_frontmatter(content: str) -> bool:
    if not content.startswith("---"):
        return False
    end = content.find("\n---", 3)
    if end == -1:
        return False
    frontmatter = content[3:end]
    has_name = bool(re.search(r"^name\s*:", frontmatter, re.MULTILINE))
    has_description = bool(re.search(r"^description\s*:", frontmatter, re.MULTILINE))
    return has_name and has_description


def scan_track(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        return {
            "path": str(path),
            "name": path.parent.name,
            "missing_sections": [],
            "status": "ERROR",
            "error": str(e),
        }

    missing: list[str] = []

    if not check_frontmatter(content):
        missing.append(SECTION_CHECKS[0][2])

    for label, pattern, _ in SECTION_CHECKS[1:]:
        if not pattern.search(content):
            missing.append(f'"{label}"')

    status = "FAIL" if missing else "PASS"

    return {
        "path": str(path),
        "name": path.parent.name,
        "missing_sections": missing,
        "status": status,
    }


def find_track_files(root: Path) -> list[Path]:
    # Exclude the template file — it's not a real track
    return sorted(
        p for p in root.rglob("TRACK.md")
        if p.name == "TRACK.md"
    )


def format_text(results: list[dict]) -> tuple[str, int, int]:
    passes = sum(1 for r in results if r["status"] == "PASS")
    fails = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    total = len(results)

    lines = [f"Track validator — {total} TRACK.md files scanned", SEPARATOR]
    for r in results:
        status = r["status"]
        name = r["name"]
        if status == "PASS":
            lines.append(f"PASS  {name:<30} all 8 sections present")
        elif status == "FAIL":
            lines.append(f"FAIL  {name:<30} missing: {', '.join(r['missing_sections'])}")
        else:
            lines.append(f"ERROR {name:<30} {r.get('error', 'unknown')}")

    lines.append("")
    lines.append(f"Results: {passes} PASS, {fails} FAIL")
    return "\n".join(lines), passes, fails


def format_json(results: list[dict]) -> str:
    passes = sum(1 for r in results if r["status"] == "PASS")
    fails = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    output = {
        "total": len(results),
        "pass": passes,
        "fail": fails,
        "results": results,
    }
    return json.dumps(output, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Track Validator — validates all TRACK.md files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/track_validator.py
  python scripts/track_validator.py --path skills/tracks
  python scripts/track_validator.py --json
        """,
    )
    parser.add_argument("--path", default=None, help="Root directory to scan")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    scan_root = Path(args.path).resolve() if args.path else repo_root / "skills" / "tracks"

    if not scan_root.exists():
        print(f"Error: path does not exist: {scan_root}", file=sys.stderr)
        sys.exit(2)

    tracks = find_track_files(scan_root)
    if not tracks:
        print(f"No TRACK.md files found under {scan_root}", file=sys.stderr)
        sys.exit(0)

    results = [scan_track(p) for p in tracks]

    if args.json:
        print(format_json(results))
    else:
        text, passes, fails = format_text(results)
        print(text)

    fails = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
