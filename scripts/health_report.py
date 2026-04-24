"""
sdlc-skills-library Project Health Dashboard

Generates docs/health-report.md by reading available data sources:
  - docs/skill-log.md     — skill usage frequency and BLOCKED rates
  - docs/sdlc-status.md   — current pipeline state
  - git log               — deployment frequency (git tags matching v*)
  - coverage.xml / .coverage — test coverage if present
  - requirements.txt / package.json — dependency counts

Usage:
    python scripts/health_report.py            # generate docs/health-report.md
    python scripts/health_report.py --stdout   # print to stdout instead of file
    python scripts/health_report.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TODAY = date.today().isoformat()
THIRTY_DAYS_AGO = (date.today() - timedelta(days=30)).isoformat()

def _discover_all_skills() -> list[str]:
    here = Path(__file__).resolve().parent
    skills_dir = here.parent / "skills"
    if not skills_dir.exists():
        return []
    return sorted(p.parent.name for p in skills_dir.rglob("SKILL.md"))

ALL_SKILLS = _discover_all_skills()

LOG_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2})\]\s+([\w-]+)"
    r"(?:\s*\|\s*outcome:\s*(OK|BLOCKED|PARTIAL))?",
    re.IGNORECASE,
)
LEGACY_PATTERN = re.compile(r"^\[(\d{4}-\d{2}-\d{2})\]\s+([\w-]+)\s+[—-]")


# ---------------------------------------------------------------------------
# Data source readers
# ---------------------------------------------------------------------------

def read_skill_log(log_path: Path) -> dict:
    """Parse skill-log.md for usage stats."""
    result = {
        "available": False,
        "total_firings": 0,
        "outcome_counts": {},
        "skill_counts_30d": {},
        "high_blocked": [],
        "never_used": [],
    }
    if not log_path.exists():
        return result

    result["available"] = True
    today = date.today()
    cutoff = today - timedelta(days=30)

    skill_counts_30d: dict[str, int] = defaultdict(int)
    skill_outcomes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    outcome_totals: dict[str, int] = defaultdict(int)
    total = 0
    used_skills: set[str] = set()

    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        m = LOG_PATTERN.match(line)
        if not m:
            m2 = LEGACY_PATTERN.match(line)
            if m2:
                entry_date_str, skill = m2.group(1), m2.group(2)
                outcome = "OK"
            else:
                continue
        else:
            entry_date_str, skill, outcome = m.group(1), m.group(2), m.group(3) or "OK"

        try:
            entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        outcome = outcome.upper()
        total += 1
        used_skills.add(skill)
        skill_outcomes[skill][outcome] += 1
        outcome_totals[outcome] += 1

        if entry_date >= cutoff:
            skill_counts_30d[skill] += 1

    # Top 10 by usage last 30 days
    top_10 = sorted(skill_counts_30d.items(), key=lambda x: -x[1])[:10]

    # High blocked/partial rate
    high_blocked = []
    for skill, outcomes in skill_outcomes.items():
        t = sum(outcomes.values())
        bad = outcomes.get("BLOCKED", 0) + outcomes.get("PARTIAL", 0)
        if t > 0 and (bad / t) >= 0.15:
            rate = round(bad / t * 100)
            high_blocked.append(f"{skill} ({rate}%)")
    high_blocked.sort()

    never_used = [s for s in ALL_SKILLS if s not in used_skills]

    result.update({
        "total_firings": total,
        "outcome_counts": dict(outcome_totals),
        "skill_counts_30d": dict(top_10),
        "high_blocked": high_blocked,
        "never_used": never_used,
    })
    return result


def read_sdlc_status(status_path: Path) -> dict:
    """Read current pipeline stage from sdlc-status.md."""
    result = {"available": False, "status_line": None}
    if not status_path.exists():
        return result
    result["available"] = True
    content = status_path.read_text(encoding="utf-8")
    # Look for a line like "Stage N — Name (Status)"
    m = re.search(r"(Stage\s+\d+[^|\n]+)", content, re.IGNORECASE)
    if m:
        result["status_line"] = m.group(1).strip()
    else:
        # First non-empty, non-heading line
        for line in content.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                result["status_line"] = stripped
                break
    return result


def read_git_deployments(repo_root: Path) -> dict:
    """Count git tags matching v* in last 30 days."""
    result = {"available": False, "count_30d": 0, "last_tag": None, "last_date": None}
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return result

    try:
        # List tags with creation date
        raw = subprocess.check_output(
            ["git", "tag", "-l", "v*", "--sort=-creatordate",
             "--format=%(creatordate:short) %(refname:short)"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return result

    result["available"] = True
    cutoff = date.today() - timedelta(days=30)
    count = 0
    for line in raw.strip().splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        tag_date_str, tag_name = parts
        try:
            tag_date = datetime.strptime(tag_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if result["last_tag"] is None:
            result["last_tag"] = tag_name
            result["last_date"] = tag_date_str
        if tag_date >= cutoff:
            count += 1

    result["count_30d"] = count
    return result


def read_coverage(repo_root: Path) -> dict:
    """Try to read test coverage from coverage.xml or .coverage."""
    result = {"available": False, "percentage": None, "source": None}

    # Try coverage.xml first (standard output from pytest-cov)
    for pattern in ["coverage.xml", "**/coverage.xml"]:
        matches = list(repo_root.glob(pattern))
        if matches:
            xml_path = matches[0]
            try:
                tree = ET.parse(str(xml_path))
                root_elem = tree.getroot()
                line_rate = root_elem.get("line-rate")
                if line_rate is not None:
                    result["available"] = True
                    result["percentage"] = round(float(line_rate) * 100, 1)
                    result["source"] = str(xml_path.relative_to(repo_root))
                    return result
            except (ET.ParseError, ValueError, OSError):
                pass

    # Try .coverage (binary — just detect presence, can't read without coverage.py)
    if (repo_root / ".coverage").exists():
        result["available"] = True
        result["percentage"] = None
        result["source"] = ".coverage (binary — run 'coverage report' for percentage)"

    return result


def read_dependencies(repo_root: Path) -> dict:
    """Count dependencies from requirements.txt or package.json files."""
    result = {"available": False, "files": []}

    # requirements.txt
    for req_path in repo_root.glob("**/requirements*.txt"):
        if ".git" in req_path.parts:
            continue
        try:
            lines = [ln.strip() for ln in req_path.read_text(encoding="utf-8").splitlines()
                     if ln.strip() and not ln.startswith("#")]
            result["files"].append({
                "path": str(req_path.relative_to(repo_root)),
                "count": len(lines),
                "type": "python",
            })
            result["available"] = True
        except OSError:
            pass

    # package.json
    for pkg_path in repo_root.glob("**/package.json"):
        if ".git" in pkg_path.parts or "node_modules" in pkg_path.parts:
            continue
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            deps = len(data.get("dependencies", {})) + len(data.get("devDependencies", {}))
            result["files"].append({
                "path": str(pkg_path.relative_to(repo_root)),
                "count": deps,
                "type": "node",
            })
            result["available"] = True
        except (OSError, json.JSONDecodeError):
            pass

    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    skill_log: dict,
    sdlc_status: dict,
    git_info: dict,
    coverage: dict,
    deps: dict,
    today_str: str,
) -> str:
    lines = []
    lines.append(f"# Project Health Report — {today_str}")
    lines.append("")

    # Delivery section
    lines.append("## Delivery")

    if git_info["available"]:
        count = git_info["count_30d"]
        lines.append(f"- Deployment frequency: {count} release{'s' if count != 1 else ''} in last 30 days (via git tags)")
        if git_info["last_tag"]:
            lines.append(f"- Last deployment: {git_info['last_date']} ({git_info['last_tag']})")
        else:
            lines.append("- Last deployment: none found")
    else:
        lines.append("- Deployment frequency: not available (no git repository detected)")

    if sdlc_status["available"] and sdlc_status["status_line"]:
        lines.append(f"- Pipeline status: {sdlc_status['status_line']}")
    elif sdlc_status["available"]:
        lines.append("- Pipeline status: sdlc-status.md found but status unreadable")
    else:
        lines.append("- Pipeline status: not available (no docs/sdlc-status.md found)")

    lines.append("")

    # Quality section
    lines.append("## Quality")

    if coverage["available"] and coverage["percentage"] is not None:
        lines.append(f"- Test coverage: {coverage['percentage']}% (from {coverage['source']})")
    elif coverage["available"]:
        lines.append(f"- Test coverage: detected ({coverage['source']})")
    else:
        lines.append("- Test coverage: not available (no coverage.xml found)")

    if skill_log["available"] and skill_log["high_blocked"]:
        hb = ", ".join(skill_log["high_blocked"][:5])
        lines.append(f"- Skills with high BLOCKED rate: {hb}")
    elif skill_log["available"]:
        lines.append("- Skills with high BLOCKED rate: none")
    else:
        lines.append("- Skills with high BLOCKED rate: not available (no skill-log.md)")

    if deps["available"]:
        for dep_file in deps["files"][:3]:
            lines.append(f"- Dependencies ({dep_file['type']}): {dep_file['count']} in {dep_file['path']}")
    else:
        lines.append("- Dependencies: not available (no requirements.txt or package.json found)")

    lines.append("")

    # Activity section
    lines.append("## Activity")

    if skill_log["available"]:
        top = skill_log["skill_counts_30d"]
        if top:
            top_str = ", ".join(f"{s} ({c})" for s, c in list(top.items())[:7])
            lines.append(f"- Most used skills (last 30 days): {top_str}")
        else:
            lines.append("- Most used skills (last 30 days): no activity in last 30 days")

        never = skill_log["never_used"]
        if never:
            never_str = ", ".join(never[:8])
            suffix = f" (+{len(never)-8} more)" if len(never) > 8 else ""
            lines.append(f"- Skills never used: {never_str}{suffix}")
        else:
            lines.append("- Skills never used: all skills have been used at least once")
    else:
        lines.append("- Activity data: not available (no docs/skill-log.md found)")
        lines.append("  Run the sdlc-orchestrator to begin generating log entries.")

    lines.append("")

    # Skill log summary
    lines.append("## Skill log summary")

    if skill_log["available"]:
        total = skill_log["total_firings"]
        oc = skill_log["outcome_counts"]
        ok = oc.get("OK", 0)
        partial = oc.get("PARTIAL", 0)
        blocked = oc.get("BLOCKED", 0)

        ok_pct = round(ok / total * 100) if total > 0 else 0
        partial_pct = round(partial / total * 100) if total > 0 else 0
        blocked_pct = round(blocked / total * 100) if total > 0 else 0

        lines.append(f"- Total skill firings: {total}")
        lines.append(
            f"- Outcome: {ok} OK ({ok_pct}%), {partial} PARTIAL ({partial_pct}%), {blocked} BLOCKED ({blocked_pct}%)"
        )
    else:
        lines.append("- Skill log: not yet created — pipeline has not run")
        lines.append("  To create: trigger any skill via the sdlc-orchestrator")

    lines.append("")
    lines.append("---")
    lines.append("_Generated by scripts/health_report.py — run again to refresh_")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Project Health Dashboard — generates docs/health-report.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/health_report.py
  python scripts/health_report.py --stdout
        """,
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print report to stdout instead of writing to docs/health-report.md",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Path to repository root (default: auto-detected from script location)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = Path(args.repo).resolve() if args.repo else script_dir.parent

    log_path = repo_root / "docs" / "skill-log.md"
    status_path = repo_root / "docs" / "sdlc-status.md"

    print("Reading data sources...", file=sys.stderr)

    skill_log = read_skill_log(log_path)
    sdlc_status = read_sdlc_status(status_path)
    git_info = read_git_deployments(repo_root)
    coverage = read_coverage(repo_root)
    deps = read_dependencies(repo_root)

    # Log what was found
    sources_found = []
    sources_missing = []
    for name, data in [
        ("skill-log.md", skill_log),
        ("sdlc-status.md", sdlc_status),
        ("git tags", git_info),
        ("coverage", coverage),
        ("dependencies", deps),
    ]:
        (sources_found if data["available"] else sources_missing).append(name)

    if sources_found:
        print(f"  Found: {', '.join(sources_found)}", file=sys.stderr)
    if sources_missing:
        print(f"  Missing (skipped): {', '.join(sources_missing)}", file=sys.stderr)

    report = generate_report(skill_log, sdlc_status, git_info, coverage, deps, TODAY)

    if args.stdout:
        print(report)
    else:
        out_path = repo_root / "docs" / "health-report.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to: {out_path}", file=sys.stderr)
        print(f"Run 'cat {out_path}' to view.", file=sys.stderr)


if __name__ == "__main__":
    main()
