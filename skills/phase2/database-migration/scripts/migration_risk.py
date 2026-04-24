"""
Database Migration Risk Analyzer

Reads a SQL migration file and reports risk signals including lock risks, idempotency,
missing rollback plans, data volume risks, column removal, and NOT NULL additions.

Usage:
    python migration_risk.py path/to/migration.sql
    python migration_risk.py path/to/migration.sql --json
    python migration_risk.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    status: str          # PASS | WARN | FAIL
    label: str           # short label
    message: str         # display message
    lines: list[tuple[int, str]] = field(default_factory=list)   # [(lineno, text)]
    fix: str | None = None


# Risk level weights: FAIL=2, WARN=1
RISK_WEIGHTS = {"PASS": 0, "WARN": 1, "FAIL": 2}

RISK_THRESHOLDS = {
    "LOW": (0, 1),
    "MEDIUM": (2, 4),
    "HIGH": (5, 999),
}


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_idempotency(lines: list[str]) -> Finding:
    """Check that CREATE/DROP statements use IF NOT EXISTS / IF EXISTS."""
    create_drop_pattern = re.compile(
        r"\b(CREATE|DROP)\s+(TABLE|INDEX|SEQUENCE|VIEW|FUNCTION|TRIGGER|TYPE)\b",
        re.IGNORECASE,
    )
    if_exists_pattern = re.compile(r"\bIF\s+(NOT\s+)?EXISTS\b", re.IGNORECASE)

    non_idempotent: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if create_drop_pattern.search(stripped) and not if_exists_pattern.search(stripped):
            non_idempotent.append((i, stripped))

    if non_idempotent:
        return Finding(
            status="WARN",
            label="Idempotency",
            message="CREATE/DROP without IF [NOT] EXISTS — migration is not safe to re-run",
            lines=non_idempotent,
            fix="Add IF NOT EXISTS to CREATE statements and IF EXISTS to DROP statements",
        )
    return Finding(status="PASS", label="Idempotency", message="IF NOT EXISTS / IF EXISTS used (idempotent)")


def check_alter_table_lock(lines: list[str]) -> Finding:
    """Check for ALTER TABLE statements that will acquire an ACCESS EXCLUSIVE lock."""
    alter_pattern = re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE)

    risky: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if alter_pattern.search(stripped):
            risky.append((i, stripped))

    if risky:
        return Finding(
            status="WARN",
            label="ALTER TABLE lock risk",
            message="ALTER TABLE acquires ACCESS EXCLUSIVE lock — blocks reads and writes for the migration duration",
            lines=risky,
            fix="Use expand-contract pattern: add nullable column first, then migrate data, then add constraint",
        )
    return Finding(status="PASS", label="ALTER TABLE lock risk", message="No blocking ALTER TABLE detected")


def check_index_lock(lines: list[str]) -> Finding:
    """Check for CREATE INDEX without CONCURRENTLY."""
    index_pattern = re.compile(r"\bCREATE\s+(UNIQUE\s+)?INDEX\b", re.IGNORECASE)
    concurrently_pattern = re.compile(r"\bCONCURRENTLY\b", re.IGNORECASE)

    risky: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if index_pattern.search(stripped) and not concurrently_pattern.search(stripped):
            risky.append((i, stripped))

    if risky:
        return Finding(
            status="WARN",
            label="Index creation lock",
            message="Index created without CONCURRENTLY — will lock table during creation",
            lines=risky,
            fix="Use CREATE INDEX CONCURRENTLY instead (cannot run inside a transaction block)",
        )
    return Finding(status="PASS", label="Index creation lock", message="No blocking index creation detected")


def check_rollback(content: str) -> Finding:
    """Check for presence of a Down/rollback section."""
    rollback_pattern = re.compile(
        r"--\s*(down|rollback|undo|revert|reverse)",
        re.IGNORECASE,
    )
    if rollback_pattern.search(content):
        return Finding(status="PASS", label="Rollback plan", message="Down/rollback section found")
    return Finding(
        status="WARN",
        label="Rollback plan",
        message="No Down/rollback section found — add a rollback plan comment",
        fix="Add a '-- Down' section with the inverse SQL to undo this migration",
    )


def check_full_table_update(lines: list[str]) -> Finding:
    """Check for UPDATE without WHERE clause (full table scan)."""
    update_pattern = re.compile(r"\bUPDATE\s+\w+\s+SET\b", re.IGNORECASE)
    where_pattern = re.compile(r"\bWHERE\b", re.IGNORECASE)

    # Collect multi-line UPDATE statements
    risky: list[tuple[int, str]] = []
    # Simple single-line check (good enough for most migrations)
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if update_pattern.search(stripped) and not where_pattern.search(stripped):
            # Check next 5 lines for WHERE
            context = " ".join(ln.strip() for ln in lines[i:min(i + 5, len(lines))])
            if not where_pattern.search(context):
                risky.append((i, stripped))

    if risky:
        return Finding(
            status="FAIL",
            label="Full-table UPDATE",
            message="UPDATE without WHERE — will scan and lock entire table",
            lines=risky,
            fix="Add a WHERE clause or batch the update. For large tables use batched updates with LIMIT.",
        )
    return Finding(status="PASS", label="Full-table UPDATE", message="No full-table UPDATE detected")


def check_column_removal(lines: list[str]) -> Finding:
    """Check for DROP COLUMN (irreversible)."""
    drop_column_pattern = re.compile(r"\bDROP\s+COLUMN\b", re.IGNORECASE)

    found: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if drop_column_pattern.search(stripped):
            found.append((i, stripped))

    if found:
        return Finding(
            status="FAIL",
            label="Column removal",
            message="DROP COLUMN detected — irreversible, high risk",
            lines=found,
            fix="Use expand-contract: stop writing to the column first, then remove after confirming no reads. "
                "Ensure column is not referenced by any application code before this migration runs.",
        )
    return Finding(status="PASS", label="Column removal", message="No column removal detected")


def check_not_null_without_default(lines: list[str]) -> Finding:
    """Check for NOT NULL column addition without a DEFAULT value."""
    # Pattern: ADD COLUMN ... NOT NULL (without DEFAULT)
    add_col_pattern = re.compile(
        r"\bADD\s+COLUMN\b.+\bNOT\s+NULL\b",
        re.IGNORECASE,
    )
    default_pattern = re.compile(r"\bDEFAULT\b", re.IGNORECASE)

    risky: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if add_col_pattern.search(stripped) and not default_pattern.search(stripped):
            risky.append((i, stripped))

    if risky:
        return Finding(
            status="FAIL",
            label="NOT NULL without DEFAULT",
            message="NOT NULL column added without DEFAULT — will fail on existing rows",
            lines=risky,
            fix="Add a DEFAULT value, or: (1) add nullable, (2) backfill, (3) add NOT NULL constraint separately",
        )
    return Finding(
        status="PASS",
        label="NOT NULL without DEFAULT",
        message="No NOT NULL column without DEFAULT detected",
    )


# ---------------------------------------------------------------------------
# Risk level computation
# ---------------------------------------------------------------------------

def compute_risk_level(findings: list[Finding]) -> tuple[str, str]:
    """Return (risk_level, recommendation)."""
    score = sum(RISK_WEIGHTS[f.status] for f in findings)
    fails = [f for f in findings if f.status == "FAIL"]
    warns = [f for f in findings if f.status == "WARN"]

    if score <= 1:
        level = "LOW"
        rec = "Migration looks safe. Review WARN items and proceed."
    elif score <= 4:
        level = "MEDIUM"
        issues = [f.label for f in warns + fails]
        rec = f"Address before deploying to production: {'; '.join(issues)}"
    else:
        level = "HIGH"
        issues = [f.label for f in fails]
        rec = f"Do not deploy without fixing FAIL items: {'; '.join(issues)}"

    return level, rec


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

SEPARATOR = "━" * 55


def print_text(filename: str, findings: list[Finding], risk_level: str, recommendation: str) -> None:
    print()
    print(f"Migration risk analysis: {filename}")
    print(SEPARATOR)

    for f in findings:
        icon = f.status
        print(f"{icon:<5} {f.message}")
        for lineno, text in f.lines:
            # Truncate long lines for display
            display = text if len(text) <= 70 else text[:67] + "..."
            print(f"        Line {lineno}: {display}")
        if f.fix and f.status != "PASS":
            print(f"        Fix: {f.fix}")

    print()
    print(f"Risk level: {risk_level}")
    print(f"Recommendation: {recommendation}")
    print()


def output_json(filename: str, findings: list[Finding], risk_level: str, recommendation: str) -> None:
    data = {
        "file": filename,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "findings": [
            {
                "status": f.status,
                "label": f.label,
                "message": f.message,
                "lines": [{"line": ln, "text": txt} for ln, txt in f.lines],
                "fix": f.fix,
            }
            for f in findings
        ],
        "summary": {
            "pass": sum(1 for f in findings if f.status == "PASS"),
            "warn": sum(1 for f in findings if f.status == "WARN"),
            "fail": sum(1 for f in findings if f.status == "FAIL"),
        },
    }
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Database Migration Risk Analyzer — checks SQL migration files for common risk patterns.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migration_risk.py migrations/add_device_partition_key.sql
  python migration_risk.py migrations/add_device_partition_key.sql --json
        """,
    )
    parser.add_argument("migration_file", help="Path to the SQL migration file to analyze")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    migration_path = Path(args.migration_file)
    if not migration_path.exists():
        print(f"ERROR: File not found: {migration_path}", file=sys.stderr)
        sys.exit(2)

    if migration_path.suffix.lower() not in (".sql", ".psql", ".pgsql", ""):
        print(f"WARNING: File does not have .sql extension: {migration_path}", file=sys.stderr)

    try:
        content = migration_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"ERROR reading file: {e}", file=sys.stderr)
        sys.exit(2)

    lines = content.splitlines()
    filename = migration_path.name

    # Run all checks
    findings = [
        check_idempotency(lines),
        check_alter_table_lock(lines),
        check_index_lock(lines),
        check_rollback(content),
        check_full_table_update(lines),
        check_column_removal(lines),
        check_not_null_without_default(lines),
    ]

    risk_level, recommendation = compute_risk_level(findings)

    if args.json:
        output_json(filename, findings, risk_level, recommendation)
    else:
        print_text(filename, findings, risk_level, recommendation)

    # Exit with non-zero if any FAIL
    any_fail = any(f.status == "FAIL" for f in findings)
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
