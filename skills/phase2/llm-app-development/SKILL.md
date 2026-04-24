---
name: llm-app-development
description: >
  Activate when building software that calls an LLM internally — your product
  is the builder, not just the user. Use when designing prompt pipelines,
  implementing a RAG system, building agent tool loops, setting up an eval
  framework, or shipping an AI-powered feature. Trigger phrases: "build an LLM
  feature", "add AI to the product", "implement a chatbot", "build a RAG
  pipeline", "prompt engineering for our app", "eval framework", "we're
  shipping an AI feature", "LLM pipeline", "AI-powered feature".
---

# LLM application development

## Purpose

This skill covers building software products that use an LLM as a component — your code calls the LLM, your team owns the prompt, and the output becomes part of your system's behaviour. This is distinct from `ai-assisted-engineering`, which covers using AI tools (Claude Code, Copilot, Cursor) to write your code faster. The difference: `ai-assisted-engineering` is about your workflow; this skill is about what you are shipping to users.

LLM integration is engineering, not magic. The discipline is: write evals before you write prompts (just as you write tests before you write code), version prompts like code, choose the right pipeline pattern, instrument everything in production, and contain the failure modes before they reach users. Without this discipline, "AI features" ship as demos that degrade silently in production.

---

## When to use

- Adding an LLM call to an existing service (summarisation, classification, extraction, generation)
- Designing or implementing a RAG pipeline (retrieval-augmented generation)
- Building an agent that calls external tools via function-calling or MCP
- Setting up an eval harness for an existing or new LLM feature
- Choosing between LLM pipeline patterns (single-shot vs chain vs router vs orchestrator)
- Defining production monitoring for LLM calls (latency, cost, quality)
- Conducting prompt A/B tests before full rollout

---

## When NOT to use

- **Using AI tools to write code faster** — that is `ai-assisted-engineering`. If you are asking how to prompt Claude Code or Copilot effectively, go there.
- **Testing AI features that already exist** — that is `comprehensive-test-strategy`, which covers LLM eval-based testing in its "LLM and AI feature testing" section. Use this skill to design and build the feature; use `comprehensive-test-strategy` to define the test strategy for it.
- **Security review of AI-generated code or AI-specific threats** — that is `security-audit-secure-sdlc`, which covers prompt injection and AI supply chain risks at the threat modelling level.
- **Rule-based logic that does not need an LLM** — if the problem can be expressed deterministically (regex, structured data transformation, known schema mapping), build it without an LLM. LLMs are not the right tool for deterministic transformations.

---

## Process

### 1. Eval-driven development — start here, before the prompt

Write evals before writing the prompt. This is the discipline. Without evals, you have no signal on whether your prompt works, no baseline to protect against regressions, and no CI gate.

**Eval structure:** every eval case defines input, expected behaviour, and passing criteria. Never use exact string matching — LLM outputs are non-deterministic by design.

```python
{
    "input": "Summarize this device alert: CPU at 98% for 10 minutes",
    "passing_criteria": [
        "mentions CPU",
        "mentions duration or time",
        "does not hallucinate device IDs",
        "response under 100 tokens"
    ],
    "weight": 1.0
}
```

**Golden dataset:** minimum 20 examples before shipping. Cover:
- Happy path (typical, well-formed inputs)
- Edge cases (empty input, very long input, unexpected format, multilingual)
- Adversarial inputs (prompt injection attempts, inputs designed to confuse the model)

**LLM-as-judge:** when semantic correctness cannot be checked with a keyword or regex, use a separate LLM call to score the output against the criteria. This costs tokens — use it selectively for criteria that matter and cannot be measured programmatically.

**CI gate:** run the full eval suite on every PR that changes a prompt or model version. Fail the build if eval score drops more than 5% from the baseline on `main`. Store eval scores as CI artifacts — track the trend, not just the latest run.

See `references/eval-harness-template.py` for a working eval harness with no external framework dependencies.

---

### 2. Prompt versioning — prompts are code

Prompts belong in version control, loaded from files, not hardcoded in application source.

**Directory layout:**
```
prompts/
  alert-summarizer/
    v1.txt          — original prompt
    v2.txt          — revised prompt (never edit v1 once deployed)
  device-classifier/
    v1.txt
```

