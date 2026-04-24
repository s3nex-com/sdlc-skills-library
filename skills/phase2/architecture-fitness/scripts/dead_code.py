#!/usr/bin/env python3
"""
dead_code.py — Architecture fitness: dead module detector.

Reads .fitness.yml for dead_module_days threshold, reads a coverage report
(coverage.xml or .coverage), and uses git log to find the last commit date
per file. Flags modules that have BOTH zero test coverage AND no git commits
in N days.

Does NOT fail the build (always exits 0). Reports as WARN only — dead code
is informational. Act on it when it suits you.

Usage:
    python dead_code.py [--root PATH] [--config PATH]
    python dead_code.py --help

Exit codes:
    0 — always (dead code detection is informational)
"""

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional, Set

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"[dead_code] No .fitness.yml found at {config_path} — skipping check")
        sys.exit(0)
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def find_zero_coverage_files(root: Path) -> Set[str]:
    """
    Return set of relative file paths with zero line coverage.
    Reads coverage.xml if present, otherwise skips coverage check.
    """
    xml_path = root / "coverage.xml"
    if not xml_path.exists():
        # Try .coverage (binary — can't parse without coverage.py installed)
        try:
            result = subprocess.run(
                ["python", "-m", "coverage", "xml", "-o", str(xml_path)],
                capture_output=True, text=True, cwd=root
            )
            if result.returncode != 0 or not xml_path.exists():
                print("[dead_code] No coverage.xml found and could not generate one — skipping coverage check")
                return set()
        except FileNotFoundError:
            print("[dead_code] No coverage.xml and coverage.py not available — skipping coverage check")
            return set()

    zero_coverage = set()
    try:
        tree = ET.parse(xml_path)
        root_elem = tree.getroot()
        for cls in root_elem.iter("class"):
            filename = cls.get("filename", "")
            lines = cls.findall(".//line")
            if not lines:
                zero_coverage.add(filename)
                continue
            hits = sum(int(line.get("hits", 0)) for line in lines)
            if hits == 0:
                zero_coverage.add(filename)
    except ET.ParseError as e:
        print(f"[dead_code] Could not parse coverage.xml: {e}")

    return zero_coverage


def get_last_commit_dates(root: Path, files: Set[str]) -> Dict[str, Optional[date]]:
    """
    For each file path, return the date of its last git commit.
    Returns None for files not tracked in git.
    """
    dates = {}
    if not files:
        return dates

    for filepath in files:
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci", "--", filepath],
                capture_output=True, text=True, cwd=root
            )
            output = result.stdout.strip()
            if output:
                # Format: "2025-11-14 10:23:45 +0000"
                date_str = output.split(" ")[0]
                dates[filepath] = date.fromisoformat(date_str)
            else:
                dates[filepath] = None
        except Exception:
            dates[filepath] = None

    return dates


def normalize_path(filepath: str, root: Path) -> str:
    """Normalise a coverage.xml path to be relative to repo root."""
    p = Path(filepath)
    if p.is_absolute():
        try:
            return str(p.relative_to(root))
        except ValueError:
            return filepath
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Architecture fitness: detect dead modules (zero coverage + no recent commits)."
    )
    parser.add_argument("--root", default=".", help="Repo root directory (default: current directory)")
    parser.add_argument("--config", default=".fitness.yml", help="Path to .fitness.yml (default: .fitness.yml)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path)

    threshold_days = config.get("quality", {}).get("dead_module_days", 90)
    cutoff = date.today() - timedelta(days=threshold_days)

    zero_cov = find_zero_coverage_files(root)
    if not zero_cov:
        print("[dead_code] No zero-coverage modules found (or no coverage data available)")
        print("PASS  dead_modules          no candidates to check")
        print("Exit: 0")
        sys.exit(0)

    normalized = {normalize_path(f, root): f for f in zero_cov}
    print(f"[dead_code] Reading coverage.xml — {len(zero_cov)} modules with zero coverage")
    print(f"[dead_code] Cross-referencing git log (threshold: {threshold_days} days)...")

    commit_dates = get_last_commit_dates(root, set(normalized.keys()))

    dead = []
    for norm_path, orig_path in normalized.items():
        last_commit = commit_dates.get(norm_path)
        if last_commit is None:
            # Not in git — treat as potentially dead but don't flag without date
            continue
        if last_commit < cutoff:
            days_ago = (date.today() - last_commit).days
            dead.append((norm_path, days_ago))

    if not dead:
        print(f"PASS  dead_modules          0 modules with zero coverage and no commits in {threshold_days}+ days")
    else:
        print(f"WARN  dead_modules          {len(dead)} module(s) with zero coverage and no commits in {threshold_days}+ days")
        for filepath, days_ago in sorted(dead, key=lambda x: -x[1]):
            print(f"  {filepath}   (last commit: {days_ago} days ago)")
        print("  Action: delete, add tests, or document why these are intentionally inactive")

    # Always exit 0 — dead code is informational, never blocks a PR
    print("Exit: 0  (dead code is informational only — build not blocked)")
    sys.exit(0)


if __name__ == "__main__":
    main()
