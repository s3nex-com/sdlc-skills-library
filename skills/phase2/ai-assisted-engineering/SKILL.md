---
name: ai-assisted-engineering
description: >
  Activate when engineers want to use AI tools more effectively in daily work —
  coding, review, debugging, refactoring, test generation. Use when establishing
  team norms for AI tool use, reviewing AI-generated code for correctness and
  security, diagnosing why AI tool results are poor quality, or deciding which
  tasks belong to Claude vs Cursor/Copilot vs human. Applies to Claude Code,
  Cursor, GitHub Copilot, MCP integrations, and agentic coding workflows.
triggers:
  - "how do I use AI better for coding"
  - "AI-generated code review"
  - "copilot tips"
  - "cursor best practices"
  - "claude code tips"
  - "improve AI coding results"
  - "AI code quality"
  - "prompt engineering for code"
  - "AI tool norms"
  - "team AI policy"
  - "AI code security review"
  - "why is AI giving me bad code"
  - "AI test generation"
  - "review AI code"
  - "agentic coding"
  - "MCP integration"
  - "claude code workflow"
  - "trust boundary AI"
---

# AI-assisted engineering

## Purpose

AI coding tools are now core infrastructure for a small engineering team — not optional enhancements. Claude Code, Cursor, and GitHub Copilot can give a 3-5 person team the output leverage of a team twice its size, but only when used with clear trust boundaries. Without those boundaries, AI is a fast way to ship confident-looking bugs. This skill defines what each tool is for, how to write prompts that produce usable code, how to catch what AI gets wrong, and how to embed Claude as an agentic stage driver across the entire SDLC pipeline.

The frame: you are a senior engineer using AI to move faster. You are still accountable for every line you merge.

---

## When to use

- Starting a sprint and want to establish which tasks go to AI vs human
- Writing prompts for code generation and getting poor results
- Reviewing a PR where AI generated significant logic
- Setting up Claude Code or MCP integrations in the team's workflow
- Onboarding an engineer to the team's AI tool conventions
- Deciding whether a task is safe to hand to AI or needs human authorship

---

## When NOT to use

- **Implementing code from a design doc** — that is `code-implementer`. This skill governs how you use AI tools; `code-implementer` is the process that uses them.
- **Running a PR review** — that is `code-review-quality-gates`, which has its own checklist. This skill's security checklist supplements it for AI-generated code specifically.
- **Defining test strategy** — that is `comprehensive-test-strategy`. This skill covers how AI helps you execute tests, not how you design the test pyramid.
- **Security threat modelling** — that is `security-audit-secure-sdlc`. This skill covers AI-specific security risks in generated code, not full threat modelling.

---

## Process

### 1. Assign tasks to the right tool

Pick the tier before you start. Wrong tool = wrong result.

| Tool | Use for | Trust level |
|------|---------|-------------|
| **Claude Code (agentic/CLI)** | Large refactors, architecture exploration, test generation, multi-file changes, code review, ADR drafting, documentation, release notes | High output leverage, full review required |
| **Cursor / Copilot (inline)** | Autocomplete, small implementations, boilerplate, single-function generation | Low friction, review completions before accepting |
| **Human only — no AI** | Security-critical logic, cryptography, custom auth flows, novel algorithms, final PR approval | Non-delegable |

A task is human-only if: getting it wrong has a security or data-integrity consequence AND running tests alone cannot verify correctness (e.g., timing-safe comparison, key derivation).

---

### 2. Write a prompt that produces usable output

Bad prompts produce code that needs rewriting. Good prompts produce code you review. The difference is specificity.

**What every code-generation prompt needs:**
- File path and function signature (exact)
- Behaviour in plain terms: "must do X when Y, must return Z"
- Constraints: error handling style, library version, existing interfaces to match
- Test cases expected — list them, don't ask AI to decide
- What NOT to do if there is a common wrong approach

**Bad prompt:**
```
Write a function to validate a device ID.
```

**Good prompt:**
```
Write a Go function ValidateDeviceID(id string) error in internal/validator/device.go.
- Match pattern ^[a-zA-Z0-9_-]{1,64}$
- Return ErrInvalidDeviceID (defined in internal/errors/errors.go) if invalid
- Return nil if valid
- Do NOT return a boolean — the caller pattern expects error
Include a table-driven test in internal/validator/device_test.go covering:
valid ID, ID with special char (!), ID at exactly 65 chars, empty string.
```

Never ask for "best practices". Ask for "implement X that satisfies Y given constraint Z". Best-practices prompts produce generic advice disguised as code.

See `references/prompt-patterns.md` for a full collection of patterns with before/after examples.

---

### 3. Run Claude as an agentic SDLC driver

Claude Code is not just a code editor — it is an agentic tool that can drive each pipeline stage. Use it deliberately at each stage rather than only during implementation.

| Stage | Where Claude adds value | How to invoke |
|-------|------------------------|---------------|
| **Stage 1 — Define** | PRD drafting from bullet points, requirements decomposition, risk identification | `prd-creator` skill, `requirements-tracer` skill |
| **Stage 2 — Design** | Architecture alternatives with trade-offs, ADR drafting, API contract generation from spec prose | `design-doc-generator`, `architecture-decision-records` |
| **Stage 3 — Build** | Implementation from DESIGN.md, test generation, multi-file refactors | `code-implementer` skill |
| **Stage 4 — Verify** | Security scan of AI-generated code, acceptance test execution, API drift detection | `security-audit-secure-sdlc`, `executable-acceptance-verification` |
| **Stage 5 — Ship** | Release notes from git log + PR list, migration scripts, runbook generation | `release-readiness`, `documentation-system-design` |