**Promotion process:**
1. Write the new prompt version in a new file (`v2.txt`).
2. Run the full eval suite against the new version. Score must meet or exceed baseline.
3. Submit for review — the eval score is part of the PR.
4. A/B test on a percentage of traffic if the change is significant.
5. Merge only after eval gate passes.

Never edit an existing version file once it has been deployed. Create a new version. This gives you an unambiguous rollback path — redeploy with the old version file.

See `references/prompt-registry-format.md` for full structure, baseline score tracking, and promotion checklist.

---

### 3. Pipeline pattern — choose before you build

Four patterns cover most LLM feature designs. Choose the pattern that matches the problem structure, not the one that is most interesting to implement.

| Pattern | When to use | Caution |
|---------|-------------|---------|
| **Single-shot** | Simple classification, extraction, summarisation. One prompt, one response. | Default choice. Do not reach for complexity. |
| **Chain** | Problem decomposes into sequential subtasks where each step's output is the next step's input. | Each step adds latency and cost. Keep chains short. |
| **Router** | Inputs have very different shapes; a classifier decides which specialised prompt handles each type. | Router accuracy becomes a bottleneck — eval the router separately. |
| **Orchestrator-worker** | Agent-style: an orchestrator LLM breaks a task into subtasks and delegates to worker LLMs or tools. | Hardest to eval and debug. Use only when simpler patterns genuinely cannot handle the task. |

**When not to use an LLM at all:** rule-based logic that can be expressed deterministically (regex, lookup tables, schema transformation), exact string matching, structured data transformation with a known schema. If you can write the logic in code, write it in code.

---

### 4. RAG — retrieval-augmented generation

Use RAG when the model needs external knowledge not in its training data: internal docs, live device state, domain-specific reference data.

**Chunking:** chunk by semantic unit (paragraph, section heading boundary), not by fixed token count. Fixed-count chunking splits sentences and breaks context. Test chunk boundaries manually on a sample of your corpus.

**Embedding model:** general-purpose models (text-embedding-3-small, nomic-embed-text) work for general English text. For domain-specific corpora (network protocols, medical terminology, legal language), evaluate a domain-specific model against your retrieval quality metric before committing.

**Retrieval quality metrics to measure:**
- **Recall@k** — does the correct chunk appear in the top-k retrieved results? Aim for recall@5 > 0.85 before connecting retrieval to the LLM.
- **MRR (mean reciprocal rank)** — on average, how high does the correct chunk rank? MRR < 0.5 means users frequently see irrelevant context first.

**Reranking:** retrieve top-20 candidates from the vector store, then rerank to top-3 before passing to the LLM. The retrieval step optimises for recall; the reranking step optimises for precision. Without reranking, noisy chunks degrade answer quality.

**Context stuffing failure:** if retrieved chunks fill the context window, do not blindly truncate. Summarise or filter lower-ranked chunks first. A truncated context produces confidently wrong answers — the model does not know it has incomplete information.

See `references/rag-design-guide.md` for chunking strategies with examples, embedding model selection criteria, and failure mode catalogue.

---

### 5. Agent tool design

When the LLM needs to call functions or APIs to complete a task:

**Each tool does exactly one thing.** No multi-purpose tools. If a tool does two things, split it — the model will hallucinate which mode to use.

**Tools must be idempotent where possible.** Design tools so retrying on failure is safe. If the tool cannot be idempotent (e.g., sending an email), make that explicit in the tool description.

**Error messages are for the model, not for humans.** The model reads your error messages and decides what to do next. Write them accordingly:
- Bad: `404 Not Found`
- Good: `No device found with ID "dev-xyz-999". Valid device IDs can be retrieved with list_devices().`

**Irreversible side effects require a confirmation gate.** Any tool that deletes data, sends external messages, or charges money must require explicit human confirmation before executing. Do not let the model trigger irreversible actions autonomously. Build the gate into the tool, not as a prompt instruction — prompt instructions can be overridden.

**Test each tool in isolation first.** Unit test the tool function before connecting it to the LLM. If the tool does not work deterministically in isolation, the agent will behave unpredictably.

---

### 6. Failure modes and mitigations

