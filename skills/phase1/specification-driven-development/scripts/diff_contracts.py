#!/usr/bin/env python3
"""
diff_contracts.py — Compare two OpenAPI spec versions and categorise all changes.

Usage:
    python diff_contracts.py --old v1.0.0.yaml --new v1.1.0.yaml
    python diff_contracts.py --old v1.0.0.yaml --new v1.1.0.yaml --output diff-report.md

Change categories:
    Breaking     — Removed endpoints, removed required fields, changed types, changed
                   status codes, removed response fields. Consumers MUST update.
    Non-breaking — Changed descriptions, added optional fields to requests,
                   relaxed constraints. Consumers may benefit but are not broken.
    Additive     — New endpoints, new optional response fields, new optional
                   request parameters. Consumers can adopt at their own pace.

Install dependencies:
    pip install pyyaml

Exit codes:
    0 = no breaking changes
    1 = breaking changes found (useful for CI/CD gates)
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_spec(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        return yaml.safe_load(f)


def get_required_fields(schema: dict) -> set[str]:
    return set(schema.get("required", []))


def get_properties(schema: dict) -> dict:
    return schema.get("properties", {})


def get_operations(spec: dict) -> dict[str, dict]:
    """Returns {f"{method} {path}": operation_dict}"""
    ops = {}
    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            op = path_item.get(method)
            if op:
                ops[f"{method.upper()} {path}"] = op
    return ops


def get_response_codes(operation: dict) -> set[str]:
    return set(str(k) for k in operation.get("responses", {}).keys())


def diff_schemas(old_schema: dict, new_schema: dict, context: str) -> list[dict]:
    """Compare two schemas and return a list of change findings."""
    changes = []

    if not old_schema and not new_schema:
        return changes

    if old_schema and not new_schema:
        changes.append({
            "type": "Breaking",
            "context": context,
            "description": "Schema was removed entirely",
        })
        return changes

    if not old_schema and new_schema:
        changes.append({
            "type": "Additive",
            "context": context,
            "description": "Schema was added",
        })
        return changes

    old_type = old_schema.get("type")
    new_type = new_schema.get("type")
    if old_type and new_type and old_type != new_type:
        changes.append({
            "type": "Breaking",
            "context": context,
            "description": f"Field type changed from '{old_type}' to '{new_type}'"
        })

    old_required = get_required_fields(old_schema)
    new_required = get_required_fields(new_schema)

    # Fields that became required (breaking for requests, non-breaking for responses)
    newly_required = new_required - old_required
    for field in newly_required:
        is_request = "request" in context.lower() or "body" in context.lower()
        changes.append({
            "type": "Breaking" if is_request else "Non-breaking",
            "context": context,
            "description": f"Field '{field}' became required {'(consumers must now provide this field)' if is_request else '(response now always includes this field)'}"
        })

    # Fields that became optional (non-breaking for requests, potentially breaking for responses)
    newly_optional = old_required - new_required
    for field in newly_optional:
        changes.append({
            "type": "Non-breaking",
            "context": context,
            "description": f"Field '{field}' is now optional (was required)"
        })

    # Removed fields
    old_props = get_properties(old_schema)
    new_props = get_properties(new_schema)

    for field in old_props:
        if field not in new_props:
            changes.append({
                "type": "Breaking",
                "context": context,
                "description": f"Field '{field}' was removed"
            })

    # Added fields
    for field in new_props:
        if field not in old_props:
            required = field in new_required
            changes.append({
                "type": "Breaking" if required else "Additive",
                "context": context,
                "description": f"Field '{field}' was added ({'required' if required else 'optional'})"
            })

    return changes


def diff_specs(old_spec: dict, new_spec: dict) -> list[dict]:
    changes = []

    old_ops = get_operations(old_spec)
    new_ops = get_operations(new_spec)

    # Removed endpoints (Breaking)
    for op_key in old_ops:
        if op_key not in new_ops:
            changes.append({
                "type": "Breaking",
                "context": op_key,
                "description": "Endpoint removed"
            })

    # Added endpoints (Additive)
    for op_key in new_ops:
        if op_key not in old_ops:
            changes.append({
                "type": "Additive",
                "context": op_key,
                "description": "New endpoint added"
            })

    # Compare existing operations
    for op_key in old_ops:
        if op_key not in new_ops:
            continue

        old_op = old_ops[op_key]
        new_op = new_ops[op_key]

        # Response code changes
        old_codes = get_response_codes(old_op)
        new_codes = get_response_codes(new_op)

        removed_codes = old_codes - new_codes
        for code in removed_codes:
            changes.append({
                "type": "Breaking",
                "context": op_key,
                "description": f"Response code {code} removed"
            })

        added_codes = new_codes - old_codes
        for code in added_codes:
            changes.append({
                "type": "Additive",
                "context": op_key,
                "description": f"New response code {code} added"
            })

        # Request body schema changes
        old_body = old_op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        new_body = new_op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        if old_body or new_body:
            schema_changes = diff_schemas(old_body, new_body, f"{op_key} request body")
            changes.extend(schema_changes)

        # Response schema changes (200/201/202)
        for code in ("200", "201", "202"):
            old_resp = old_op.get("responses", {}).get(code, {})
            new_resp = new_op.get("responses", {}).get(code, {})
            old_schema = old_resp.get("content", {}).get("application/json", {}).get("schema", {})
            new_schema = new_resp.get("content", {}).get("application/json", {}).get("schema", {})
            if old_schema or new_schema:
                schema_changes = diff_schemas(old_schema, new_schema, f"{op_key} response {code}")
                changes.extend(schema_changes)

    return changes


def generate_report(old_path: str, new_path: str, changes: list[dict]) -> str:
    breaking = [c for c in changes if c["type"] == "Breaking"]
    non_breaking = [c for c in changes if c["type"] == "Non-breaking"]
    additive = [c for c in changes if c["type"] == "Additive"]

    status = "❌ Breaking changes detected" if breaking else (
        "⚠️ Non-breaking changes" if non_breaking or additive else "✅ No changes detected"
    )

    lines = ["# Contract diff report\n"]
    lines.append(f"**Old:** `{old_path}`")
    lines.append(f"**New:** `{new_path}`")
    lines.append(f"**Status:** {status}\n")
    lines.append(f"**Summary:** {len(breaking)} breaking | {len(non_breaking)} non-breaking | {len(additive)} additive\n")
    lines.append("---\n")

    if breaking:
        lines.append(f"## ❌ Breaking changes ({len(breaking)})\n")
        lines.append("Consumers MUST update their implementations before the new version is deployed.\n")
        lines.append("| Operation | Change |")
        lines.append("|-----------|--------|")
        for c in breaking:
            lines.append(f"| `{c['context']}` | {c['description']} |")
        lines.append("")

    if non_breaking:
        lines.append(f"## ⚠️ Non-breaking changes ({len(non_breaking)})\n")
        lines.append("Consumers are not broken but may want to take advantage of these changes.\n")
        lines.append("| Operation | Change |")
        lines.append("|-----------|--------|")
        for c in non_breaking:
            lines.append(f"| `{c['context']}` | {c['description']} |")
        lines.append("")

    if additive:
        lines.append(f"## ✅ Additive changes ({len(additive)})\n")
        lines.append("New functionality. Existing consumers are unaffected.\n")
        lines.append("| Operation | Change |")
        lines.append("|-----------|--------|")
        for c in additive:
            lines.append(f"| `{c['context']}` | {c['description']} |")

    if not changes:
        lines.append("*No changes detected between the two spec versions.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two OpenAPI spec versions and categorise changes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--old", required=True, help="Path to the old (baseline) OpenAPI spec")
    parser.add_argument("--new", required=True, help="Path to the new OpenAPI spec")
    parser.add_argument("--output", default=None, help="Output file for the report (default: stdout)")
    parser.add_argument("--fail-on-breaking", action="store_true",
                        help="Exit code 1 if breaking changes are found (for CI/CD gates)")

    args = parser.parse_args()

    for path in [args.old, args.new]:
        if not Path(path).exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    old_spec = load_spec(args.old)
    new_spec = load_spec(args.new)
    changes = diff_specs(old_spec, new_spec)
    report = generate_report(args.old, args.new, changes)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)

    if args.fail_on_breaking:
        breaking = [c for c in changes if c["type"] == "Breaking"]
        if breaking:
            sys.exit(1)


if __name__ == "__main__":
    main()
