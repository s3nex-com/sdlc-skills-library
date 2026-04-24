"""
Chaos Experiment Schedule Generator

Generates a quarterly chaos experiment schedule given a list of services.
Experiments are spread across the quarter (not all in week 1) and follow
hypothesis-driven chaos principles with steady-state definitions.

Usage:
    python chaos_schedule.py --services web-api,telemetry-ingest,device-registry --output chaos-schedule-Q2-2026.md
    python chaos_schedule.py --services web-api,telemetry-ingest --quarter Q3 --year 2026
    python chaos_schedule.py          # interactive mode — prompts for services
    python chaos_schedule.py --help
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Standard experiment templates
# ---------------------------------------------------------------------------

EXPERIMENT_TEMPLATES = [
    {
        "name": "Dependency outage",
        "description": "Simulate one service's dependency going down",
        "duration": "30 minutes",
        "hypothesis_template": "{target} gracefully queues or degrades when {dependency} is unavailable",
        "steady_state_template": "{target} p95 < 200ms, error rate < 1%",
        "abort_if": "error rate > 5% or data loss detected",
        "requires_dependency": True,
    },
    {
        "name": "Database slow query",
        "description": "Inject 2-second delay on all DB queries",
        "duration": "20 minutes",
        "hypothesis_template": "{target} returns errors gracefully and surfaces DB latency in metrics",
        "steady_state_template": "{target} p95 < 500ms, DB query timeout alerts fire correctly",
        "abort_if": "p99 > 30s or cascading errors spread to dependent services",
        "requires_dependency": False,
    },
    {
        "name": "Pod/instance failure",
        "description": "Kill one instance and verify auto-recovery",
        "duration": "15 minutes",
        "hypothesis_template": "{target} auto-recovers within 60 seconds with no requests dropped",
        "steady_state_template": "{target} healthy instances >= 2, p95 < 300ms",
        "abort_if": "service does not recover within 5 minutes or error rate > 10%",
        "requires_dependency": False,
    },
    {
        "name": "Message queue partition",
        "description": "Simulate Kafka/queue partition or lag (inject 60-second consumer lag)",
        "duration": "45 minutes",
        "hypothesis_template": "{target} processes backlogged events after lag clears, no data loss",
        "steady_state_template": "{target} consumer lag < 1000 messages, processing rate > 90% of normal",
        "abort_if": "consumer lag grows unbounded or messages are dropped/deduplicated incorrectly",
        "requires_dependency": False,
    },
    {
        "name": "Network partition",
        "description": "Isolate one service from the others via firewall rules",
        "duration": "25 minutes",
        "hypothesis_template": "{target} returns circuit-breaker fallback responses within 5 seconds",
        "steady_state_template": "{target} circuit breaker opens within 30s, fallback response rate = 100%",
        "abort_if": "service hangs indefinitely or other services cascade-fail",
        "requires_dependency": True,
    },
]


# ---------------------------------------------------------------------------
# Quarter date utilities
# ---------------------------------------------------------------------------

QUARTER_STARTS = {
    "Q1": (1, 1),
    "Q2": (4, 1),
    "Q3": (7, 1),
    "Q4": (10, 1),
}

QUARTER_ENDS = {
    "Q1": (3, 31),
    "Q2": (6, 30),
    "Q3": (9, 30),
    "Q4": (12, 31),
}


def get_quarter_from_date(d: date) -> tuple[str, int]:
    month = d.month
    if month <= 3:
        return "Q1", d.year
    elif month <= 6:
        return "Q2", d.year
    elif month <= 9:
        return "Q3", d.year
    else:
        return "Q4", d.year


def quarter_start_date(quarter: str, year: int) -> date:
    m, day = QUARTER_STARTS[quarter]
    return date(year, m, day)


def quarter_end_date(quarter: str, year: int) -> date:
    m, day = QUARTER_ENDS[quarter]
    return date(year, m, day)


def next_monday_on_or_after(d: date) -> date:
    """Return the next Monday on or after date d."""
    days_ahead = (7 - d.weekday()) % 7  # Monday = 0
    return d + timedelta(days=days_ahead)


def spread_experiment_dates(quarter: str, year: int, count: int) -> list[date]:
    """
    Spread `count` experiments across a quarter, starting in week 3
    (to allow prerequisites completion) and not bunching in week 1.
    """
    q_start = quarter_start_date(quarter, year)
    q_end = quarter_end_date(quarter, year)
    q_duration = (q_end - q_start).days

    # Start no earlier than week 3 (day 14)
    # End no later than 2 weeks before quarter end (allow time for retrospective)
    available_start = q_start + timedelta(days=14)
    available_end = q_end - timedelta(days=14)
    available_days = (available_end - available_start).days

    if available_days <= 0:
        available_days = q_duration

    # Space experiments evenly
    dates = []
    if count == 1:
        offsets = [available_days // 2]
    else:
        step = available_days / (count + 1)
        offsets = [int(step * (i + 1)) for i in range(count)]

    for offset in offsets:
        d = available_start + timedelta(days=offset)
        # Move to next Monday for clean scheduling
        d = next_monday_on_or_after(d)
        # Clamp to available window
        if d > available_end:
            d = available_end
        dates.append(d)

    return dates


def week_number_in_quarter(d: date, quarter: str, year: int) -> int:
    """Return the week number within the quarter (week 1 = first week)."""
    q_start = quarter_start_date(quarter, year)
    delta = (d - q_start).days
    return (delta // 7) + 1


# ---------------------------------------------------------------------------
# Experiment assignment
# ---------------------------------------------------------------------------

def assign_experiments(services: list[str], quarter: str, year: int) -> list[dict]:
    """
    Create one experiment per template (5 templates), assign services as targets,
    spread across the quarter.
    """
    num_experiments = len(EXPERIMENT_TEMPLATES)
    dates = spread_experiment_dates(quarter, year, num_experiments)

    experiments = []
    for i, (template, exp_date) in enumerate(zip(EXPERIMENT_TEMPLATES, dates)):
        # Rotate services as targets
        target = services[i % len(services)]

        # Find a dependency (next service in list) for templates that need one
        if template["requires_dependency"] and len(services) > 1:
            dependency = services[(i + 1) % len(services)]
        else:
            dependency = services[(i + 1) % len(services)] if len(services) > 1 else "external-dependency"

        hypothesis = template["hypothesis_template"].format(
            target=target,
            dependency=dependency,
        )
        steady_state = template["steady_state_template"].format(
            target=target,
            dependency=dependency,
        )

        week_num = week_number_in_quarter(exp_date, quarter, year)

        experiments.append({
            "name": template["name"],
            "description": template["description"],
            "date": exp_date,
            "week": week_num,
            "target": target,
            "dependency": dependency,
            "duration": template["duration"],
            "hypothesis": hypothesis,
            "steady_state": steady_state,
            "abort_if": template["abort_if"],
        })

    return experiments


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_markdown(services: list[str], quarter: str, year: int, experiments: list[dict]) -> str:
    today = date.today().isoformat()
    services_str = ", ".join(services)

    lines = []
    lines.append(f"# Chaos Engineering Schedule — {quarter} {year}")
    lines.append("")
    lines.append(f"Generated: {today} | Services: {services_str}")
    lines.append("")

    # Prerequisites
    lines.append("## Prerequisites (complete before first experiment)")
    lines.append("")
    for svc in services:
        lines.append(f"- [ ] Define steady state for **{svc}** (p95 latency, error rate, throughput)")
    lines.append("- [ ] Set up abort conditions and monitoring alerts for each service")
    lines.append("- [ ] Confirm rollback procedures are documented and tested")
    lines.append("- [ ] Verify experiment tooling is in place (chaos mesh, tc, iptables, or equivalent)")
    lines.append("- [ ] Brief the team — everyone should know the experiment schedule")
    lines.append("- [ ] Ensure observability (metrics, logs, traces) is working for all target services")
    lines.append("")

    # Experiments
    lines.append("## Experiments")
    lines.append("")

    for exp in experiments:
        date_str = exp["date"].strftime("%Y-%m-%d")
        lines.append(f"### Week {exp['week']} — {date_str}")
        lines.append("")
        lines.append(f"**Experiment:** {exp['name']}")
        lines.append(f"**Target:** {exp['target']}")
        if exp["description"]:
            lines.append(f"**What:** {exp['description']}")
        lines.append(f"**Duration:** {exp['duration']}")
        lines.append(f"**Hypothesis:** {exp['hypothesis']}")
        lines.append(f"**Steady state:** {exp['steady_state']}")
        lines.append(f"**Abort if:** {exp['abort_if']}")
        lines.append("")
        lines.append("**Runbook:**")
        lines.append("- [ ] Verify steady state before starting")
        lines.append(f"- [ ] Inject fault: _{exp['description']}_")
        lines.append(f"- [ ] Monitor for {exp['duration']}")
        lines.append("- [ ] Restore normal conditions")
        lines.append("- [ ] Verify steady state restored")
        lines.append("- [ ] Document findings in postmortem (even if experiment passes)")
        lines.append("")

    # Review cadence
    lines.append("## Review cadence")
    lines.append("")
    lines.append("After each experiment:")
    lines.append("- Write a short findings note (5 minutes max) — what happened, did hypothesis hold?")
    lines.append("- If hypothesis failed: create a follow-up ticket, schedule a postmortem")
    lines.append("- If hypothesis held: document as evidence of system resilience")
    lines.append("")
    lines.append("End of quarter:")
    lines.append("- Retrospective: which experiments found real issues? Which were wasted effort?")
    lines.append("- Update steady-state definitions based on observed real traffic")
    lines.append("- Plan next quarter experiments based on findings and new risk areas")
    lines.append("")
    lines.append("---")
    lines.append("_Generated by skills/phase3/chaos-engineering/scripts/chaos_schedule.py_")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def prompt_for_services() -> list[str]:
    """Interactively prompt for service names."""
    print()
    print("Chaos Schedule Generator — Interactive Mode")
    print("Enter service names one per line. Empty line to finish.")
    print()
    services = []
    while True:
        try:
            raw = input(f"Service {len(services) + 1} (or Enter to finish): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)
        if not raw:
            if not services:
                print("At least one service is required.")
                continue
            break
        # Sanitise: lowercase, replace spaces with hyphens
        name = raw.lower().replace(" ", "-")
        services.append(name)
    return services


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chaos Experiment Schedule Generator — creates a quarterly experiment schedule.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chaos_schedule.py --services web-api,telemetry-ingest,device-registry
  python chaos_schedule.py --services web-api,telemetry-ingest --quarter Q3 --year 2026
  python chaos_schedule.py --services web-api --output chaos-Q2-2026.md
  python chaos_schedule.py    # interactive mode
        """,
    )
    parser.add_argument(
        "--services",
        help="Comma-separated list of service names (e.g. web-api,telemetry-ingest,device-registry)",
    )
    parser.add_argument(
        "--quarter",
        choices=["Q1", "Q2", "Q3", "Q4"],
        default=None,
        help="Quarter to schedule (default: current quarter)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year for the schedule (default: current year)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output filename (default: chaos-schedule-{quarter}-{year}.md in current directory)",
    )
    args = parser.parse_args()

    # Determine quarter and year
    today = date.today()
    current_quarter, current_year = get_quarter_from_date(today)

    quarter = args.quarter or current_quarter
    year = args.year or current_year

    # Get services
    if args.services:
        services = [s.strip().lower().replace(" ", "-") for s in args.services.split(",") if s.strip()]
        if not services:
            print("ERROR: --services must contain at least one service name.", file=sys.stderr)
            sys.exit(2)
    else:
        services = prompt_for_services()

    # Generate experiments
    experiments = assign_experiments(services, quarter, year)

    # Generate markdown
    markdown = generate_markdown(services, quarter, year, experiments)

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(f"chaos-schedule-{quarter}-{year}.md")

    try:
        out_path.write_text(markdown, encoding="utf-8")
    except OSError as e:
        print(f"ERROR writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Generated: {out_path}")
    print(f"  Quarter:      {quarter} {year}")
    print(f"  Services:     {', '.join(services)}")
    print(f"  Experiments:  {len(experiments)}")
    for exp in experiments:
        date_str = exp["date"].strftime("%Y-%m-%d")
        print(f"    Week {exp['week']:>2} ({date_str}) — {exp['name']} → {exp['target']}")
    print()
    print(f"Next step: complete prerequisites before the first experiment on {experiments[0]['date'].strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