Use `sdlc-orchestrator` to coordinate stages. Do not skip stages for non-trivial features because "AI can handle it" — it cannot handle ambiguity that upstream stages would have resolved.

---

### 4. Use MCP integrations to connect stages without leaving the terminal

MCP (Model Context Protocol) servers give Claude Code direct access to external systems. Configure the servers your team uses so Claude can act across the SDLC without manual copy-paste between tools.

**GitHub MCP** — Claude reads PR diffs, comments on PRs, creates issues, checks CI status. Eliminates context-switching between terminal and browser during review cycles.

**Slack MCP** — Claude posts standup summaries, posts release notifications, reads a channel for context before drafting a document. Useful for `stakeholder-communications` skill.

**Jira/Linear MCP** — Claude reads issue descriptions when implementing, creates subtasks, transitions issues on merge. Closes the loop between task tracking and code.

**Local filesystem MCP** — Claude reads spec files, DESIGN.md, test fixtures as live context rather than requiring you to paste them. Essential for multi-file agentic tasks.

**Setup:** MCP servers are configured in `.claude/settings.json` under `mcpServers`. Run `claude mcp list` to see active servers; `claude mcp add` to register new ones.

---

### 5. Review AI-generated code with elevated scrutiny

AI-generated code has specific failure patterns that standard PR review does not always catch. Use the checklist in `references/ai-code-review-checklist.md` for any PR where AI generated significant logic.

The four categories to focus on:

**Hallucinated APIs** — AI invents methods that do not exist in the library version you use. Verify every external method call against the official docs for your pinned version. Never trust AI's assertion about an SDK method.

**Insecure defaults** — AI frequently generates code that works but is insecure by default: `verify=False` in Python requests, wildcard CORS, debug flags left enabled, credentials in test fixtures. Search for these explicitly.

**Outdated patterns** — AI training data includes deprecated APIs and old auth patterns. Anything involving JWT handling, OAuth flows, TLS configuration, or password hashing should be verified against current library docs, not assumed correct.

**Over-permissive code** — Broad exception catches that swallow errors, unnecessary admin privileges, missing input validation at trust boundaries. AI optimises for "code that runs" not "code that fails safely".

---

### 6. Test AI-generated code with property-based tests

AI code passes the tests AI wrote. That is not a coincidence — it is a failure mode. AI generates test data that matches the happy path it implemented. Property-based testing forces the code to run against inputs AI did not anticipate.

**Standard unit tests:** verify the cases AI gave you. Necessary but not sufficient.

**Property-based tests (Hypothesis, fast-check, gopter):** define invariants and let the framework generate thousands of inputs. AI code frequently fails on inputs like: empty string where non-empty was assumed, maximum integer boundary, Unicode in an ASCII-assumed field, zero in a denominator position.

**Rule:** for any function that validates, transforms, or parses data — add at least one property-based test when AI generated the implementation. The AI will have missed an edge case. The property test will find it.

**Do not auto-accept:** run the tests before merging. "It compiles and the happy path passes" is not a review. Read the diff as if it came from a junior engineer on their first week.

---

### 7. Disclose AI use in PRs

In your PR description, note when AI generated significant logic. Not boilerplate — logic.

```
Implementation notes:
- Retry logic in internal/retry/retry.go: AI-generated, reviewed against
  the failure-mode checklist. Verified: context cancellation, max retries,
  backoff cap.
- Handler wiring in cmd/api/handlers.go: boilerplate, AI-generated.
```

Disclosure does not reduce accountability. You own the code you merge. It signals to reviewers which sections to scrutinise more carefully.

---

## Output format with real examples

### Example: good vs bad prompt

**Bad:**
```
Help me implement a retry mechanism with exponential backoff.
```

**Good:**
```
Implement a Retry[T any](ctx context.Context, fn func() (T, error), cfg RetryConfig) (T, error)
function in internal/retry/retry.go.

RetryConfig is already defined in internal/retry/config.go — match it exactly.
Requirements:
- Retry on error up to cfg.MaxAttempts times
- Backoff: cfg.BaseDelay * 2^attempt, capped at cfg.MaxDelay
- Respect ctx cancellation between attempts (return ctx.Err() if cancelled)
- Do NOT retry if the error implements IsRetryable() bool and returns false

After the implementation, list failure modes you did not handle.
```

### Example: agentic multi-stage use

```
# Terminal session

$ claude "Read DESIGN.md and implement Phase 1 (device registration endpoint).
  Tests are in internal/api/device_test.go — make them pass without changing them.
  Security: input validation must happen at the handler layer per our DESIGN.md
  security requirements section. When done, run the tests and show me the output."
```

Claude Code reads the design doc, implements the handler, runs tests, and reports results — without you leaving the terminal.

### Example: MCP-connected review

```
$ claude "Using the GitHub MCP, read PR #147 diff. Apply the AI code review checklist
  from skills/phase2/ai-assisted-engineering/references/ai-code-review-checklist.md
  and post a review comment for each issue found."
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] ai-assisted-engineering — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] ai-assisted-engineering — Established AI tool norms for new sprint; assigned tasks to tiers
[2026-04-20] ai-assisted-engineering — Reviewed AI-generated retry logic for security and correctness
[2026-04-20] ai-assisted-engineering — Configured GitHub and Jira MCP servers for agentic pipeline use
```

---

## Reference files

| File | Contents |
|------|----------|
| `references/prompt-patterns.md` | Full library of prompt templates: code generation, refactoring, debugging, test generation, review. Each with before/after examples. |
| `references/ai-code-review-checklist.md` | Checklist for reviewing AI-generated code. Covers correctness, security, tests, dependencies. Use on every PR with significant AI-generated logic. |
