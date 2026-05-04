"""Rubric oracle — load rubric YAML, write a human-review sheet, return PENDING_RUBRIC."""

from __future__ import annotations

from pathlib import Path

import yaml


def run(
    scenario: dict,
    oracle_cfg: dict,
    response_text: str,
    repo_root: Path,
    output_dir: Path,
) -> dict:
    rubric_id = scenario.get("rubric_id") or oracle_cfg.get("rubric_id")
    if not rubric_id:
        return {"status": "ERROR", "detail": "rubric oracle requires rubric_id", "checks": []}

    rubric_files = list((repo_root / "tests" / "rubrics").glob(f"{rubric_id}-*.yaml"))
    if not rubric_files:
        return {
            "status": "ERROR",
            "detail": f"No rubric file found for {rubric_id} in tests/rubrics/",
            "checks": [],
        }

    rubric = yaml.safe_load(rubric_files[0].read_text(encoding="utf-8"))
    criteria = rubric.get("criteria", [])
    scoring = rubric.get("scoring", {})
    mandatory = scoring.get("mandatory", [])
    threshold = scoring.get("pass_threshold", len(criteria))

    review_dir = output_dir / "rubrics"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"{scenario['id']}-review.md"

    preview = response_text[:3000] + ("…" if len(response_text) > 3000 else "")
    rows = "\n".join(f"| {c['id']} | {c['check'][:80]} | [ ] | |" for c in criteria)

    review_path.write_text(
        f"# Rubric review: {scenario['id']} — {scenario.get('name', '')}\n"
        f"**Rubric:** {rubric_id}  |  **Skill:** {scenario.get('skill', '')}\n\n"
        f"## Model response\n\n```\n{preview}\n```\n\n"
        f"## Criteria checklist\n\n"
        f"| ID | Check | Pass? | Notes |\n"
        f"|----|-------|-------|-------|\n"
        f"{rows}\n\n"
        f"**Pass threshold:** {threshold} of {len(criteria)}  "
        f"**Mandatory:** {', '.join(mandatory) if mandatory else 'none'}\n\n"
        f"_Fill in Pass? column (Y/N) and save._\n",
        encoding="utf-8",
    )

    return {
        "status": "PENDING_RUBRIC",
        "rubric_id": rubric_id,
        "review_path": str(review_path),
        "criteria_count": len(criteria),
        "mandatory": mandatory,
        "checks": [{"rule": f"rubric_criterion: {c['id']}", "result": "PENDING"} for c in criteria],
    }
