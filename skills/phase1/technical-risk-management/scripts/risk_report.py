#!/usr/bin/env python3
"""
risk_report.py — Generate a formatted risk summary report from a risk register CSV or JSON.

Usage:
    python risk_report.py --input risk-register.json --output risk-report.md
    python risk_report.py --input risk-register.csv --output risk-report.md

JSON format:
    [
        {
            "id": "RISK-001",
            "title": "Kafka throughput does not meet 50k events/sec target",
            "category": "Architecture",
            "probability": 3,
            "impact": 5,
            "status": "Being mitigated",
            "mitigation": "Performance spike in Sprint 3",
            "contingency": "Evaluate Confluent Cloud throughput tiers",
            "owner": "TL-B",
            "early_warning": "Producer send latency >50ms at 10k events/sec",
            "review_date": "Sprint 3 review"
        }
    ]

CSV format (header row required):
    id,title,category,probability,impact,status,mitigation,contingency,owner,early_warning,review_date

Valid status values: Identified, Being mitigated, Resolved, Accepted, Escalated
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

PRIORITY_BANDS = [
    (20, 25, "🔴 Critical"),
    (12, 19, "🟠 High"),
    (6, 11, "🟡 Medium"),
    (1, 5, "🟢 Low"),
]

CATEGORY_ORDER = [
    "Architecture", "Delivery", "Dependency",
    "Security", "Operational", "Contractual", "Organisational"
]


def get_priority(score: int) -> str:
    for low, high, label in PRIORITY_BANDS:
        if low <= score <= high:
            return label
    return "🟢 Low"


def load_risks_json(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_risks_csv(path: str) -> list[dict]:
    risks = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["probability"] = int(row.get("probability", 1))
            row["impact"] = int(row.get("impact", 1))
            risks.append(dict(row))
    return risks


def generate_report(risks: list[dict], title: str = "Risk summary report") -> str:
    # Calculate composite scores
    for r in risks:
        r["score"] = r.get("probability", 1) * r.get("impact", 1)
        r["priority"] = get_priority(r["score"])

    active_risks = [r for r in risks if r.get("status", "") not in ("Resolved", "Accepted")]
    resolved_risks = [r for r in risks if r.get("status", "") == "Resolved"]
    accepted_risks = [r for r in risks if r.get("status", "") == "Accepted"]

    sorted_active = sorted(active_risks, key=lambda r: -r["score"])

    lines = []
    lines.append(f"# {title}")
    lines.append(f"\n**Generated:** {date.today().isoformat()}")
    lines.append(f"**Total risks:** {len(risks)}")
    lines.append(f"**Active risks:** {len(active_risks)}")
    lines.append(f"**Resolved:** {len(resolved_risks)} | **Accepted:** {len(accepted_risks)}\n")

    lines.append("---\n")
    lines.append("## Executive summary\n")

    # Count by priority band (active only)
    band_counts = defaultdict(int)
    for r in active_risks:
        band_counts[r["priority"]] += 1

    escalated = [r for r in active_risks if r.get("status") == "Escalated"]
    if escalated:
        lines.append(f"⚠️ **{len(escalated)} risk(s) currently ESCALATED — immediate attention required.**\n")

    lines.append("**Active risks by priority:**\n")
    lines.append("| Priority | Count |")
    lines.append("|----------|-------|")
    for _, _, label in PRIORITY_BANDS:
        count = band_counts.get(label, 0)
        if count > 0:
            lines.append(f"| {label} | {count} |")
    lines.append(f"| **Total active** | **{len(active_risks)}** |")
    lines.append("")

    lines.append("---\n")
    lines.append("## Top 5 priority risks\n")

    top5 = sorted_active[:5]
    if top5:
        lines.append("| Rank | ID | Title | Priority | Status | Owner |")
        lines.append("|------|----|-------|----------|--------|-------|")
        for i, r in enumerate(top5, 1):
            lines.append(
                f"| {i} | {r.get('id', '?')} | {r.get('title', '')} | "
                f"{r['priority']} | {r.get('status', '')} | {r.get('owner', '')} |"
            )
    else:
        lines.append("*No active risks.*")
    lines.append("")

    lines.append("---\n")
    lines.append("## All active risks\n")

    # Group by category
    by_category = defaultdict(list)
    for r in sorted_active:
        by_category[r.get("category", "Uncategorised")].append(r)

    for category in CATEGORY_ORDER + ["Uncategorised"]:
        cat_risks = by_category.get(category, [])
        if not cat_risks:
            continue
        lines.append(f"### {category}\n")
        for r in cat_risks:
            score = r["score"]
            lines.append(
                f"**{r.get('id', '?')} — {r.get('title', '')}** "
                f"({r['priority']}, score {score})"
            )
            lines.append(f"- **Status:** {r.get('status', 'Unknown')}")
            lines.append(f"- **P×I:** {r.get('probability', '?')} × {r.get('impact', '?')} = {score}")
            lines.append(f"- **Mitigation:** {r.get('mitigation', 'None defined')}")
            lines.append(f"- **Owner:** {r.get('owner', 'Unassigned')}")
            lines.append(f"- **Early warning:** {r.get('early_warning', 'Not defined')}")
            lines.append(f"- **Review:** {r.get('review_date', 'Not scheduled')}\n")

    if resolved_risks or accepted_risks:
        lines.append("---\n")
        lines.append("## Closed risks\n")
        closed = resolved_risks + accepted_risks
        lines.append("| ID | Title | Status | Category |")
        lines.append("|----|-------|--------|---------|")
        for r in closed:
            lines.append(
                f"| {r.get('id', '?')} | {r.get('title', '')} | "
                f"{r.get('status', '')} | {r.get('category', '')} |"
            )
        lines.append("")

    lines.append("---")
    lines.append(f"\n*Report generated by risk_report.py on {date.today().isoformat()}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a risk summary report from a risk register.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--input", required=True, help="Path to risk register JSON or CSV file")
    parser.add_argument("--output", default=None, help="Output file path (default: print to stdout)")
    parser.add_argument("--title", default="Risk summary report", help="Report title")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    suffix = input_path.suffix.lower()
    if suffix == ".json":
        risks = load_risks_json(args.input)
    elif suffix == ".csv":
        risks = load_risks_csv(args.input)
    else:
        print(f"Error: unsupported file format '{suffix}'. Use .json or .csv", file=sys.stderr)
        sys.exit(1)

    report = generate_report(risks, args.title)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
