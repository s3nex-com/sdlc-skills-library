# Implementation checklist

Apply this checklist per task, not per phase. Complete it as you go — do not batch it at the end.

---

## Before starting a task

- [ ] The task has no incomplete dependencies
- [ ] The relevant spec section has been read (OpenAPI path, Protobuf service, AsyncAPI channel)
- [ ] The relevant acceptance criteria (BDD Given/When/Then) have been read
- [ ] Any open design questions (DQ-NNN) that affect this task are resolved
- [ ] The security gate requirements for this task are understood (see `security-audit-secure-sdlc`)

---

## During implementation

### Spec compliance
- [ ] Every request parameter matches the spec schema (name, type, required/optional)
- [ ] Every response body matches the spec schema (structure, field names, types)
- [ ] All documented status codes are returned for their documented conditions
- [ ] No undocumented endpoints, parameters, or response fields are introduced

### Code quality
- [ ] Function and variable names communicate intent without requiring a comment
- [ ] No function exceeds a single responsibility (if a comment is needed to explain what it does, split it)
- [ ] No hardcoded values — environment variables or config for anything environment-specific
- [ ] No dead code — no commented-out blocks, no unreachable paths
- [ ] Error paths are explicit — no silent failures, no swallowed exceptions
- [ ] Every error response includes appropriate context for the caller (not internal details)
- [ ] Resource lifecycle managed — connections closed, goroutines cancelled, file handles released

### Security (do not defer)
- [ ] Input validation at every trust boundary (HTTP handler, event consumer, file ingestion)
  - [ ] Type validation (reject wrong types, not just coerce them)
  - [ ] Range validation (length limits, numeric bounds)
  - [ ] Format validation (UUIDs, emails, dates — reject malformed values)
  - [ ] Allowlist for enum-like fields (reject unexpected values)
- [ ] Authentication verified before any business logic executes
- [ ] Authorisation checked: does this caller have permission for this resource?
- [ ] Tenant isolation: multi-tenant system queries scoped to the caller's tenant at the query level, not just the application level
- [ ] No SQL injection: parameterised queries or ORM used throughout (no string concatenation in queries)
- [ ] No NoSQL injection: sanitised inputs to document store queries
- [ ] Secrets not in source code, not in logs, not in error responses
- [ ] Sensitive field values not logged (PII, tokens, passwords)
- [ ] Stack traces not returned in API error responses

### Database
- [ ] Queries use indexes for the access pattern (verify with EXPLAIN if in doubt)
- [ ] Transactions used where multiple writes must be atomic
- [ ] Connection pool used — no per-request connection creation
- [ ] Migrations are additive (new table or new nullable column) or explicitly planned for backward compatibility
- [ ] Migration is reversible (rollback is possible without data loss)

### Observability
- [ ] Structured log statements at entry and exit of significant operations
- [ ] Log includes correlation ID / request ID for traceability
- [ ] Metrics emitted for latency-sensitive or high-volume operations
- [ ] Error conditions logged with enough context to diagnose without a debugger

---

## After implementing a task — before marking complete

### Tests
- [ ] Unit tests written for all new functions (happy path + primary error paths)
- [ ] Integration test written for the component interaction (handler + DB, service + queue, etc.)
- [ ] Contract test written for each new API endpoint (validates response against OpenAPI spec)
- [ ] BDD acceptance scenario for this task's story runs and passes
- [ ] No tests skip silently — skipped tests have a documented reason

### Review
- [ ] Self-reviewed: read the implementation as if reviewing someone else's code
- [ ] No temporary code remains (TODOs that were meant to be removed, debug log statements)
- [ ] Implementation matches the design doc — or a deviation is documented

### Documentation
- [ ] If the implementation reveals a design doc error: DESIGN.md is updated or a DQ is raised
- [ ] If a significant implementation decision was made: ADR is created or implementation notes updated
- [ ] `docs/implementation-status.md` updated: task marked Complete

---

## Common mistakes to avoid

| Mistake | Consequence | Prevention |
|---------|-------------|-----------|
| Writing tests after the feature is "done" | Tests that verify implementation details, not behaviour | Write tests alongside, not after |
| Ignoring the spec and implementing from memory | Schema drift, contract violations | Read the spec before implementing each endpoint |
| Silently implementing extra functionality | Scope creep, untested paths, security surface expansion | Only implement what the design doc specifies |
| Deferring security validation to "later" | Security debt that is expensive to retrofit | Apply security checklist at each task |
| Implementing Phase 2 scope during Phase 1 | Untested dependencies, gate failures, schedule pressure | Strict phase scope adherence |
| Not committing frequently | Large diffs that are hard to review | Commit per logical unit of work, not per phase |
| Assuming a design question has an obvious answer | Design drift, integration failures | Raise DQ, get answer, then implement |
