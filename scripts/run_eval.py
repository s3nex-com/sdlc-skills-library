# -*- coding: utf-8 -*-
"""
run_eval.py - Replay skill evaluation scenarios against the Claude API and check oracle rules.

Each scenario YAML in tests/scenarios/ defines a user prompt, the skill to load as system
context, mode/track injection, and an oracle (structure assertions, tool-backed script, or
human rubric). This harness replays the prompt, saves the transcript, runs the oracle, and
emits a pass/fail report.

Usage:
    python scripts/run_eval.py                          # all scenarios in tests/scenarios/golden/
    python scripts/run_eval.py --scenario S-02          # single scenario by ID
    python scripts/run_eval.py --scenario-dir tests/scenarios/golden/
    python scripts/run_eval.py --model claude-sonnet-4-6
    python scripts/run_eval.py --output-dir tmp/
    python scripts/run_eval.py --dry-run                # load scenarios, skip API calls
    python scripts/run_eval.py --json                   # machine-readable report to stdout

Requirements:
    pip install anthropic pyyaml
    export ANTHROPIC_API_KEY=...
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Allow `from oracles import ...` when run as scripts/run_eval.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracles import rubric as rubric_oracle
from oracles import structure as structure_oracle
from oracles import tool_backed as tool_backed_oracle

SEPARATOR = "━" * 60
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_GOLDEN_DIR = "tests/scenarios/golden"
DEFAULT_OUTPUT_DIR = "tmp"
MAX_TOKENS = 4096


# ---------------------------------------------------------------------------
# Repo root
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Scenario loading
# ---------------------------------------------------------------------------

def load_scenario(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_scenarios(scenario_dir: Path, filter_id: str | None) -> list[dict]:
    scenarios = [load_scenario(f) for f in sorted(scenario_dir.glob("*.yaml"))]
    if filter_id:
        scenarios = [s for s in scenarios if s.get("id") == filter_id]
    return scenarios


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_user_message(scenario: dict) -> str:
    mode = scenario.get("mode", "standard")
    tracks = scenario.get("tracks") or []
    workflow_path = scenario.get("workflow_path") or "none"
    tracks_str = ", ".join(tracks) if tracks else "none"
    header = (
        f"**Session context (injected by evaluator)**\n"
        f"- Mode: {mode}\n"
        f"- Tracks: {tracks_str}\n"
        f"- Workflow path: {workflow_path}\n\n---\n\n"
    )
    return header + scenario["user_prompt"].strip()


# ---------------------------------------------------------------------------
# Claude API
# ---------------------------------------------------------------------------

def call_claude(system_prompt: str, user_message: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(2):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return msg.content[0].text
        except Exception as exc:
            if attempt == 0:
                time.sleep(5)
                continue
            raise RuntimeError(f"Claude API call failed: {exc}") from exc

    raise RuntimeError("Unreachable")


# ---------------------------------------------------------------------------
# Transcript persistence
# ---------------------------------------------------------------------------

def save_transcript(output_dir: Path, scenario: dict, response_text: str) -> Path:
    transcripts_dir = output_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    path = transcripts_dir / f"{scenario['id']}.json"
    path.write_text(
        json.dumps(
            {
                "scenario_id": scenario["id"],
                "scenario_name": scenario.get("name"),
                "skill": scenario.get("skill"),
                "mode": scenario.get("mode"),
                "tracks": scenario.get("tracks"),
                "response": response_text,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Oracle dispatch
# ---------------------------------------------------------------------------

def run_oracle(scenario: dict, response_text: str, output_dir: Path, root: Path) -> dict:
    oracle_cfg = scenario.get("oracle") or {}
    kind = oracle_cfg.get("kind", "structure")

    if kind == "structure":
        return structure_oracle.run(oracle_cfg, response_text)
    if kind == "tool_backed":
        return tool_backed_oracle.run(scenario, oracle_cfg, response_text, output_dir, root)
    if kind == "rubric":
        return rubric_oracle.run(scenario, oracle_cfg, response_text, root, output_dir)

    return {"status": "ERROR", "detail": f"Unknown oracle kind: {kind!r}", "checks": []}


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

def run_scenario(scenario: dict, model: str, output_dir: Path, dry_run: bool, root: Path) -> dict:
    base = {
        "id": scenario.get("id", "?"),
        "name": scenario.get("name", ""),
        "tag": scenario.get("tag", ""),
        "skill": scenario.get("skill", ""),
        "oracle_kind": (scenario.get("oracle") or {}).get("kind", ""),
    }

    skill_load_path = (scenario.get("context") or {}).get("skill_load_path", "")
    skill_path = root / skill_load_path

    if not skill_path.exists():
        return {**base, "status": "ERROR", "detail": f"SKILL.md not found: {skill_load_path}", "checks": []}

    system_prompt = skill_path.read_text(encoding="utf-8")
    user_message = build_user_message(scenario)

    if dry_run:
        return {**base, "status": "DRY_RUN", "detail": "dry-run — API call skipped", "checks": []}

    try:
        response_text = call_claude(system_prompt, user_message, model)
    except RuntimeError as exc:
        return {**base, "status": "ERROR", "detail": str(exc), "checks": []}

    transcript_path = save_transcript(output_dir, scenario, response_text)
    oracle_result = run_oracle(scenario, response_text, output_dir, root)

    return {**base, **oracle_result, "transcript_path": str(transcript_path)}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _count(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in results:
        s = r.get("status", "ERROR")
        counts[s] = counts.get(s, 0) + 1
    return counts


def format_text(results: list[dict], model: str) -> str:
    counts = _count(results)
    lines = [f"Skill library eval — {len(results)} scenarios — {model}", SEPARATOR]

    for r in results:
        status = r.get("status", "ERROR")
        skill = r.get("skill", "")[:22]
        oracle_kind = r.get("oracle_kind", "")[:13]

        if status == "FAIL":
            failed = [c["rule"] for c in r.get("checks", []) if c.get("result") == "FAIL"]
            detail = "→ " + "; ".join(failed[:3])
        elif status == "PENDING_RUBRIC":
            detail = f"→ {r.get('review_path', '')}"
        elif status == "ERROR":
            detail = f"→ {str(r.get('detail', ''))[:60]}"
        else:
            detail = ""

        lines.append(
            f"{status:<15} {r['id']:<6} {r.get('tag','?')}  "
            f"{skill:<24} {oracle_kind:<14} {detail}"
        )

    lines.append(SEPARATOR)
    summary_parts = [
        f"{counts.get('PASS', 0)} PASS",
        f"{counts.get('FAIL', 0)} FAIL",
        f"{counts.get('ERROR', 0)} ERROR",
        f"{counts.get('PENDING_RUBRIC', 0)} PENDING_RUBRIC",
    ]
    if counts.get("DRY_RUN"):
        summary_parts.append(f"{counts['DRY_RUN']} DRY_RUN")
    lines.append("Results: " + ", ".join(summary_parts))
    return "\n".join(lines)


def format_json(results: list[dict], model: str) -> str:
    counts = _count(results)
    return json.dumps(
        {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "total": len(results),
            **counts,
            "results": results,
        },
        indent=2,
        ensure_ascii=False,
    )


def save_report(output_dir: Path, results: list[dict], model: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.json"
    path.write_text(format_json(results, model), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay skill evaluation scenarios against the Claude API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_eval.py
  python scripts/run_eval.py --scenario S-02
  python scripts/run_eval.py --dry-run
  python scripts/run_eval.py --json --output-dir tmp/
        """,
    )
    parser.add_argument("--scenario", default=None, metavar="ID",
                        help="Run a single scenario by ID (e.g. S-02)")
    parser.add_argument("--scenario-dir", default=None, metavar="DIR",
                        help=f"Scenario directory (default: {DEFAULT_GOLDEN_DIR})")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Claude model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, metavar="DIR",
                        help=f"Output directory for transcripts and report (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Load scenarios and build prompts, but skip API calls")
    parser.add_argument("--json", action="store_true",
                        help="Print JSON report to stdout instead of human-readable table")
    args = parser.parse_args()

    root = _repo_root()
    scenario_dir = Path(args.scenario_dir) if args.scenario_dir else root / DEFAULT_GOLDEN_DIR

    if not scenario_dir.exists():
        print(f"ERROR: Scenario directory not found: {scenario_dir}", file=sys.stderr)
        sys.exit(2)

    scenarios = load_scenarios(scenario_dir, args.scenario)
    if not scenarios:
        suffix = f" matching ID '{args.scenario}'" if args.scenario else ""
        print(f"ERROR: No scenarios found{suffix} in {scenario_dir}", file=sys.stderr)
        sys.exit(2)

    output_dir = root / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    results: list[dict] = []

    for scenario in scenarios:
        if not args.json:
            print(f"  {scenario.get('id','?')}  {scenario.get('skill','')}...", end=" ", flush=True)
        result = run_scenario(scenario, args.model, output_dir, args.dry_run, root)
        results.append(result)
        if not args.json:
            print(result.get("status", "ERROR"))

    report_path = save_report(output_dir, results, args.model)

    if args.json:
        print(format_json(results, args.model))
    else:
        print()
        print(format_text(results, args.model))
        print(f"\nReport: {report_path}")

    sys.exit(1 if any(r.get("status") in ("FAIL", "ERROR") for r in results) else 0)


if __name__ == "__main__":
    main()
