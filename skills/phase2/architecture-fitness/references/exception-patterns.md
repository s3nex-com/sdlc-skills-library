# Exception patterns

When a fitness function violation is legitimate and the rule should not be changed, you open a formal exception. This document covers when exceptions are the right call, when they indicate the rule is wrong, and how to write a good exception entry.

---

## When an exception is legitimate

**Bootstrap and wiring code** — a `config/bootstrap.py` or `main.py` must often reach across layers to wire up the application. This is the correct place for cross-layer access; enforce it by excepting only that file, not the whole layer.

**Test fixtures** — test setup files frequently import from multiple layers. Rather than weakening the layer rule, except the `tests/fixtures/` path explicitly.

**One-off migrations** — a data migration script that imports from both `repository` and `services` to backfill data is legitimate for the duration of the migration. Set a short expiry (2–4 weeks).

**Legacy code under active refactor** — if you are moving code from `api/` into `services/` over several PRs, you may need a short-lived exception while the refactor is in progress. Expiry should match the sprint end.

---

## When the exception indicates the rule is wrong

**Multiple teams filing the same exception** — if three engineers independently except the same rule for the same layer path, the rule is wrong, not the code. Revisit the layer boundary definition.

**The "reason" field is abstract** — "technical reasons" or "needed for functionality" is not a reason. A legitimate reason names a specific constraint. If you cannot name it concretely, the exception should not exist.

**Exceptions older than their expiry** — an exception that gets renewed every quarter without the underlying issue being fixed is masking a design problem. Escalate to a design review rather than renewing.

**The excepted file grows** — if `config/bootstrap.py` gets excepted and then grows to 500 lines with business logic, the exception has been abused. Fitness rules apply to the full file, not just the wiring code.

---

## How to write a good exception entry

Required fields: `rule`, `location` (file path or package name), `reason`, `owner`, `expires`.

```yaml
exceptions:
  - rule: layer_boundary
    location: config/bootstrap.py
    reason: "Bootstrap initialises DB connection pool before adapters load; no other file in config/ is excepted"
    owner: platform-team
    expires: 2026-09-01

  - rule: layer_boundary
    location: tests/fixtures/db_helpers.py
    reason: "Test fixture accesses repository layer directly to seed state; acceptable in test context only"
    owner: any
    expires: 2027-01-01    # long expiry: test fixtures are stable

  - rule: dependency_budget
    package: boto3
    reason: "S3 adapter added Q1; evaluate moving file access to pre-signed URL proxy by Q3"
    owner: infra-team
    expires: 2026-07-01
```

**`owner`** — team or individual responsible for resolving the underlying issue before expiry. `any` is acceptable for test fixtures that are unlikely to be removed.

**`expires`** — must be a concrete date, not `null` or `never`. For truly permanent exceptions (test fixture cross-layer access), use a date 12–24 months out and review at expiry.

**`location`** — be as specific as possible. A file path is better than a directory; a directory is better than a layer name.

---

## Exception review cadence

Review all exceptions at the quarterly fitness function tune (see SKILL.md Step 5). For each exception:

1. Is the `expires` date in the past? → treat as active violation, fix or renew with updated rationale
2. Is the underlying issue resolved? → remove the exception
3. Has the excepted file grown beyond its original scope? → investigate; the exception may be masking a design problem
4. Is the `reason` still accurate? → update if the situation has changed
