"""
sdlc-skills-library Skill Usage Analytics

Parses docs/skill-log.md and reports usage analytics including most-used skills,
BLOCKED/PARTIAL rates, pipeline completion times, unused skills, and outcome distribution.

Log format parsed:
    [YYYY-MM-DD] skill-name | outcome: OK|BLOCKED|PARTIAL | next: skill-name or "none" | note: brief description

Usage:
    python scripts/skill_usage.py                         # full analytics report
    python scripts/skill_usage.py --since 2026-01-01      # filter by date
    python scripts/skill_usage.py --json                  # JSON output
    python scripts/skill_usage.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# All skills in the library (used for "never used" detection)
# ---------------------------------------------------------------------------

def _discover_all_skills() -> list[str]:
    here = Path(__file__).resolve().parent
    skills_dir = here.parent / "skills"
    if not skills_dir.exists():
        return []
    return sorted(p.parent.name for p in skills_dir.rglob("SKILL.md"))

ALL_SKILLS = _discover_all_skills()

SEPARATOR = "━" * 50

# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------

LOG_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2})\]\s+"        # [date]
    r"([\w-]+)"                             # skill-name
    r"(?:\s*\|\s*outcome:\s*(OK|BLOCKED|PARTIAL))?"   # optional outcome
    r"(?:\s*\|\s*next:\s*([^|]+?))?"       # optional next
    r"(?:\s*\|\s*note:\s*(.+?))?$",        # optional note
    re.IGNORECASE,
)

# Also support the legacy format: [YYYY-MM-DD] skill-name — description
LEGACY_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2})\]\s+([\w-]+)\s+[—-]\s+(.+)$"
)


def parse_date(date_str: str) -> date | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_log(log_path: Path, since: date | None = None) -> list[dict]:
    """Parse skill-log.md and return list of entry dicts."""
    entries = []
    for line_num, raw_line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        m = LOG_PATTERN.match(line)
        if m:
            entry_date = parse_date(m.group(1))
            if entry_date is None:
                continue
            if since and entry_date < since:
                continue
            entries.append({
                "date": entry_date,
                "skill": m.group(2).strip(),
                "outcome": (m.group(3) or "OK").upper(),
                "next": (m.group(4) or "none").strip(),
                "note": (m.group(5) or "").strip(),
                "line": line_num,
            })
            continue

        # Try legacy format
        m2 = LEGACY_PATTERN.match(line)
        if m2:
            entry_date = parse_date(m2.group(1))
            if entry_date is None:
                continue
            if since and entry_date < since:
                continue
            entries.append({
                "date": entry_date,
                "skill": m2.group(2).strip(),
                "outcome": "OK",
                "next": "none",
                "note": m2.group(3).strip(),
                "line": line_num,
            })

    return entries


# ---------------------------------------------------------------------------
# Analytics computations
# ---------------------------------------------------------------------------

def compute_analytics(entries: list[dict]) -> dict:
    if not entries:
        return {}

    today = date.today()
    month_start = today.replace(day=1)

    # Per-skill stats
    skill_counts: dict[str, int] = defaultdict(int)
    skill_outcomes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    used_skills: set[str] = set()

    # Per-feature pipeline timing (group by date proximity — naive: same skill-chain run)
    # We approximate pipeline runs as consecutive entries ending at pr-merge-orchestrator or release-readiness
    pipeline_durations: list[int] = []  # days

    for entry in entries:
        skill = entry["skill"]
        outcome = entry["outcome"]
        skill_counts[skill] += 1
        skill_outcomes[skill][outcome] += 1
        used_skills.add(skill)

    # Top 10 this month
    month_entries = [e for e in entries if e["date"] >= month_start]
    month_counts: dict[str, int] = defaultdict(int)
    for e in month_entries:
        month_counts[e["skill"]] += 1
    top_month = sorted(month_counts.items(), key=lambda x: -x[1])[:10]

    # BLOCKED/PARTIAL rates
    blocked_partial_rates = {}
    for skill, outcomes in skill_outcomes.items():
        total = sum(outcomes.values())
        bad = outcomes.get("BLOCKED", 0) + outcomes.get("PARTIAL", 0)
        if total > 0:
            blocked_partial_rates[skill] = {
                "rate": round(bad / total * 100, 1),
                "blocked": outcomes.get("BLOCKED", 0),
                "partial": outcomes.get("PARTIAL", 0),
                "total": total,
            }
    high_blocked = {k: v for k, v in blocked_partial_rates.items() if v["rate"] >= 20}
    high_blocked_sorted = sorted(high_blocked.items(), key=lambda x: -x[1]["rate"])

    # Pipeline duration: pair each prd-creator with the next unmatched completion.
    # Uses a list (not a date-keyed dict) so multiple runs starting on the same
    # calendar day are tracked independently.
    pipeline_starts: list[date] = []
    matched_starts: set[int] = set()
    for e in entries:
        skill = e["skill"]
        if skill == "prd-creator":
            pipeline_starts.append(e["date"])
        elif skill in ("pr-merge-orchestrator", "release-readiness"):
            for i, start_date in enumerate(pipeline_starts):
                if i not in matched_starts:
                    matched_starts.add(i)
                    duration = (e["date"] - start_date).days
                    if duration >= 0:
                        pipeline_durations.append(duration)
                    break

    avg_pipeline_days = None
    if pipeline_durations:
        avg_pipeline_days = round(sum(pipeline_durations) / len(pipeline_durations), 1)

    # Never used
    never_used = [s for s in ALL_SKILLS if s not in used_skills]

    # Overall outcome distribution
    total_entries = len(entries)
    outcome_counts: dict[str, int] = defaultdict(int)
    for e in entries:
        outcome_counts[e["outcome"]] += 1
    outcome_pct = {
        k: round(v / total_entries * 100, 1)
        for k, v in outcome_counts.items()
    } if total_entries > 0 else {}

    return {
        "total_entries": total_entries,
        "top_skills_this_month": top_month,
        "high_blocked_partial_rate": high_blocked_sorted,
        "avg_pipeline_days": avg_pipeline_days,
        "never_used": never_used,
        "outcome_distribution": {
            "counts": dict(outcome_counts),
            "percentages": outcome_pct,
        },
        "date_range": {
            "earliest": min(e["date"] for e in entries).isoformat(),
            "latest": max(e["date"] for e in entries).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def print_text_report(analytics: dict, since: date | None) -> None:
    print()
    print("sdlc-skills-library Skill Usage Analytics")
    if since:
        print(f"  Filtered since: {since.isoformat()}")
    print(SEPARATOR)

    if not analytics:
        print("No entries found in the specified date range.")
        return

    dr = analytics["date_range"]
    print(f"  Log range: {dr['earliest']} to {dr['latest']}")
    print(f"  Total skill firings: {analytics['total_entries']}")
    print()

    print("Most used skills this month (top 10):")
    top = analytics["top_skills_this_month"]
    if top:
        for skill, count in top:
            print(f"  {skill:<45} {count} firing{'s' if count != 1 else ''}")
    else:
        print("  No entries this month.")
    print()

    print("Skills with high BLOCKED/PARTIAL rate (>= 20%):")
    high = analytics["high_blocked_partial_rate"]
    if high:
        for skill, stats in high:
            print(f"  {skill:<45} {stats['rate']}%  "
                  f"(B:{stats['blocked']} P:{stats['partial']} / {stats['total']} total)")
    else:
        print("  None — all skills are performing well.")
    print()

    avg = analytics["avg_pipeline_days"]
    if avg is not None:
        print(f"Average pipeline completion time: {avg} days")
    else:
        print("Average pipeline completion time: not enough data (need prd-creator → pr-merge-orchestrator pairs)")
    print()

    never = analytics["never_used"]
    print(f"Skills never used ({len(never)}):")
    if never:
        for s in never:
            print(f"  {s}")
    else:
        print("  All skills have been used at least once.")
    print()

    dist = analytics["outcome_distribution"]
    counts = dist["counts"]
    pcts = dist["percentages"]
    print("Outcome distribution:")
    for outcome in ["OK", "PARTIAL", "BLOCKED"]:
        c = counts.get(outcome, 0)
        p = pcts.get(outcome, 0.0)
        print(f"  {outcome:<10} {c:>4} entries  ({p}%)")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Skill Usage Analytics — parses docs/skill-log.md and reports usage stats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/skill_usage.py
  python scripts/skill_usage.py --since 2026-01-01
  python scripts/skill_usage.py --json
        """,
    )
    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Filter entries on or after this date",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--log",
        default=None,
        help="Path to skill-log.md (default: docs/skill-log.md relative to repo root)",
    )
    args = parser.parse_args()

    since_date: date | None = None
    if args.since:
        since_date = parse_date(args.since)
        if since_date is None:
            print(f"ERROR: Invalid date format for --since: {args.since}. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(2)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    if args.log:
        log_path = Path(args.log).resolve()
    else:
        log_path = repo_root / "docs" / "skill-log.md"

    if not log_path.exists():
        msg = (
            f"Skill log not found at: {log_path}\n"
            "The skill log is created on the first pipeline run.\n"
            "Run the sdlc-orchestrator to start a pipeline and generate log entries.\n"
            "\nExpected log format:\n"
            "  [YYYY-MM-DD] skill-name | outcome: OK|BLOCKED|PARTIAL | next: skill-name | note: description"
        )
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print(msg)
        sys.exit(0)

    try:
        entries = parse_log(log_path, since=since_date)
    except OSError as e:
        print(f"ERROR reading log: {e}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        msg = "No log entries found" + (f" since {since_date.isoformat()}" if since_date else "") + "."
        if args.json:
            print(json.dumps({"message": msg, "entries": 0}))
        else:
            print(msg)
        sys.exit(0)

    analytics = compute_analytics(entries)

    if args.json:
        # Convert date objects for JSON serialisation
        print(json.dumps(analytics, indent=2, default=str))
    else:
        print_text_report(analytics, since_date)


if __name__ == "__main__":
    main()
