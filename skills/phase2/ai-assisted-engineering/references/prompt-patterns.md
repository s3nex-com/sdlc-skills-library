# Prompt patterns for code generation

A collection of prompt templates that consistently produce usable output. Each pattern has a before/after and notes on why it works.

---

## Pattern: Specify the exact signature and constraints

Use when generating a function from scratch.

**Before (vague):**
```
Write a function to validate a device ID.
```

**After (precise):**
```
Write a Go function ValidateDeviceID(id string) error in internal/validator/device.go.
- Match pattern ^[a-zA-Z0-9_-]{1,64}$
- Return ErrInvalidDeviceID (defined in internal/errors/errors.go) if invalid
- Return nil if valid
- Do NOT return a boolean — callers expect error
Include a table-driven test in internal/validator/device_test.go covering:
valid ID, ID with special char (!), ID at exactly 65 chars, empty string.
```

**Why it works:** AI generates code that matches your actual types, error conventions, and test expectations. The vague version requires rewriting because AI guessed at all of these.

---

## Pattern: Implement to a failing test

Use when you have a test and need the implementation. Produces the most constrained, correct output.

**Template:**
```
Here is a failing test — make it pass without changing the test.

[paste test file or relevant section]

Implementation goes in [file path].
Current file contents:
[paste current file or "file does not exist yet"]

Constraints:
- [any constraints on how it must be implemented]
- [library or interface it must use]
```

**Why it works:** The test is the spec. AI cannot hallucinate behaviour that would break it. You also get immediate verification — run the test, see if it passes.

---

## Pattern: Provide the spec alongside the task

Use when implementing an endpoint, a message handler, or anything with an external contract.

**Template:**
```
Implement the [endpoint/handler/consumer] for [name].

The contract is:
[paste the relevant OpenAPI section, protobuf definition, or Avro schema]

Requirements:
- Return [status code] with [response shape] on success
- Return [status code] with our standard error envelope on validation failure
- Use [interface name] already defined in [file path]
- Input validation at the handler layer, not business logic layer

Current file: [paste or "does not exist"]
```

**Why it works:** AI generates code that matches your actual contract instead of guessing. Prevents the most common source of AI-generated endpoint bugs: hallucinating the request/response shape.

---

## Pattern: Refactoring with explicit constraints

Use when extracting, renaming, or restructuring. Unconstrained refactoring requests break callers.

**Template:**
```
Refactor [describe the change] in [file path].

Constraints:
- Must not change the public interface of [function/type]
- These tests must pass without modification: [list test names or paste test file]
- Output goes in [target file path]
- Do NOT change [specific thing AI might be tempted to change]

Current code:
[paste the function(s) to refactor]
```

**Example:**
```
Extract the retry logic from ProcessDeviceEvent into a standalone
Retry[T any](ctx context.Context, fn func() (T, error), cfg RetryConfig) (T, error)
function.

Constraints:
- Must not change ProcessDeviceEvent's public signature
- Tests in internal/processor/processor_test.go must pass without modification
- New function goes in internal/retry/retry.go
- Do NOT modify the RetryConfig struct — it is frozen

Current ProcessDeviceEvent:
[paste function]
```

---

## Pattern: Ask for failure modes after generation

Use for any code with error paths, retries, or concurrency. AI is surprisingly good at critiquing its own output.

**Template:**
```
[generate the code as normal]

After generating the code, list the failure modes you did not handle and explain why
you left them out.
```

**Why it works:** Surfaces gaps (context cancellation, partial failures, clock skew) that you can then address explicitly. Cheaper than discovering them in production.

---

## Pattern: Debugging with structured evidence

Use instead of "why is this broken?" which produces generic guesses.

**Template:**
```
Here is an error and stack trace from our [language/framework] service:

[paste error and full stack trace]

Here is the relevant code:

[paste the functions involved — not the whole file]

What are the 3 most likely causes of this error? For each cause:
1. What evidence in the stack trace or code points to it
2. How to verify it is actually the cause
3. How to fix it if confirmed
```

**Why it works:** Forces AI to reason from your actual evidence rather than enumerate all possible causes of that error type in the abstract.

---

## Pattern: Multi-file rename or migration

Use for mechanical consistency work across the codebase.

**Template:**
```
Rename [old name] to [new name] across the codebase.

Scope:
- Struct field: [file path]
- All callers: [directories to search]
- Tests: [test directories]
- Migration file: [path]

Do NOT rename [adjacent thing that should stay the same].
After making changes, list every file you modified.
```

**Why it works:** Scoping the rename explicitly prevents AI from modifying files you didn't intend (e.g., renaming a field in a shared library that other services depend on).

---

## Pattern: Generate property-based test invariants

Use to get property-based tests for functions that validate, transform, or parse.

**Template:**
```
Write property-based tests for [function name] using [Hypothesis / fast-check / gopter].

The function is:
[paste function signature and implementation]

Define at least 3 invariants:
1. A round-trip property if applicable (encode then decode = original)
2. A boundary property (output constraints hold for all valid inputs)
3. An error property (invalid inputs always produce errors, never panics)

Use realistic generators — not just strings of ASCII letters.
```

---

## Pattern: Security-focused code review

Use when you want AI to review code it or another engineer generated.

**Template:**
```
Review this code for security issues. Focus on:
1. Input validation — is all external input validated at the trust boundary?
2. Authentication and authorisation — are all paths protected?
3. Secrets and credentials — anything hardcoded or logged?
4. SQL / query injection — any string interpolation in queries?
5. Insecure defaults — verify=False, wildcard CORS, debug flags?
6. Error handling — do error messages leak internal details?

Code:
[paste code]

For each issue found: severity (Critical / High / Medium / Low), what the issue is,
and a concrete fix.
```

---

## Pattern: Release notes from git history

Use before shipping to generate a changelog without manual writing.

**Template:**
```
Generate release notes for version [version] from this git log and PR list.

Git log (since last release):
[git log --oneline vX.Y.Z..HEAD]

PR titles merged:
[list of PR titles]

Format:
## [version] — [date]
### Features
### Fixes
### Breaking changes (if any)
### Dependencies updated (if any)

Audience: engineers and technical stakeholders. No marketing language.
```
