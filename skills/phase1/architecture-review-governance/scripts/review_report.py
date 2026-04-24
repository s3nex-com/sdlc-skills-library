#!/usr/bin/env python3
"""
review_report.py — Generate a formatted architecture review report from a JSON findings file.

Usage:
    python review_report.py --input findings.json --output review-report.md

Input JSON format:
    {
        "review": {
            "subject": "Telemetry Ingestion Service",
            "date": "2024-05-15",
            "reviewer": "Alice Chen, Lead Architect, Company A",
            "scope": "Full architecture review prior to M2 milestone"
        },
        "findings": [
            {
                "id": "F001",
                "title": "No circuit breaker on Kafka producer",
                "domain": "Integration safety",
                "severity": "Critical",
                "description": "The ingestion service calls the Kafka producer without a circuit breaker. If Kafka becomes slow, producer calls will block, exhausting the service's thread pool.",
                "recommendation": "Implement a circuit breaker using Resilience4j around all Kafka producer calls. Configure: failure rate threshold 50%, wait duration 30s.",
                "owner": "TL-B",
                "status": "Open"
            }
        ],
        "nfr_validation": [
            {
                "nfr_id": "NFR-001",
                "description": "p99 latency <= 500ms at 1000 concurrent connections",
                "validated": false,
                "evidence": "Load test not yet run",
                "status": "Pending"
            }
        ]
    }

Valid severity values: Critical, High, Medium, Low, Informational
Valid status values: Open, In Progress, Resolved, Accepted (risk accepted with documentation)
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from collections import defaultdict

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Informational"]
SEVERITY_EMOJI = {
    "Critical": "🔴",
    "High": "🟠",
    "Medium": "🟡",
    "Low": "🟢",
    "Informational": "ℹ️",
}


def determine_overall_status(findings: list[dict]) -> str:
    """Determine the overall review status based on open findings."""
    open_findings = [f for f in findings if f.get("status", "Open") not in ("Resolved", "Accepted")]
    severities = {f.get("severity", "Informational") for f in open_findings}

    if "Critical" in severities:
        return "❌ Fail — Critical findings must be resolved before proceeding"
    elif "High" in severities:
        return "⚠️ Conditional pass — High findings must be resolved before next milestone"
    elif "Medium" in severities:
        return "⚠️ Conditional pass — Medium findings should be addressed in next sprint"
    elif open_findings:
        return "✅ Pass with observations — Low/informational findings noted"
    else:
        return "✅ Pass — No open findings"


def generate_report(data: dict) -> str:
    review = data.get("review", {})
    findings = data.get("findings", [])
    nfr_validation = data.get("nfr_validation", [])

    # Sort findings by severity
    severity_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    sorted_findings = sorted(findings, key=lambda f: severity_rank.get(f.get("severity", "Informational"), 99))

    overall_status = determine_overall_status(findings)

    # Count by severity
    counts = defaultdict(int)
    for f in findings:
        counts[f.get("severity", "Informational")] += 1

    lines = []
    lines.append(f"# Architecture review report: {review.get('subject', '[Subject not specified]')}\n")
    lines.append(f"**Review date:** {review.get('date', date.today().isoformat())}")
    lines.append(f"**Reviewer:** {review.get('reviewer', '[Reviewer not specified]')}")
    lines.append(f"**Scope:** {review.get('scope', '[Scope not specified]')}")
    lines.append(f"**Report generated:** {date.today().isoformat()}\n")

    lines.append("---\n")
    lines.append("## Executive summary\n")
    lines.append(f"**Overall status:** {overall_status}\n")

    lines.append("**Finding summary:**\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for severity in SEVERITY_ORDER:
        if counts[severity] > 0:
            emoji = SEVERITY_EMOJI.get(severity, "")
            lines.append(f"| {emoji} {severity} | {counts[severity]} |")
    lines.append(f"| **Total** | **{len(findings)}** |")
    lines.append("")

    if not findings:
        lines.append("*No findings recorded.*\n")
    else:
        lines.append("---\n")
        lines.append("## Findings\n")

        # Group by domain
        by_domain = defaultdict(list)
        for f in sorted_findings:
            by_domain[f.get("domain", "Uncategorised")].append(f)

        for domain, domain_findings in sorted(by_domain.items()):
            lines.append(f"### {domain}\n")
            for f in domain_findings:
                severity = f.get("severity", "Informational")
                emoji = SEVERITY_EMOJI.get(severity, "")
                status = f.get("status", "Open")
                lines.append(f"#### {emoji} [{severity}] {f.get('id', '?')} — {f.get('title', 'Untitled')}")
                lines.append(f"**Status:** {status}")
                lines.append(f"**Owner:** {f.get('owner', 'Unassigned')}\n")
                lines.append(f"**Description:** {f.get('description', '')}\n")
                lines.append(f"**Recommendation:** {f.get('recommendation', '')}\n")

    if nfr_validation:
        lines.append("---\n")
        lines.append("## NFR validation status\n")
        lines.append("| NFR ID | Description | Status | Evidence |")
        lines.append("|--------|-------------|--------|---------|")
        for nfr in nfr_validation:
            status_icon = "✅" if nfr.get("validated") else "❌"
            lines.append(
                f"| {nfr.get('nfr_id', '?')} | {nfr.get('description', '')} | "
                f"{status_icon} {nfr.get('status', 'Unknown')} | {nfr.get('evidence', '')} |"
            )
        lines.append("")

    lines.append("---\n")
    lines.append("## Action items\n")
    open_findings = [f for f in sorted_findings if f.get("status", "Open") not in ("Resolved", "Accepted")]
    if open_findings:
        lines.append("| ID | Finding | Severity | Owner | Due |")
        lines.append("|----|---------|----------|-------|-----|")
        for f in open_findings:
            severity = f.get("severity", "?")
            emoji = SEVERITY_EMOJI.get(severity, "")
            lines.append(
                f"| {f.get('id', '?')} | {f.get('title', '')} | "
                f"{emoji} {severity} | {f.get('owner', 'Unassigned')} | [Set due date] |"
            )
    else:
        lines.append("*No open action items.*")

    lines.append("")
    lines.append("---")
    lines.append(f"\n*Report generated by review_report.py on {date.today().isoformat()}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a formatted architecture review report from a JSON findings file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--input", required=True, help="Path to the JSON findings file")
    parser.add_argument("--output", default=None, help="Output file path (default: print to stdout)")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    report = generate_report(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
