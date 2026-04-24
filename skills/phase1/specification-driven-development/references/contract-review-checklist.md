# Contract review checklist

Use this checklist before freezing any API contract. Mark each item: ✅ Pass | ⚠️ Concern | ❌ Fail | N/A

---

## Section 1: Completeness (does the spec cover everything needed?)

| # | Check | Severity if fails |
|---|-------|-------------------|
| 1.1 | Every endpoint that will be implemented is described in the spec | Critical |
| 1.2 | Every request parameter (path, query, header) is documented with type, constraints, and description | High |
| 1.3 | Every request body field is documented — type, required/optional, constraints, description | High |
| 1.4 | Every response field is documented — type, always-present vs conditional, description | High |
| 1.5 | Every error scenario that can occur at runtime has a defined error response | High |
| 1.6 | At minimum: 400/422, 401, 403, 500 responses are defined for all authenticated endpoints | Critical |
| 1.7 | 404 is defined for all operations that address a specific resource by ID | High |
| 1.8 | 429 (rate limiting) is defined for rate-limited endpoints | Medium |
| 1.9 | Authentication requirements are specified for every operation | Critical |
| 1.10 | Pagination is defined for all list/collection endpoints | High |

---

## Section 2: Consistency

| # | Check | Severity if fails |
|---|-------|-------------------|
| 2.1 | Error response schema is consistent across all operations (same schema, same fields) | High |
| 2.2 | Naming conventions are consistent: camelCase for JSON fields, kebab-case for URL paths | Medium |
| 2.3 | HTTP methods are used semantically correctly: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove) | High |
| 2.4 | HTTP status codes are used semantically correctly: 200 (success + body), 201 (created), 202 (accepted async), 204 (no content) | High |
| 2.5 | Date/time fields all use the same format (recommend: ISO 8601 / `date-time` format) | High |
| 2.6 | ID fields all use the same format (UUID, or project-defined format consistently applied) | Medium |
| 2.7 | Boolean field naming is consistent (e.g., all start with `is_` or `has_`) | Low |
| 2.8 | Collection responses have a consistent envelope (e.g., `{"items": [...], "total": N}`) | Medium |

---

## Section 3: Error handling

| # | Check | Severity if fails |
|---|-------|-------------------|
| 3.1 | Every validation error response includes the specific field that failed validation | High |
| 3.2 | Error codes are machine-readable strings, not human-readable messages that may change | High |
| 3.3 | A `request_id` field is included in all error responses for log correlation | Medium |
| 3.4 | Error messages are sanitised — no stack traces, database errors, or internal paths in error responses | Critical |
| 3.5 | The spec documents what consumers should do when they receive each error type (retry? contact support? fix the request?) | Medium |

---

## Section 4: Versioning

| # | Check | Severity if fails |
|---|-------|-------------------|
| 4.1 | The API version is explicit in the spec (in `info.version`) | High |
| 4.2 | The major version is present in the URL path (e.g., `/v1/`) | High |
| 4.3 | The versioning strategy is documented (when will the version increment? what constitutes a breaking change?) | Medium |
| 4.4 | Deprecated operations or fields are marked with `deprecated: true` and include a sunset date | Medium |

---

## Section 5: Security

| # | Check | Severity if fails |
|---|-------|-------------------|
| 5.1 | Authentication scheme is defined in `components/securitySchemes` | Critical |
| 5.2 | Security requirements are applied globally or individually to every operation | Critical |
| 5.3 | Endpoints that are intentionally unauthenticated are explicitly marked with an empty security array `security: []` and have a comment explaining why | High |
| 5.4 | Sensitive fields (tokens, passwords, secrets) are not included in request/response schemas that would cause them to appear in logs | Critical |
| 5.5 | Rate limiting behaviour is documented | Medium |

---

## Section 6: Documentation quality

| # | Check | Severity if fails |
|---|-------|-------------------|
| 6.1 | Every operation has a `summary` (one line) and `description` (meaningful detail) | High |
| 6.2 | Every field has a `description` that explains semantics, not just restates the field name | High |
| 6.3 | Every operation has at least one realistic `example` in the request body | High |
| 6.4 | Every operation has at least one example in the success response | Medium |
| 6.5 | Async operations clearly state they are asynchronous and how the caller learns the result | High |
| 6.6 | Idempotency behaviour is documented for operations that support it | Medium |
| 6.7 | The spec has been spell-checked and uses consistent capitalisation in descriptions | Low |

---

## Review summary

**Total items checked:** 37
**Pass:** ___ | **Concern:** ___ | **Fail:** ___ | **N/A:** ___

**Critical failures (block freeze):** ___
**Overall recommendation:** Ready to freeze / Needs revision / Major issues

**Reviewer:** [Name, Company]
**Review date:** [date]
