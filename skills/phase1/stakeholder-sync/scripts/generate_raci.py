#!/usr/bin/env python3
"""
generate_raci.py — Generate a formatted RACI matrix from a JSON input file.

Usage:
    python generate_raci.py --input raci-input.json --output raci.md

Input JSON format:
    {
        "roles": [
            {"code": "VPE-A", "title": "VP Engineering", "company": "Company A"},
            {"code": "ARC-A", "title": "Lead Architect", "company": "Company A"},
            {"code": "EM-B", "title": "Engineering Manager", "company": "Company B"},
            {"code": "TL-B", "title": "Tech Lead", "company": "Company B"}
        ],
        "categories": [
            {
                "category": "Governance",
                "decisions": [
                    {
                        "id": 1,
                        "title": "Project charter approval",
                        "assignments": {
                            "VPE-A": "A",
                            "ARC-A": "C",
                            "EM-B": "C",
                            "TL-B": "I"
                        },
                        "notes": "Both VPEs must sign"
                    }
                ]
            }
        ]
    }

Valid assignment values: R, A, C, I (or empty string for no assignment)
Each decision row must have exactly one "A" assignment.
"""

import argparse
import json
import sys
from pathlib import Path


def validate_raci(data: dict) -> list[str]:
    """Validate the input data. Returns a list of error messages."""
    errors = []
    role_codes = {r["code"] for r in data.get("roles", [])}

    for category in data.get("categories", []):
        cat_name = category.get("category", "Unknown")
        for decision in category.get("decisions", []):
            title = decision.get("title", "Unknown")
            assignments = decision.get("assignments", {})

            # Check all roles are known
            for code in assignments:
                if code not in role_codes:
                    errors.append(f"Unknown role code '{code}' in decision: {title}")

            # Check exactly one A per row
            accountable = [k for k, v in assignments.items() if v == "A"]
            if len(accountable) == 0:
                errors.append(f"[{cat_name}] Decision '{title}' has no Accountable (A) assignment")
            elif len(accountable) > 1:
                errors.append(f"[{cat_name}] Decision '{title}' has multiple Accountable (A) assignments: {accountable}")

            # Check valid values
            for code, val in assignments.items():
                if val not in ("R", "A", "C", "I", ""):
                    errors.append(f"[{cat_name}] Decision '{title}', role '{code}' has invalid value '{val}' (must be R, A, C, or I)")

    return errors


def generate_raci_markdown(data: dict) -> str:
    roles = data["roles"]
    role_codes = [r["code"] for r in roles]

    lines = []
    lines.append("# RACI matrix\n")
    lines.append("**R = Responsible** | **A = Accountable** | **C = Consulted** | **I = Informed**\n")

    # Roles legend
    lines.append("## Roles\n")
    lines.append("| Code | Title | Company |")
    lines.append("|------|-------|---------|")
    for r in roles:
        lines.append(f"| {r['code']} | {r['title']} | {r['company']} |")
    lines.append("")

    # Build table header
    header_cells = ["#", "Decision type"] + role_codes + ["Notes"]
    separator_cells = ["---", "---"] + ["---"] * len(role_codes) + ["---"]

    lines.append("## Decision matrix\n")

    for category in data["categories"]:
        lines.append(f"| **{category['category']}** | | " + " | " * len(role_codes) + " |")
        lines.append("| " + " | ".join(header_cells) + " |")
        lines.append("| " + " | ".join(separator_cells) + " |")

        for decision in category["decisions"]:
            assignments = decision.get("assignments", {})
            cells = [
                str(decision.get("id", "")),
                decision.get("title", ""),
            ]
            for code in role_codes:
                cells.append(assignments.get(code, ""))
            cells.append(decision.get("notes", ""))
            lines.append("| " + " | ".join(cells) + " |")

        lines.append("")

    lines.append("---")
    lines.append("\n## Validation checklist\n")
    lines.append("- [ ] Every row has exactly one **A**")
    lines.append("- [ ] No row has only **I** entries")
    lines.append("- [ ] Both companies are represented in every significant decision category")
    lines.append("- [ ] Matrix reviewed by Engineering Managers from both companies")
    lines.append("- [ ] Linked from project charter")
    lines.append(f"\n**Last updated:** {__import__('datetime').date.today().isoformat()}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a RACI matrix Markdown table from a JSON input file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--input", required=True, help="Path to the JSON input file")
    parser.add_argument("--output", default=None, help="Output file path (default: print to stdout)")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation checks")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON in {args.input}: {e}", file=sys.stderr)
            sys.exit(1)

    if not args.no_validate:
        errors = validate_raci(data)
        if errors:
            print("Validation errors found:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            print("\nFix these errors or use --no-validate to skip validation.", file=sys.stderr)
            sys.exit(1)

    output = generate_raci_markdown(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"RACI matrix written to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
