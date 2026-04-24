#!/usr/bin/env python3
"""
dep_budget.py — Architecture fitness: dependency budget checker.

Reads .fitness.yml for the dependency budget, then parses requirements.txt,
pyproject.toml, or package.json to count third-party dependencies. Reports
new deps not in approved-deps.txt and fails if over budget.

Usage:
    python dep_budget.py [--root PATH] [--config PATH]
    python dep_budget.py --help

Exit codes:
    0 — within budget
    1 — over budget
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"[dep_budget] No .fitness.yml found at {config_path} — skipping check")
        sys.exit(0)
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def load_approved(root: Path) -> Set[str]:
    approved_path = root / "approved-deps.txt"
    if not approved_path.exists():
        return set()
    lines = approved_path.read_text().splitlines()
    return {line.strip().lower() for line in lines if line.strip() and not line.startswith("#")}


def parse_requirements_txt(path: Path) -> List[str]:
    """Parse a requirements.txt file and return package names (no versions)."""
    deps = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r") or line.startswith("--"):
            continue
        # Strip version specifiers and extras: requests[security]>=2.0 -> requests
        name = re.split(r"[>=<!;\[\s]", line)[0].strip()
        if name:
            deps.append(name)
    return deps


def parse_pyproject_toml(path: Path) -> List[str]:
    """Parse pyproject.toml — supports both [project.dependencies] and [tool.poetry.dependencies]."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # backport
        except ImportError:
            # Fallback: naive line-based parsing
            deps = []
            in_deps = False
            for line in path.read_text().splitlines():
                stripped = line.strip()
                if stripped in ("[project.dependencies]", "[tool.poetry.dependencies]"):
                    in_deps = True
                    continue
                if stripped.startswith("[") and in_deps:
                    in_deps = False
                if in_deps and "=" in stripped and not stripped.startswith("#"):
                    name = re.split(r"[>=<!;\[\s=]", stripped)[0].strip().strip('"')
                    if name and name not in ("python", ""):
                        deps.append(name)
            return deps

    with open(path, "rb") as f:
        data = tomllib.load(f)

    deps = []
    # PEP 517 style
    project_deps = data.get("project", {}).get("dependencies", [])
    for dep in project_deps:
        name = re.split(r"[>=<!;\[\s]", dep)[0].strip()
        if name:
            deps.append(name)

    # Poetry style
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    for name in poetry_deps:
        if name.lower() != "python":
            deps.append(name)

    return deps


def parse_package_json(path: Path) -> List[str]:
    """Parse package.json and return dependency names (dependencies + devDependencies)."""
    import json
    data = json.loads(path.read_text())
    deps = list(data.get("dependencies", {}).keys())
    deps += list(data.get("devDependencies", {}).keys())
    return deps


def find_and_parse_deps(root: Path) -> Tuple[List[str], str]:
    """Find the first recognised dep file and parse it. Returns (dep_list, source_file)."""
    candidates = [
        (root / "requirements.txt", parse_requirements_txt),
        (root / "pyproject.toml", parse_pyproject_toml),
        (root / "package.json", parse_package_json),
    ]
    for path, parser in candidates:
        if path.exists():
            deps = parser(path)
            return deps, str(path.relative_to(root))
    return [], "none found"


def main():
    parser = argparse.ArgumentParser(
        description="Architecture fitness: check dependency count against budget."
    )
    parser.add_argument("--root", default=".", help="Repo root directory (default: current directory)")
    parser.add_argument("--config", default=".fitness.yml", help="Path to .fitness.yml (default: .fitness.yml)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path)

    budget = config.get("import_rules", {}).get("dependency_budget")
    if budget is None:
        print("[dep_budget] dependency_budget not set in .fitness.yml — skipping check")
        sys.exit(0)

    deps, source_file = find_and_parse_deps(root)
    dep_count = len(deps)

    print(f"[dep_budget] Reading {source_file} — {dep_count} dependencies found")

    approved = load_approved(root)
    unapproved = [d for d in deps if d.lower() not in approved] if approved else []

    exit_code = 0

    if dep_count <= budget:
        print(f"PASS  dependency_budget     {dep_count} deps found (budget: {budget})")
    else:
        over_by = dep_count - budget
        print(f"FAIL  dependency_budget     {dep_count} deps found, budget is {budget}")
        print(f"  Over by {over_by}: {', '.join(deps[-over_by:])}")
        if unapproved:
            print(f"  Not in approved-deps.txt: {', '.join(unapproved[:10])}")
        print("  Action: add to approved-deps.txt or remove if unused")
        exit_code = 1

    if approved and unapproved and exit_code == 0:
        # Within budget but unapproved deps exist — warn only
        print(f"WARN  unapproved_deps       {len(unapproved)} dep(s) not in approved-deps.txt")
        print(f"  {', '.join(unapproved[:10])}")
        print("  Action: add to approved-deps.txt to acknowledge")

    print(f"Exit: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
