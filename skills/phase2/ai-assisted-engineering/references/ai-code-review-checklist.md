# AI code review checklist

Use this checklist on every PR where AI generated significant logic — not just boilerplate handler wiring or format conversions, but actual business logic, error handling, security controls, or concurrency.

This supplements your standard PR review process (`code-review-quality-gates` skill). It covers the specific failure patterns that AI introduces that human reviewers often miss because the code looks plausible.

---

## Section 1: Hallucinated APIs

AI confidently uses methods that do not exist in the library version your project pins.

- [ ] Every external library method call verified against official docs for the **pinned version** — not the latest docs, not AI's assertion
- [ ] No methods called on types that do not have those methods in your version (check with `go doc`, `pydoc`, IDE type checker)
- [ ] No parameters passed in an order or type that differs from the actual signature
- [ ] No deprecated methods used that were removed in a version after AI's training data (check the library changelog if anything looks old)

**How to check:** For Go, `go build` catches most of these. For Python, run `mypy` or check in the REPL. Never assume a method exists because AI used it.

---

## Section 2: Insecure defaults

AI generates code that runs correctly but is insecure by default. These are the most common patterns.

- [ ] **TLS verification:** No `verify=False` (Python requests), `InsecureSkipVerify: true` (Go), `rejectUnauthorized: false` (Node)
- [ ] **CORS:** No wildcard origin (`*`) on routes that carry authentication or sensitive data
- [ ] **Debug flags:** No debug mode, verbose logging of request bodies, or stack traces exposed to callers in non-development code
- [ ] **Credentials in code:** No hardcoded tokens, passwords, API keys, or private keys — including in test fixtures and example data
- [ ] **Auth bypasses:** No `if os.Getenv("SKIP_AUTH") == "true"` or equivalent left over from development
- [ ] **Broad permissions:** No IAM policies, RBAC roles, or filesystem permissions that are more permissive than required
- [ ] **HTTP timeouts:** No HTTP clients created without explicit timeouts (AI frequently omits these)
- [ ] **Default passwords/users:** No default credentials in DB setup scripts, container configs, or seeding code

---

## Section 3: Outdated patterns

AI training data includes deprecated APIs, old auth patterns, and old library idioms. These compile and run but are insecure or unmaintained.

- [ ] **Password hashing:** bcrypt, scrypt, or Argon2 — not MD5, SHA1, or SHA256 alone
- [ ] **JWT handling:** Using a maintained library with signature verification — not custom parsing or `none` algorithm acceptance
- [ ] **OAuth flows:** PKCE for public clients, not implicit flow (deprecated in OAuth 2.1)
- [ ] **TLS config:** TLS 1.2+ minimum, no deprecated cipher suites
- [ ] **Crypto primitives:** AES-GCM not AES-CBC/ECB, ECDH not DH, Ed25519 not RSA-1024
- [ ] **Library versions:** Any library pinned to a version with known CVEs? Run `govulncheck`, `pip-audit`, `npm audit`

---

## Section 4: Over-permissive and unsafe code

AI optimises for code that runs, not code that fails safely.

- [ ] **Exception/error catches:** No bare `except Exception`, `catch (e: Exception)`, or `catch (_)` that swallows all errors silently
- [ ] **Input validation:** All external input validated at the trust boundary (HTTP handler, message consumer entry point) — not only in business logic
- [ ] **SQL injection:** No string interpolation or concatenation in SQL queries — parameterised statements only
- [ ] **Path traversal:** File path operations that include user input must sanitise against `../` traversal
- [ ] **Error messages:** Error responses do not include stack traces, internal file paths, SQL query text, or system details
- [ ] **Goroutine/thread leaks:** All goroutines have a cancellation path — no goroutines started with no way to stop them
- [ ] **Resource cleanup:** All file handles, DB connections, HTTP response bodies closed on all paths including error paths

---

## Section 5: Test quality

AI generates tests that pass. That is not the same as tests that verify behaviour.

- [ ] **Assertions are meaningful:** `assert result == expected_value` not `assert result is not None` or `assert err == nil`
- [ ] **Test data is realistic:** Not just `"test"`, `0`, `[]`, `"device"` everywhere — use values that exercise real conditions
- [ ] **Mock expectations are specific:** Mocks assert what was called with what arguments, not just that they were called at all
- [ ] **Negative tests verify the failure:** Error-path tests assert the specific error returned, not just that an error occurred
- [ ] **Edge cases present:** At least one test for empty input, maximum-size input, and boundary values — these are what AI misses
- [ ] **Suspiciously high coverage:** If coverage is unusually high for the code complexity, check whether assertions are substantive or trivially passing

---

## Section 6: Dependencies

Quick check — do not skip.

- [ ] No new imports that were not in the approved design or discussed in the PR
- [ ] Any new dependency has a known maintainer, recent commits, and no critical CVEs
- [ ] No dependency added that duplicates functionality already in an existing dependency

---

## Quick reference: most common AI-generated bugs by category

| Category | Most common AI mistake |
|----------|----------------------|
| HTTP clients | Missing timeout, TLS verify disabled |
| Auth | Hardcoded credential in test, missing auth check on new endpoint |
| Database | N+1 query in a loop, missing index, wrong transaction boundary |
| Concurrency | Goroutine leak, mutex scope wrong, WaitGroup misuse |
| Error handling | Error swallowed with `_`, cleanup missing on error path |
| Tests | Trivial assertion (`!= nil`), mock accepts any args |
| Crypto | Wrong algorithm (MD5/SHA1), custom IV/nonce logic |
| APIs | Method exists in latest docs but not in pinned version |

When in doubt on any security item: reject and ask a teammate before merging.
