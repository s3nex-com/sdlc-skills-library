"""
sdlc-skills-library Skill Health Checker

Validates every SKILL.md in the library has all 8 required sections and checks
for stale references to replaced skill names.

Required sections checked:
  1. YAML frontmatter (--- block with name: and description:)
  2. Purpose section
  3. When to use section
  4. When NOT to use section
  5. Process or Checklist section
  6. Output section (flexible match)
  7. Skill execution log section (contains "skill-log.md")
  8. Reference files section

Usage:
    python scripts/skill_health.py                    # scan all SKILL.md files
    python scripts/skill_health.py --path skills/     # scan specific directory
    python scripts/skill_health.py --json             # JSON output
    python scripts/skill_health.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEPARATOR = "━" * 45

STALE_REFERENCES = [
    "inter-company-communications",
    "project-partner-governance",
    "formal-verification-chaos-engineering",
]

# Each entry: (label, regex_pattern, description_for_error)
SECTION_CHECKS = [
    (
        "YAML frontmatter",
        None,  # handled specially
        "missing YAML frontmatter (file must start with --- and contain name: and description:)",
    ),
    (
        "Purpose",
        re.compile(r"^#{1,2}\s+Purpose", re.MULTILINE | re.IGNORECASE),
        'missing "Purpose" section',
    ),
    (
        "When to use",
        re.compile(r"^#{1,3}\s+When to use", re.MULTILINE | re.IGNORECASE),
        'missing "When to use" section',
    ),
    (
        "When NOT to use",
        re.compile(r"^#{1,3}\s+When not to use", re.MULTILINE | re.IGNORECASE),
        'missing "When NOT to use" section',
    ),
    (
        "Process or Checklist",
        re.compile(r"^#{1,3}\s+(Process|Checklist)", re.MULTILINE | re.IGNORECASE),
        'missing "Process" or "Checklist" section',
    ),
    (
        "Output section",
        re.compile(r"^#{1,3}\s+Output", re.MULTILINE | re.IGNORECASE),
        'missing "Output" section (output format, output example, etc.)',
    ),
    (
        "Skill execution log",
        re.compile(r"skill-log\.md", re.MULTILINE),
        'missing skill execution log reference (must mention "skill-log.md")',
    ),
    (
        "Reference files",
        re.compile(r"^#{1,3}\s+Reference", re.MULTILINE | re.IGNORECASE),
        'missing "Reference files" section',
    ),
]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_frontmatter(content: str) -> bool:
    """Return True if file starts with --- YAML block containing name: and description:."""
    if not content.startswith("---"):
        return False
    end = content.find("\n---", 3)
    if end == -1:
        return False
    frontmatter = content[3:end]
    has_name = bool(re.search(r"^name\s*:", frontmatter, re.MULTILINE))
    has_description = bool(re.search(r"^description\s*:", frontmatter, re.MULTILINE))
    return has_name and has_description


def check_stale_references(content: str) -> list[str]:
    """Return list of stale reference names found in the content."""
    found = []
    for ref in STALE_REFERENCES:
        if ref in content:
            found.append(ref)
    return found


def scan_skill(path: Path) -> dict:
    """
    Scan a single SKILL.md file.
    Returns a dict with: path, name, missing_sections, stale_refs, status
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        return {
            "path": str(path),
            "name": path.parent.name,
            "missing_sections": [],
            "stale_refs": [],
            "status": "ERROR",
            "error": str(e),
        }

    missing = []

    # Check 1: frontmatter (special case)
    if not check_frontmatter(content):
        missing.append(SECTION_CHECKS[0][2])

    # Checks 2–8: regex-based
    for label, pattern, error_msg in SECTION_CHECKS[1:]:
        if not pattern.search(content):
            missing.append(f'"{label}"')

    stale_refs = check_stale_references(content)

    if missing:
        status = "FAIL"
    elif stale_refs:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "path": str(path),
        "name": path.parent.name,
        "missing_sections": missing,
        "stale_refs": stale_refs,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_skill_files(root: Path) -> list[Path]:
    """Recursively find all SKILL.md files under root."""
    return sorted(root.rglob("SKILL.md"))


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_text(results: list[dict]) -> tuple[str, int, int, int]:
    """Return formatted text output and counts."""
    passes = sum(1 for r in results if r["status"] == "PASS")
    fails = sum(1 for r in results if r["status"] == "FAIL")
    warns = sum(1 for r in results if r["status"] in ("WARN", "ERROR"))
    total = len(results)

    lines = []
    lines.append(f"Skill health check — {total} skills scanned")
    lines.append(SEPARATOR)

    for r in results:
        status = r["status"]
        name = r["name"]

        if status == "PASS":
            lines.append(f"PASS  {name:<40} all 8 sections present")
        elif status == "FAIL":
            missing_str = ", ".join(r["missing_sections"])
            lines.append(f"FAIL  {name:<40} missing: {missing_str}")
            if r["stale_refs"]:
                for ref in r["stale_refs"]:
                    lines.append(f"      {'':40} stale reference: '{ref}'")
        elif status == "WARN":
            for ref in r["stale_refs"]:
                lines.append(f"WARN  {name:<40} stale reference: '{ref}'")
        elif status == "ERROR":
            lines.append(f"ERROR {name:<40} {r.get('error', 'unknown error')}")

    lines.append("")
    lines.append(f"Results: {passes} PASS, {fails} FAIL, {warns} WARN")

    return "\n".join(lines), passes, fails, warns


def format_json(results: list[dict]) -> str:
    passes = sum(1 for r in results if r["status"] == "PASS")
    fails = sum(1 for r in results if r["status"] == "FAIL")
    warns = sum(1 for r in results if r["status"] in ("WARN", "ERROR"))
    output = {
        "total": len(results),
        "pass": passes,
        "fail": fails,
        "warn": warns,
        "results": results,
    }
    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Skill Health Checker — validates all SKILL.md files in the library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/skill_health.py
  python scripts/skill_health.py --path skills/phase2
  python scripts/skill_health.py --json
        """,
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Root directory to scan (default: skills/ relative to this script's repo root)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    # Determine repo root (two levels up from this script: scripts/ → repo root)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    if args.path:
        scan_root = Path(args.path).resolve()
    else:
        scan_root = repo_root / "skills"

    if not scan_root.exists():
        print(f"ERROR: Directory not found: {scan_root}", file=sys.stderr)
        sys.exit(2)

    skill_files = find_skill_files(scan_root)

    if not skill_files:
        print(f"No SKILL.md files found under: {scan_root}", file=sys.stderr)
        sys.exit(2)

    results = [scan_skill(f) for f in skill_files]

    if args.json:
        print(format_json(results))
    else:
        text, passes, fails, warns = format_text(results)
        print(text)

    any_fail = any(r["status"] == "FAIL" for r in results)
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
