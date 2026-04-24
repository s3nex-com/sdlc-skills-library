# Prompt registry format

Prompts are code. They go in version control, follow a naming convention, and are promoted through the same gate as code changes: write, eval, review, merge.

---

## Directory structure

```
prompts/
  <feature-name>/
    v1.txt              — original prompt, never edited after deployment
    v2.txt              — next version (create; do not edit v1)
    registry.yaml       — version index with baseline scores and status
  <feature-name-2>/
    v1.txt
    registry.yaml
```

One directory per LLM feature. One file per version. `registry.yaml` is the single source of truth for which version is active and what its baseline score is.

---

## Version file naming

- Always `v<N>.txt` where N is an integer starting at 1.
- Never edit an existing version file once it has been deployed to production.
- Never rename version files.
- If you need to experiment, create a new version file.

The immutability rule is non-negotiable. It gives you an unambiguous rollback path: to roll back a prompt change, redeploy with the previous version file. If you edited the file in place, you no longer have that option.

---

## registry.yaml format

```yaml
feature: alert-summarizer
description: "Summarizes device alerts into a single concise sentence for the ops dashboard."
eval_dataset: evals/alert-summarizer/golden.jsonl
ci_threshold: 0.87          # fail CI if score drops below this absolute value

versions:
  - version: 1
    file: v1.txt
    deployed: 2026-03-10
    eval_score: 0.84
    status: retired         # retired | active | candidate
    notes: "Initial version. Failed on alerts without explicit timestamps."

  - version: 2
    file: v2.txt
    deployed: 2026-04-15
    eval_score: 0.91
    status: active
    notes: "Added explicit instruction to infer time from context when not stated."

  - version: 3
    file: v3.txt
    deployed: null           # null = not yet deployed
    eval_score: 0.93
    status: candidate        # passed eval; pending A/B test
    notes: "Shorter system prompt; restructured output instructions."
```

**Status values:**
- `active` — currently serving production traffic
- `candidate` — eval passed; A/B test in progress or pending
- `retired` — replaced by a newer version; do not redeploy without re-evaluating

---

## Promotion checklist

Before merging a new prompt version:

- [ ] New version file created (`v<N>.txt`). Existing version file untouched.
- [ ] Full eval suite run against the new version using `eval-harness-template.py`.
- [ ] Eval score meets or exceeds the `ci_threshold` in `registry.yaml`.
- [ ] Eval score meets or exceeds the previous active version's score (regression check).
- [ ] `registry.yaml` updated: new version entry added with `status: candidate`, `eval_score` filled in.
- [ ] PR includes the eval result JSON as an artifact or attached comment.
- [ ] A/B test plan defined if the change is significant (see below).

---

## A/B testing prompt versions

Use A/B testing for any prompt change that affects output format, length, or tone — not just correctness. Eval scores measure correctness; A/B tests measure real-world quality and user behaviour.

**Process:**

1. Deploy the candidate version alongside the active version.
2. Route N% of traffic to the candidate (start with 10%).
3. Collect metrics for both versions for a meaningful sample (at minimum 200 requests, or 48 hours of normal traffic — whichever comes first).
4. Compare: eval score on production samples, latency, and any user feedback signals (thumbs-up/down, follow-up questions, explicit corrections).
5. If candidate matches or beats active on all three signals: promote to `active`, retire the old version.
6. If candidate underperforms: keep active version, set candidate to `retired`, document the failure reason in `notes`.

**Traffic routing:** implement in your application code, not in the prompt registry. The registry records the outcome.

```python
import random

def get_prompt_version(feature: str, candidate_pct: float = 0.0) -> str:
    """
    Returns the prompt file path for a feature, routing `candidate_pct`
    fraction of requests to the candidate version when one exists.
    """
    registry = load_registry(f"prompts/{feature}/registry.yaml")
    active = next(v for v in registry["versions"] if v["status"] == "active")
    candidate = next((v for v in registry["versions"] if v["status"] == "candidate"), None)

    if candidate and random.random() < candidate_pct:
        version = candidate
    else:
        version = active

    return f"prompts/{feature}/{version['file']}", version["version"]
```

Log which version was used on every request (`prompt_version` field in your telemetry). Without this, you cannot compute per-version metrics.

---

## Loading prompts in application code

Load from file at startup (or cache with a short TTL). Never hardcode prompt text in application logic.

```python
from pathlib import Path
import functools

@functools.lru_cache(maxsize=32)
def load_prompt(feature: str, version: int) -> str:
    path = Path(f"prompts/{feature}/v{version}.txt")
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()
```

Use `lru_cache` (or equivalent) to avoid re-reading the file on every request. Restart the service to pick up a new prompt version — this is intentional, it makes deployments explicit.

---

## Prompt file format

Prompt files are plain text. Use a consistent structure:

```
SYSTEM INSTRUCTIONS
-------------------
You are a device alert summarizer. You receive raw alert text from IoT device monitoring
and return a single concise sentence describing the alert. Be factual. Do not invent
device IDs or values not present in the alert. If the duration is not stated, omit it.

OUTPUT FORMAT
-------------
One sentence. Maximum 100 tokens. No markdown. No bullet points.

EXAMPLES
--------
Input: CPU at 98% for 10 minutes on device dev-001
Output: Device dev-001 experienced a sustained high-CPU event (98%) lasting 10 minutes.

Input: Memory pressure detected
Output: Memory pressure was detected on the monitored device.
```

Include at least two examples in every prompt file. Examples are the most reliable way to steer output format — they outperform abstract instructions in most models.

---

## What not to do

- Do not hardcode the prompt text as a string constant in application source. When it changes, the change is invisible in code review.
- Do not use a single shared prompt file for multiple features. Separate prompts, separate versions, separate eval datasets.
- Do not merge a prompt change without an eval run. Treat it like a schema migration: you would not merge a schema change without running migration tests.
- Do not delete old version files. Retired versions are the historical record and the rollback target.
