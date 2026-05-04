"""Tool-backed oracle — extract artifact from response, write to tmp/, run script, check exit code."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


# Maps script filename → function that returns the CLI args list given artifact path.
SCRIPT_ARGS: dict[str, object] = {
    "validate_openapi.py": lambda p: ["--spec", str(p), "--fail-on-critical"],
    "migration_risk.py": lambda p: [str(p)],
    "check_orphans.py": lambda p: [str(p)],
}


def _extract_code_block(text: str, lang: str = "yaml") -> str | None:
    # Try language-tagged block first (yaml or yml)
    pattern = re.compile(
        rf"```(?:{re.escape(lang)}|yml)\s*\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(text)
    if m:
        return m.group(1)
    # Fall back to any fenced block
    m = re.compile(r"```\w*\s*\n(.*?)```", re.DOTALL).search(text)
    return m.group(1) if m else None


def run(
    scenario: dict,
    oracle_cfg: dict,
    response_text: str,
    output_dir: Path,
    repo_root: Path,
) -> dict:
    scenario_id = scenario["id"]
    script_rel = oracle_cfg.get("script")

    if not script_rel:
        return {"status": "ERROR", "detail": "tool_backed oracle missing script path", "checks": []}

    artifact = _extract_code_block(response_text)
    if artifact is None:
        return {
            "status": "FAIL",
            "detail": "No code block found in response",
            "checks": [{"rule": "extract_artifact", "result": "FAIL"}],
        }

    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifacts_dir / f"{scenario_id}-output.yaml"
    artifact_path.write_text(artifact, encoding="utf-8")

    script_path = repo_root / script_rel
    if not script_path.exists():
        return {
            "status": "ERROR",
            "detail": f"Script not found: {script_rel}",
            "checks": [{"rule": "script_exists", "result": "FAIL"}],
        }

    args_fn = SCRIPT_ARGS.get(script_path.name, lambda p: [str(p)])
    cmd = [sys.executable, str(script_path)] + args_fn(artifact_path)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {
            "status": "ERROR",
            "detail": "Script timed out after 30s",
            "checks": [{"rule": "script_exit_code", "result": "ERROR"}],
        }

    passed = proc.returncode == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "artifact_path": str(artifact_path),
        "script": script_rel,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[:2000],
        "stderr": proc.stderr[:500],
        "checks": [
            {"rule": "extract_artifact", "result": "PASS"},
            {"rule": "script_exit_code", "result": "PASS" if passed else "FAIL"},
        ],
    }
