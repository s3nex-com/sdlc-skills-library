"""
sdlc-skills-library Mode Advisor

Asks the 3-question mode derivation and recommends a delivery mode (Nano/Lean/Standard/Rigorous)
along with the skills to run for that mode.

Usage:
    python scripts/mode_advisor.py           # interactive mode
    python scripts/mode_advisor.py --json    # output result as JSON for tooling integration
    python scripts/mode_advisor.py --help
"""

from __future__ import annotations

import argparse
import json
import sys

# ---------------------------------------------------------------------------
# Mode definitions
# ---------------------------------------------------------------------------

MODES = {
    "NANO": {
        "description": "Internal-only, reversible, no external dependencies.",
        "phase1": ["prd-creator", "requirements-tracer"],
        "phase2": ["code-implementer", "code-review-quality-gates", "pr-merge-orchestrator"],
        "phase3": [],
        "estimated_time": "< 1 day | ~20k Claude tokens",
        "gates": "Soft — self-review acceptable, no mandatory peer review",
    },
    "LEAN": {
        "description": "External users affected, easy rollback, no API contract dependencies.",
        "phase1": [
            "prd-creator",
            "requirements-tracer",
            "design-doc-generator",
            "architecture-decision-records",
        ],
        "phase2": [
            "code-implementer",
            "comprehensive-test-strategy",
            "code-review-quality-gates",
            "executable-acceptance-verification",
            "release-readiness",
            "pr-merge-orchestrator",
        ],
        "phase3": ["delivery-metrics-dora (post go-live)"],
        "estimated_time": "1–2 days | ~40k Claude tokens",
        "gates": "Soft — peer review strongly recommended",
    },
    "STANDARD": {
        "description": "External users, external API contract dependencies, or hard rollback.",
        "phase1": [
            "prd-creator",
            "requirements-tracer",
            "design-doc-generator",
            "specification-driven-development",
            "security-audit-secure-sdlc",
            "data-governance-privacy",
            "architecture-decision-records",
            "technical-risk-management",
        ],
        "phase2": [
            "code-implementer",
            "comprehensive-test-strategy",
            "code-review-quality-gates",
            "api-contract-enforcer",
            "executable-acceptance-verification",
            "release-readiness",
            "pr-merge-orchestrator",
        ],
        "phase3": ["delivery-metrics-dora", "technical-debt-tracker (post go-live)"],
        "estimated_time": "3–5 days | ~80k Claude tokens",
        "gates": "Hard — all gates must pass, peer review mandatory",
    },
    "RIGOROUS": {
        "description": "Regulated users, financial transactions, critical infrastructure, or irreversible changes.",
        "phase1": [
            "prd-creator",
            "requirements-tracer",
            "design-doc-generator",
            "specification-driven-development",
            "architecture-review-governance",
            "architecture-decision-records",
            "technical-risk-management",
            "security-audit-secure-sdlc",
            "data-governance-privacy",
            "stakeholder-sync",
        ],
        "phase2": [
            "code-implementer",
            "comprehensive-test-strategy",
            "code-review-quality-gates",
            "api-contract-enforcer",
            "executable-acceptance-verification",
            "performance-reliability-engineering",
            "observability-sre-practice",
            "devops-pipeline-governance",
            "release-readiness",
            "pr-merge-orchestrator",
        ],
        "phase3": [
            "delivery-metrics-dora",
            "technical-debt-tracker",
            "incident-postmortem",
            "dependency-health-management (post go-live)",
        ],
        "phase4": ["formal-verification (if distributed protocol involved)"],
        "estimated_time": "1–2 weeks | ~150k+ Claude tokens",
        "gates": "Hard — full sign-off chain, security review mandatory, staged rollout required",
    },
}

# ---------------------------------------------------------------------------
# Questions and derivation logic
# ---------------------------------------------------------------------------

QUESTIONS = [
    {
        "id": "q1",
        "text": "Q1. Who uses this feature if it breaks?",
        "choices": [
            "Internal team only",
            "Paying customers or external users",
            "Regulated users, financial transactions, or critical infrastructure",
        ],
    },
    {
        "id": "q2",
        "text": "Q2. Does another system or team depend on this API contract?",
        "choices": [
            "No external dependencies",
            "Yes — another team/system consumes this API",
        ],
    },
    {
        "id": "q3",
        "text": "Q3. Is this reversible if something goes wrong?",
        "choices": [
            "Yes — easy rollback (feature flag, config change)",
            "Hard rollback (database migration, data transformation)",
            "Irreversible (data deletion, external side effects, financial transactions)",
        ],
    },
]


