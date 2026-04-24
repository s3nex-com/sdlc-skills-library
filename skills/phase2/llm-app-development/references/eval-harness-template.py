#!/usr/bin/env python3
"""
LLM eval harness — no external framework dependencies.

Usage:
    python eval-harness-template.py \
        --dataset evals/alert-summarizer/golden.jsonl \
        --baseline 0.91 \
        --threshold 0.05

Exit codes:
    0 — eval passed (score within threshold of baseline)
    1 — eval failed (score dropped more than threshold from baseline)
    2 — harness error (dataset missing, LLM call failed, etc.)

Replace `call_llm()` and `check_criterion()` with your actual implementations.
"""

import json
import sys
import argparse
import hashlib
import time
from typing import Any


# ---------------------------------------------------------------------------
# 1. Replace this with your actual LLM client call.
# ---------------------------------------------------------------------------

def call_llm(prompt: str, input_text: str, model: str = "claude-haiku-4-5") -> dict:
    """
    Call the LLM and return a dict with `output` (str) and `metadata` (dict).

    Example using the Anthropic SDK:

        import anthropic
        client = anthropic.Anthropic()

        message = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt + "\n\n" + input_text}]
        )
        output_text = message.content[0].text
        return {
            "output": output_text,
            "metadata": {
                "prompt_tokens": message.usage.input_tokens,
                "completion_tokens": message.usage.output_tokens,
                "finish_reason": message.stop_reason,
            }
        }

    For local testing without API calls, return a stub:
    """
    # STUB — replace with real implementation
    return {
        "output": f"[STUB] Processed: {input_text[:50]}",
        "metadata": {"prompt_tokens": 0, "completion_tokens": 0, "finish_reason": "end_turn"},
    }


# ---------------------------------------------------------------------------
# 2. Replace or extend this with your criterion checkers.
# ---------------------------------------------------------------------------

def check_criterion(output: str, criterion: str, llm_judge: bool = False) -> bool:
    """
    Check whether `output` satisfies `criterion`.

    Criterion format conventions (pick one per criterion):
        keyword:<term>          — output must contain the term (case-insensitive)
        not:<term>              — output must NOT contain the term (case-insensitive)
        max_tokens:<n>          — output must be under n tokens (rough: words * 1.3)
        json_valid              — output must parse as valid JSON
        <free text>             — falls back to LLM-as-judge if llm_judge=True,
                                  otherwise treated as keyword check

    LLM-as-judge is slower and costs tokens. Enable it only for criteria that
    cannot be checked programmatically.
    """
    criterion_lower = criterion.lower()

    if criterion_lower.startswith("keyword:"):
        term = criterion[len("keyword:"):].strip()
        return term.lower() in output.lower()

    if criterion_lower.startswith("not:"):
        term = criterion[len("not:"):].strip()
        return term.lower() not in output.lower()

    if criterion_lower.startswith("max_tokens:"):
        n = int(criterion[len("max_tokens:"):].strip())
        rough_token_count = len(output.split()) * 1.3
        return rough_token_count < n

    if criterion_lower == "json_valid":
        try:
            json.loads(output)
            return True
        except json.JSONDecodeError:
            return False

    # Free-text criterion: keyword heuristic first, LLM-as-judge if enabled
    # Simple heuristic: does the criterion phrase appear (partially) in the output?
    words = [w for w in criterion_lower.split() if len(w) > 3]
    keyword_match = any(w in output.lower() for w in words)

    if keyword_match or not llm_judge:
        return keyword_match

    # LLM-as-judge path — replace with your judge call
    return _llm_judge(output, criterion)


def _llm_judge(output: str, criterion: str) -> bool:
    """
    Ask a separate LLM call to evaluate whether `output` satisfies `criterion`.
    Returns True if the judge says yes.
    """
    judge_prompt = (
        f"You are an evaluator. Does the following output satisfy this criterion?\n\n"
        f"Criterion: {criterion}\n\n"
        f"Output:\n{output}\n\n"
        f"Respond with exactly 'YES' or 'NO'."
    )
    result = call_llm(judge_prompt, "")
    return result["output"].strip().upper().startswith("YES")


# ---------------------------------------------------------------------------
# 3. Core eval runner — do not modify this section.
# ---------------------------------------------------------------------------

def load_dataset(path: str) -> list[dict]:
    """Load a JSONL eval dataset. Each line is a JSON object (one eval case)."""
    cases = []
    with open(path) as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"ERROR: line {line_number} in {path} is not valid JSON: {e}", file=sys.stderr)
                sys.exit(2)
    return cases


