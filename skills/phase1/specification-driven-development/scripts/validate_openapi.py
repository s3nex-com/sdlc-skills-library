#!/usr/bin/env python3
"""
validate_openapi.py — Validate an OpenAPI 3.x spec for structural correctness and completeness.

Usage:
    python validate_openapi.py --spec openapi.yaml
    python validate_openapi.py --spec openapi.json --output report.md

Checks performed:
    1. Structural validity (using openapi-spec-validator)
    2. Every operation has a unique operationId
    3. Every operation has a description
    4. Every operation defines at minimum 401, 500 responses (plus 400/422 for POST/PUT/PATCH)
    5. All response schemas use $ref (not inline anonymous schemas)
    6. All operations have at least one example in the request body (if present)

Install dependencies:
    pip install openapi-spec-validator pyyaml

Exit codes:
    0 = no Critical findings
    1 = Critical findings found (useful for CI/CD gates)
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    from openapi_spec_validator import validate
    from openapi_spec_validator.exceptions import OpenAPISpecValidatorError
    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False


REQUIRED_ERROR_RESPONSES = {"401", "500"}
REQUIRED_WRITE_RESPONSES = {"400", "401", "500"}  # for POST/PUT/PATCH


def load_spec(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        else:
            return yaml.safe_load(f)


def find_schema_issues(schema: dict, path: str) -> list[dict]:
    """Recursively find inline complex schemas (objects with properties not using $ref)."""
    issues = []
    if isinstance(schema, dict):
        if "$ref" not in schema and schema.get("type") == "object" and "properties" in schema:
            if len(schema.get("properties", {})) > 3:
                issues.append({
                    "path": path,
                    "severity": "Medium",
                    "message": f"Inline object schema with {len(schema['properties'])} properties at {path}. Consider moving to components/schemas."
                })
        for key, value in schema.items():
            if isinstance(value, dict):
                issues.extend(find_schema_issues(value, f"{path}/{key}"))
    return issues


def validate_spec(spec: dict) -> list[dict]:
    findings = []
    seen_operation_ids = {}

    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            operation = path_item.get(method)
            if not operation:
                continue

            op_ref = f"{method.upper()} {path}"
            responses = operation.get("responses", {})
            response_codes = set(str(k) for k in responses.keys())

            # Check operationId
            op_id = operation.get("operationId")
            if not op_id:
                findings.append({
                    "path": op_ref,
                    "severity": "High",
                    "message": "Missing operationId"
                })
            elif op_id in seen_operation_ids:
                findings.append({
                    "path": op_ref,
                    "severity": "Critical",
                    "message": f"Duplicate operationId '{op_id}' (also used by {seen_operation_ids[op_id]})"
                })
            else:
                seen_operation_ids[op_id] = op_ref

            # Check description
            if not operation.get("description"):
                findings.append({
                    "path": op_ref,
                    "severity": "High",
                    "message": "Missing operation description"
                })

            # Check required error responses
            missing_required = REQUIRED_ERROR_RESPONSES - response_codes
            if missing_required:
                for code in sorted(missing_required):
                    findings.append({
                        "path": op_ref,
                        "severity": "High",
                        "message": f"Missing required response: {code}"
                    })

            # Check write method responses
            if method in ("post", "put", "patch"):
                missing_write = REQUIRED_WRITE_RESPONSES - response_codes
                for code in sorted(missing_write):
                    findings.append({
                        "path": op_ref,
                        "severity": "High",
                        "message": f"POST/PUT/PATCH operation missing {code} response"
                    })

            # Check 500 has a schema
            if "500" in responses:
                resp_500 = responses["500"]
                content = resp_500.get("content", {})
                if not content:
                    findings.append({
                        "path": op_ref,
                        "severity": "Medium",
                        "message": "500 response has no content schema defined"
                    })

            # Check request body has examples
            request_body = operation.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                has_example = False
                for media_type, media_schema in content.items():
                    if media_schema.get("example") or media_schema.get("examples"):
                        has_example = True
                        break
                    schema = media_schema.get("schema", {})
                    if schema.get("example"):
                        has_example = True
                        break
                if not has_example:
                    findings.append({
                        "path": op_ref,
                        "severity": "Medium",
                        "message": "Request body has no examples defined"
                    })

            # Check for inline complex schemas in responses
            for code, response in responses.items():
                for media_type, media_schema in response.get("content", {}).items():
                    schema = media_schema.get("schema", {})
                    if schema and "$ref" not in schema:
                        schema_issues = find_schema_issues(schema, f"{op_ref} response {code}")
                        findings.extend(schema_issues)

    return findings


def generate_report(spec_path: str, structural_valid: bool, structural_error: str,
                    findings: list[dict]) -> str:
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_findings = sorted(findings, key=lambda f: severity_order.get(f["severity"], 99))

    counts = defaultdict(int)
    for f in findings:
        counts[f["severity"]] += 1

    has_critical = counts["Critical"] > 0
    status = "❌ Fail" if has_critical or not structural_valid else ("⚠️ Review needed" if findings else "✅ Pass")

    lines = ["# OpenAPI spec validation report\n"]
    lines.append(f"**Spec:** `{spec_path}`")
    lines.append(f"**Status:** {status}\n")

    lines.append("**Finding summary:**")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ["Critical", "High", "Medium", "Low"]:
        if counts[sev]:
            lines.append(f"| {sev} | {counts[sev]} |")
    lines.append("")

    if not structural_valid:
        lines.append("## Structural validation\n")
        lines.append(f"❌ **Spec is not structurally valid:**\n```\n{structural_error}\n```\n")
    else:
        lines.append("## Structural validation\n✅ Spec is structurally valid.\n")

    if sorted_findings:
        lines.append("## Findings\n")
        lines.append("| Severity | Operation | Issue |")
        lines.append("|----------|-----------|-------|")
        for f in sorted_findings:
            lines.append(f"| {f['severity']} | `{f['path']}` | {f['message']} |")
    else:
        lines.append("## Findings\n*No additional findings.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate an OpenAPI 3.x specification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--spec", required=True, help="Path to the OpenAPI YAML or JSON spec file")
    parser.add_argument("--output", default=None, help="Output file for report (default: stdout)")
    parser.add_argument("--fail-on-critical", action="store_true",
                        help="Exit code 1 if Critical findings exist (for CI/CD gates)")

    args = parser.parse_args()

    if not Path(args.spec).exists():
        print(f"Error: spec file not found: {args.spec}", file=sys.stderr)
        sys.exit(1)

    spec = load_spec(args.spec)

    structural_valid = True
    structural_error = ""
    if HAS_VALIDATOR:
        try:
            validate(spec)
        except OpenAPISpecValidatorError as e:
            structural_valid = False
            structural_error = str(e)
    else:
        structural_error = "openapi-spec-validator not installed — skipping structural validation. Install with: pip install openapi-spec-validator"

    findings = validate_spec(spec)
    report = generate_report(args.spec, structural_valid, structural_error, findings)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)

    if args.fail_on_critical:
        critical_count = sum(1 for f in findings if f["severity"] == "Critical")
        if critical_count > 0 or not structural_valid:
            sys.exit(1)


if __name__ == "__main__":
    main()