def derive_mode(q1: int, q2: int, q3: int) -> tuple[str, list[str]]:
    """
    Derive mode from 1-indexed question answers.
    Returns (mode_name, list_of_reasoning_strings).
    """
    reasoning = []
    score = 0  # 0=Nano, 1=Lean, 2=Standard, 3=Rigorous

    # Q1
    if q1 == 1:
        reasoning.append("Q1: Internal team only → baseline Nano")
        score = max(score, 0)
    elif q1 == 2:
        reasoning.append("Q1: External users → baseline Lean")
        score = max(score, 1)
    else:
        reasoning.append("Q1: Regulated/critical users → elevate to Rigorous")
        score = max(score, 3)

    # Q2
    if q2 == 1:
        reasoning.append("Q2: No external API dependencies → no elevation from Q2")
    else:
        reasoning.append("Q2: External API contract → elevate to Standard")
        score = max(score, 2)

    # Q3
    if q3 == 1:
        reasoning.append("Q3: Easy rollback → no further elevation")
    elif q3 == 2:
        reasoning.append("Q3: Hard rollback (migration) → elevate to Standard")
        score = max(score, 2)
    else:
        reasoning.append("Q3: Irreversible change → elevate to Rigorous")
        score = max(score, 3)

    mode_map = {0: "NANO", 1: "LEAN", 2: "STANDARD", 3: "RIGOROUS"}
    return mode_map[score], reasoning


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

SEPARATOR = "━" * 35


def ask_question(question: dict) -> int:
    """Print a question and return the 1-indexed choice."""
    print()
    print(question["text"])
    for i, choice in enumerate(question["choices"], 1):
        print(f"  [{i}] {choice}")
    while True:
        raw = input("Choice: ").strip()
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(question["choices"]):
                return choice
        print(f"  Please enter a number between 1 and {len(question['choices'])}")


def wrap_list(items: list[str], indent: int = 10, width: int = 72) -> str:
    """Wrap a list of skill names with indentation for display."""
    prefix = " " * indent
    lines = []
    current = ""
    for item in items:
        if not current:
            current = item
        elif len(prefix + current + ", " + item) > width:
            lines.append(current)
            current = item
        else:
            current += ", " + item
    if current:
        lines.append(current)
    joiner = "\n" + prefix
    return joiner.join(lines)


def print_result(mode: str, reasoning: list[str], as_json: bool = False) -> None:
    mode_data = MODES[mode]

    if as_json:
        output = {
            "recommended_mode": mode,
            "description": mode_data["description"],
            "reasoning": reasoning,
            "skills": {
                "phase1": mode_data.get("phase1", []),
                "phase2": mode_data.get("phase2", []),
                "phase3": mode_data.get("phase3", []),
                **({"phase4": mode_data["phase4"]} if "phase4" in mode_data else {}),
            },
            "estimated_time": mode_data["estimated_time"],
            "gates": mode_data["gates"],
        }
        print(json.dumps(output, indent=2))
        return

    print()
    print(SEPARATOR)
    print(f"Recommended mode: {mode}")
    print()
    print("Reasoning:")
    for r in reasoning:
        print(f"  {r}")
    print()
    print("Skills to run:")

    p1 = mode_data.get("phase1", [])
    p2 = mode_data.get("phase2", [])
    p3 = mode_data.get("phase3", [])
    p4 = mode_data.get("phase4", [])

    if p1:
        wrapped = wrap_list(p1)
        print(f"  Phase 1: {wrapped}")
    if p2:
        wrapped = wrap_list(p2)
        print(f"  Phase 2: {wrapped}")
    if p3:
        wrapped = wrap_list(p3)
        print(f"  Phase 3: {wrapped}")
    if p4:
        wrapped = wrap_list(p4)
        print(f"  Phase 4: {wrapped}")

    print()
    print(f"Estimated time: {mode_data['estimated_time']}")
    print(f"Gates: {mode_data['gates']}")
    print()
    print("To override: tell the orchestrator \"use [nano|lean|standard|rigorous] mode\"")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Mode Advisor — derives the appropriate delivery mode from 3 questions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/mode_advisor.py           # interactive prompts
  python scripts/mode_advisor.py --json    # machine-readable JSON output
        """,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON (for tooling integration)",
    )
    args = parser.parse_args()

    if not args.json:
        print()
        print("sdlc-skills-library Mode Advisor")
        print(SEPARATOR)

    answers = []
    for question in QUESTIONS:
        try:
            answer = ask_question(question)
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)
        answers.append(answer)

    mode, reasoning = derive_mode(*answers)
    print_result(mode, reasoning, as_json=args.json)


if __name__ == "__main__":
    main()