| Failure | Signal | Mitigation |
|---------|--------|------------|
| Hallucination | Outputs facts not present in the input or retrieved context | Constrain: "Answer only using the provided context. If the answer is not in the context, say so." |
| Prompt injection | User input in the prompt overwrites system instructions | Treat all user input as untrusted. Use message roles correctly (system / user / assistant). Never interpolate raw user input into the system prompt. |
| Context overflow | Truncated responses, instructions near the end of the context are ignored | Monitor token counts per request. Chunk long inputs. Test at maximum expected context length. |
| Latency spike | p95 exceeds SLO | Cache deterministic queries. Use streaming for UX. Set a hard timeout — a hung LLM call should not block your service. |
| Cost runaway | Monthly bill spikes unexpectedly | Set per-request token limits. Cache aggressively. Alert on daily cost anomalies. |

---

### 7. Production LLM monitoring

Every production LLM call must log enough to debug quality issues, track cost, and catch degradation.

**Per-request log record:**
- Request: `prompt_hash`, model, temperature, `max_tokens`, timestamp
- Response: `prompt_tokens`, `completion_tokens`, latency ms, `finish_reason`
- Outcome: eval score if applicable, user thumbs-up/down if available, error if any

**Alerts to set:**
- Latency p95 exceeds your UX SLO (set this based on what users experience, not an arbitrary number)
- Non-retryable error rate > 1%
- Daily cost exceeds budget threshold
- Eval score on sampled production traffic drops > 10% from baseline

Run evals on a sample of production traffic (not just offline golden datasets). Production inputs will surprise you. Offline evals on a golden set are necessary but not sufficient.

---

## Output format with real examples

### Completed LLM feature design entry

```
Feature: Device Alert Summarizer
Pattern: Single-shot
Model: claude-haiku-4-5 (latency-sensitive path)
Prompt: prompts/alert-summarizer/v2.txt
Eval dataset: evals/alert-summarizer/golden.jsonl (47 examples)
Baseline score: 0.91
CI gate: fail if score < 0.87 (5% drop threshold)
Latency SLO: p95 < 800ms
Cost estimate: ~$0.003 per summary at current alert volume
Monitoring: prompt_hash, token_count, latency_ms, finish_reason, score logged to telemetry
Irreversible tools: none
Human gate: N/A
```

### Prompt version registry entry (in prompts/alert-summarizer/registry.yaml)

```yaml
feature: alert-summarizer
versions:
  - version: 1
    file: v1.txt
    deployed: 2026-03-10
    eval_score: 0.84
    status: retired
  - version: 2
    file: v2.txt
    deployed: 2026-04-15
    eval_score: 0.91
    status: active
baseline_version: 2
ci_threshold: 0.87
```

### Eval result summary (CI artifact)

```json
{
  "feature": "alert-summarizer",
  "prompt_version": "v2",
  "run_date": "2026-04-20",
  "overall_score": 0.89,
  "baseline_score": 0.91,
  "delta": -0.02,
  "ci_gate": "PASS",
  "total_cases": 47,
  "failures": [
    {
      "input": "Alert: disk at 100%",
      "failed_criteria": ["mentions duration or time"]
    }
  ]
}
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] llm-app-development | outcome: OK|BLOCKED|PARTIAL | next: <what happens next> | note: <what was done>
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] llm-app-development | outcome: OK | next: code-implementer | note: Designed alert-summarizer feature; single-shot pattern; eval harness scaffolded
[2026-04-20] llm-app-development | outcome: PARTIAL | next: eval-harness review | note: RAG pipeline designed; retrieval quality not yet measured; recall@5 target set
[2026-04-20] llm-app-development | outcome: BLOCKED | next: resolve model latency | note: Orchestrator-worker pattern rejected; p95 latency exceeds 800ms SLO at current depth
```

---

## Reference files

| File | Contents |
|------|----------|
| `references/eval-harness-template.py` | Working Python eval harness with no external framework dependencies. Loads golden dataset from JSONL, runs eval cases against the LLM, scores via keyword checks and LLM-as-judge, outputs score, failure list, and CI exit code. |
| `references/prompt-registry-format.md` | How to structure the `prompts/` directory, version prompt files, track baseline scores per version, and run the promotion checklist before merging a prompt change. |
| `references/rag-design-guide.md` | Detailed RAG design guide: chunking strategies with examples, embedding model selection criteria, retrieval quality measurement (recall@k, MRR), reranking patterns, and failure mode catalogue. |
