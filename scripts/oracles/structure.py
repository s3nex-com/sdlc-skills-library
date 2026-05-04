"""Structure oracle — assert required sections/phrases and forbid banned phrases."""

from __future__ import annotations

import re


def run(oracle_cfg: dict, response_text: str) -> dict:
    rules = oracle_cfg.get("structure_rules") or {}
    required_sections = rules.get("required_sections") or []
    required_phrases = rules.get("required_phrases") or []
    forbidden_phrases = rules.get("forbidden_phrases") or []

    checks: list[dict] = []
    all_pass = True

    for section in required_sections:
        found = bool(re.search(re.escape(section), response_text, re.IGNORECASE))
        checks.append({"rule": f"required_section: {section}", "result": "PASS" if found else "FAIL"})
        if not found:
            all_pass = False

    for phrase in required_phrases:
        found = bool(re.search(re.escape(phrase), response_text, re.IGNORECASE))
        checks.append({"rule": f"required_phrase: {phrase}", "result": "PASS" if found else "FAIL"})
        if not found:
            all_pass = False

    for phrase in forbidden_phrases:
        found = bool(re.search(re.escape(phrase), response_text, re.IGNORECASE))
        checks.append({"rule": f"forbidden_phrase: {phrase}", "result": "FAIL" if found else "PASS"})
        if found:
            all_pass = False

    return {"status": "PASS" if all_pass else "FAIL", "checks": checks}
