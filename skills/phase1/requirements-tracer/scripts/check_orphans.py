#!/usr/bin/env python3
"""
check_orphans.py — Detect orphaned requirements and orphaned code/test modules.

An "orphaned requirement" is a requirement with no linked code or test in the manifest.
An "orphaned module" is a code module or test with no linked requirement.

Usage:
    python check_orphans.py --requirements requirements.csv --manifest manifest.json

Requirements CSV format (columns: id, title, status, priority):
    REQ-001,Register a new device via API,Implemented,High
    REQ-002,Reject registration with missing fields,Implemented,High
    REQ-003,Rate limit device registration,Planned,Medium

Manifest JSON format (maps module/test names to arrays of requirement IDs):
    {
        "code_modules": {
            "services/device-registry/api/devices.py": ["REQ-001", "REQ-002"],
            "services/device-registry/middleware/rate_limiter.py": ["REQ-003"],
            "services/device-registry/utils/helpers.py": []
        },
        "tests": {
            "tests/unit/test_devices.py": ["REQ-001", "REQ-002"],
            "tests/unit/test_rate_limiter.py": ["REQ-003"],
            "tests/integration/test_device_flow.py": ["REQ-001"]
        }
    }

Modules with an empty requirements array [] are flagged as orphaned.
Requirements listed in the manifest that don't exist in the CSV are flagged as unknown.
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def load_requirements(csv_path: str) -> dict:
    """Load requirements from CSV. Returns dict: {req_id: {title, status, priority}}"""
    requirements = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Support both with-header and headerless formats
        if reader.fieldnames and reader.fieldnames[0].lower() in ("id", "req_id", "requirement_id"):
            for row in reader:
                req_id = row.get("id") or row.get("req_id") or row.get("requirement_id", "").strip()
                if req_id:
                    requirements[req_id] = {
                        "title": row.get("title", "").strip(),
                        "status": row.get("status", "Unknown").strip(),
                        "priority": row.get("priority", "Unknown").strip(),
                    }
        else:
            # Headerless: id,title,status,priority
            f.seek(0)
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 1 and row[0].strip():
                    req_id = row[0].strip()
                    requirements[req_id] = {
                        "title": row[1].strip() if len(row) > 1 else "",
                        "status": row[2].strip() if len(row) > 2 else "Unknown",
                        "priority": row[3].strip() if len(row) > 3 else "Unknown",
                    }
    return requirements


def load_manifest(json_path: str) -> dict:
    """Load manifest from JSON. Returns {"code_modules": {...}, "tests": {...}}"""
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def find_orphans(requirements: dict, manifest: dict) -> dict:
    """
    Returns:
        {
            "orphaned_requirements": [...],  # reqs with no linked module or test
            "orphaned_modules": [...],       # code modules with no linked req
            "orphaned_tests": [...],         # tests with no linked req
            "unknown_req_references": [...], # req IDs in manifest not in requirements CSV
        }
    """
    code_modules = manifest.get("code_modules", {})
    tests = manifest.get("tests", {})

    # Build set of all requirement IDs referenced in the manifest
    all_referenced_req_ids: set[str] = set()
    for req_ids in code_modules.values():
        all_referenced_req_ids.update(req_ids)
    for req_ids in tests.values():
        all_referenced_req_ids.update(req_ids)

    # Find orphaned requirements (in CSV but not referenced in any module/test)
    orphaned_requirements = []
    for req_id, meta in requirements.items():
        if req_id not in all_referenced_req_ids:
            orphaned_requirements.append({
                "id": req_id,
                "title": meta["title"],
                "status": meta["status"],
                "priority": meta["priority"],
            })

    # Find orphaned code modules (in manifest with empty or no req IDs)
    orphaned_modules = []
    for module, req_ids in code_modules.items():
        if not req_ids:
            orphaned_modules.append(module)

    # Find orphaned tests
    orphaned_tests = []
    for test, req_ids in tests.items():
        if not req_ids:
            orphaned_tests.append(test)

    # Find unknown requirement references (referenced in manifest but not in CSV)
    unknown_refs = sorted(all_referenced_req_ids - set(requirements.keys()))

    return {
        "orphaned_requirements": orphaned_requirements,
        "orphaned_modules": orphaned_modules,
        "orphaned_tests": orphaned_tests,
        "unknown_req_references": unknown_refs,
    }


def format_report(requirements: dict, manifest: dict, orphans: dict) -> str:
    lines = []
    lines.append("# Orphan detection report\n")

    total_reqs = len(requirements)
    total_modules = len(manifest.get("code_modules", {}))
    total_tests = len(manifest.get("tests", {}))

    lines.append(f"**Requirements:** {total_reqs}")
    lines.append(f"**Code modules:** {total_modules}")
    lines.append(f"**Test files:** {total_tests}\n")

    # Summary
    has_issues = any([
        orphans["orphaned_requirements"],
        orphans["orphaned_modules"],
        orphans["orphaned_tests"],
        orphans["unknown_req_references"],
    ])

    if has_issues:
        lines.append("**Status:** ⚠️  Issues found — review required\n")
    else:
        lines.append("**Status:** ✅ No orphans found\n")

    lines.append("---\n")

    # Orphaned requirements
    orph_reqs = orphans["orphaned_requirements"]
    lines.append(f"## Orphaned requirements ({len(orph_reqs)})\n")
    if orph_reqs:
        lines.append("These requirements have no linked code module or test. Either implementation has not started (acceptable if status is Planned) or they were forgotten.\n")
        lines.append("| Req ID | Title | Status | Priority |")
        lines.append("|--------|-------|--------|---------|")
        for r in orph_reqs:
            status_icon = "🟡" if r["status"] == "Planned" else "🔴"
            lines.append(f"| {r['id']} | {r['title']} | {status_icon} {r['status']} | {r['priority']} |")
    else:
        lines.append("*None — all requirements have linked implementation and/or tests.*")
    lines.append("")

    # Orphaned code modules
    orph_mods = orphans["orphaned_modules"]
    lines.append(f"## Orphaned code modules ({len(orph_mods)})\n")
    if orph_mods:
        lines.append("These modules have no linked requirement. Either they implement out-of-scope functionality (scope creep) or the manifest has not been updated. Action required: link to existing requirement or remove.\n")
        for mod in orph_mods:
            lines.append(f"- `{mod}`")
    else:
        lines.append("*None — all code modules are linked to requirements.*")
    lines.append("")

    # Orphaned tests
    orph_tests = orphans["orphaned_tests"]
    lines.append(f"## Orphaned tests ({len(orph_tests)})\n")
    if orph_tests:
        lines.append("These test files have no linked requirement. Each test should verify a specific requirement.\n")
        for test in orph_tests:
            lines.append(f"- `{test}`")
    else:
        lines.append("*None — all test files are linked to requirements.*")
    lines.append("")

    # Unknown references
    unknown = orphans["unknown_req_references"]
    lines.append(f"## Unknown requirement references ({len(unknown)})\n")
    if unknown:
        lines.append("These requirement IDs appear in the manifest but are not in the requirements CSV. Check for typos or requirements that have been removed.\n")
        for ref in unknown:
            lines.append(f"- `{ref}`")
    else:
        lines.append("*None — all manifest requirement references exist in the requirements CSV.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Detect orphaned requirements and orphaned code/test modules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--requirements", required=True, help="Path to requirements CSV file")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON file")
    parser.add_argument("--output", default=None, help="Output file for the report (default: print to stdout)")
    parser.add_argument("--fail-on-orphans", action="store_true",
                        help="Exit with code 1 if any orphans are found (useful in CI/CD)")

    args = parser.parse_args()

    for path in [args.requirements, args.manifest]:
        if not Path(path).exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    requirements = load_requirements(args.requirements)
    manifest = load_manifest(args.manifest)
    orphans = find_orphans(requirements, manifest)
    report = format_report(requirements, manifest, orphans)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)

    if args.fail_on_orphans:
        has_issues = any([
            orphans["orphaned_requirements"],
            orphans["orphaned_modules"],
            orphans["orphaned_tests"],
            orphans["unknown_req_references"],
        ])
        if has_issues:
            sys.exit(1)


if __name__ == "__main__":
    main()