def run_eval(
    dataset: list[dict],
    prompt: str,
    model: str,
    use_llm_judge: bool = False,
) -> dict[str, Any]:
    """
    Run all eval cases and return a results dict.

    Each case in the dataset must have:
        input (str)                — the input text
        passing_criteria (list)   — list of criterion strings
        weight (float, optional)  — default 1.0; higher weight = more impact on score
    """
    case_results = []
    total_weighted_score = 0.0
    total_weight = 0.0

    for i, case in enumerate(dataset):
        input_text = case["input"]
        criteria = case["passing_criteria"]
        weight = float(case.get("weight", 1.0))

        start = time.monotonic()
        llm_result = call_llm(prompt, input_text, model)
        latency_ms = int((time.monotonic() - start) * 1000)

        output = llm_result["output"]
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]

        passed_criteria = []
        failed_criteria = []
        for criterion in criteria:
            ok = check_criterion(output, criterion, llm_judge=use_llm_judge)
            (passed_criteria if ok else failed_criteria).append(criterion)

        case_score = len(passed_criteria) / len(criteria) if criteria else 1.0
        weighted_score = case_score * weight

        total_weighted_score += weighted_score
        total_weight += weight

        case_results.append({
            "index": i,
            "input": input_text[:120] + ("..." if len(input_text) > 120 else ""),
            "output": output[:200] + ("..." if len(output) > 200 else ""),
            "passed": passed_criteria,
            "failed": failed_criteria,
            "score": round(case_score, 4),
            "weight": weight,
            "latency_ms": latency_ms,
            "prompt_hash": prompt_hash,
            "metadata": llm_result.get("metadata", {}),
        })

    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

    failures = [r for r in case_results if r["failed"]]

    return {
        "overall_score": round(overall_score, 4),
        "total_cases": len(dataset),
        "failure_count": len(failures),
        "failures": failures,
        "cases": case_results,
    }


def ci_check(score: float, baseline: float, threshold: float) -> tuple[bool, str]:
    """
    Returns (passed, message).
    Fails if score dropped more than `threshold` (fractional) below baseline.
    """
    drop = baseline - score
    max_allowed_drop = baseline * threshold
    if drop > max_allowed_drop:
        return False, (
            f"FAIL: score {score:.4f} is {drop:.4f} below baseline {baseline:.4f} "
            f"(max allowed drop: {max_allowed_drop:.4f} = {threshold*100:.0f}% of baseline)"
        )
    return True, (
        f"PASS: score {score:.4f} vs baseline {baseline:.4f} "
        f"(drop {drop:.4f} within {threshold*100:.0f}% threshold)"
    )


# ---------------------------------------------------------------------------
# 4. CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LLM eval harness")
    parser.add_argument("--dataset", required=True, help="Path to JSONL eval dataset")
    parser.add_argument("--prompt-file", help="Path to prompt file (optional; uses empty prompt if omitted)")
    parser.add_argument("--model", default="claude-haiku-4-5", help="Model identifier")
    parser.add_argument("--baseline", type=float, default=None, help="Baseline score to compare against")
    parser.add_argument("--threshold", type=float, default=0.05, help="Max allowed fractional drop from baseline (default: 0.05)")
    parser.add_argument("--llm-judge", action="store_true", help="Enable LLM-as-judge for free-text criteria")
    parser.add_argument("--output", help="Write JSON results to this file (optional)")
    args = parser.parse_args()

    prompt = ""
    if args.prompt_file:
        with open(args.prompt_file) as f:
            prompt = f.read()

    try:
        dataset = load_dataset(args.dataset)
    except FileNotFoundError:
        print(f"ERROR: dataset not found: {args.dataset}", file=sys.stderr)
        sys.exit(2)

    print(f"Running {len(dataset)} eval cases against model={args.model} ...", flush=True)
    results = run_eval(dataset, prompt, args.model, use_llm_judge=args.llm_judge)

    print(f"\nOverall score: {results['overall_score']:.4f}  ({results['failure_count']} cases with failures out of {results['total_cases']})")

    if results["failures"]:
        print("\nFailures:")
        for f in results["failures"]:
            print(f"  Case {f['index']}: failed criteria: {f['failed']}")
            print(f"    Input:  {f['input']}")
            print(f"    Output: {f['output']}")

    if args.output:
        with open(args.output, "w") as out:
            json.dump(results, out, indent=2)
        print(f"\nResults written to {args.output}")

    if args.baseline is not None:
        passed, message = ci_check(results["overall_score"], args.baseline, args.threshold)
        print(f"\nCI gate: {message}")
        sys.exit(0 if passed else 1)

    sys.exit(0)


if __name__ == "__main__":
    main()
