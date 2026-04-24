---
name: comprehensive-test-strategy
description: >
  Activate when designing or evaluating a testing strategy, defining test pyramid ratios,
  writing test plans for a release, establishing acceptance test frameworks using
  BDD/Given-When-Then, setting up contract testing between services, designing performance
  and load test scenarios, defining test environment strategy, or determining what constitutes
  "done" for a feature. Also trigger when integration tests are failing and the cause is
  unclear, or when test execution time is blocking delivery velocity.
---

# Comprehensive test strategy

## Purpose

Testing is the engineering team's primary mechanism for building justified confidence in software. A clear test strategy means everyone on the team agrees on what "tested" means before code ships — not after a bug is found in production.

---

## When to use

- A new service or feature is being built and the test strategy (pyramid ratios, types, coverage targets) needs to be established before coding starts
- Integration tests are failing and it is unclear whether the issue is test design, flakiness, or a real regression
- The test suite is slow and blocking delivery velocity
- The team needs to agree on what "tested" means for a feature before anyone starts writing code
- A property-based testing strategy is needed for logic with complex input spaces
- LLM or AI features need an eval-based testing approach designed
- A test data management strategy is needed (factories, builders, database isolation)

## When NOT to use

- Writing and executing BDD acceptance tests from the traceability matrix — use `executable-acceptance-verification`.
- Running load, stress, or soak tests and setting performance NFRs — use `performance-reliability-engineering`.
- Designing eval harnesses for LLM-powered features — use `llm-app-development`.
- Runtime contract conformance between services (Pact, schema registry) — use `api-contract-enforcer`.
- Fault injection and resilience validation — use `chaos-engineering`.
- Defining coverage gates enforced in CI pipelines — use `devops-pipeline-governance` for the gate, this skill for the strategy behind it.

---

## Process

### Defining a test strategy

1. Identify the service type: logic-heavy (needs more unit tests), data-heavy (needs more integration tests), API surface (needs contract tests), user-facing (needs acceptance tests). Adjust pyramid ratios to fit.
2. Define the agreed ratios for this service: unit / integration / E2E. Write them down — ambiguity here causes disagreements later.
3. Define coverage targets per layer. Coverage is not a vanity metric: every BDD scenario must have a corresponding passing test; every critical business logic path must have a unit test.
4. Define test environment strategy: local, CI, staging, performance. Confirm no production data flows to lower environments.
5. Define the test data approach: factories/builders for domain objects, database isolation strategy (transaction rollback, per-test schema, or shared read-only fixtures).
6. For LLM features: define the eval-based strategy — golden dataset location, eval criteria format, CI eval threshold, and how to handle non-determinism.

### Diagnosing failing or slow tests

7. For intermittent failures: identify if the root cause is external dependency (network, DB), state leakage between tests, or genuine non-determinism.
8. For slow suites: identify which layer is slow. Unit tests taking > 1 second each are a smell. Integration tests using real infrastructure can be parallelised.
9. Produce a short finding and recommendation.

### Output

10. Document the test strategy as a brief section in the design doc or as a standalone test plan.
11. Append the execution log entry.

## Test pyramid

The test pyramid describes the distribution of test types by quantity and cost. Invert this pyramid and you get slow, brittle, expensive tests that do not catch regressions early.

```
          /\
         /  \   E2E / Acceptance tests
        /    \  (fewest — slow, expensive, catch integration gaps)
       /------\
      /        \ Integration tests
     /          \ (moderate — test service boundaries)
    /------------\
   /              \ Unit tests
  /                \ (many — fast, cheap, test logic)
 /------------------\
```

### Recommended ratios

| Layer | Proportion | Notes |
|-------|------------|-------|
| Unit | 70% | Fast, isolated, deterministic. Tests functions, classes, modules. |
| Integration | 20% | Tests interactions between components (service + DB, service + cache, service + queue) |
| E2E / Acceptance | 10% | Tests complete user journeys or contract acceptance criteria |

These ratios are guidelines. Data-heavy services with little logic may have fewer unit tests. Services with complex inter-service interactions may have more integration tests. The principle is: catch problems at the cheapest possible layer.

---

## Test layers defined

### Unit tests

**What they test:** Individual functions, methods, or classes in isolation. External dependencies (databases, APIs, queues) are replaced with test doubles.

**Characteristics:**
- Run in < 1ms per test; full suite in < 60 seconds
- No network calls, no file I/O, no random data
- Deterministic: same input always produces same result
- Each test has exactly one reason to fail

**When to mock vs not mock:**
- Mock external service calls (HTTP, gRPC, database, queue)
- Do NOT mock the code under test itself
- Do NOT mock your own domain logic — if you feel the urge to mock your own service, it is a sign the design needs to be refactored
- Use real objects where constructing them is cheap and straightforward

```python
# Good unit test — tests business logic, mocks external dependency
def test_reject_event_with_future_timestamp(mock_device_registry):
    mock_device_registry.is_registered.return_value = True
    service = IngestionService(mock_device_registry)

    future_time = datetime.utcnow() + timedelta(hours=25)
    with pytest.raises(ValidationError, match="timestamp must be within 24 hours"):
        service.validate_event(device_id="dev-001", timestamp=future_time)

    mock_device_registry.is_registered.assert_called_once_with("dev-001")
```

### Integration tests

**What they test:** The interaction between two or more components, typically a service and one of its dependencies (real database, real message queue, real cache).

**Characteristics:**
- Use real infrastructure (often spun up via Docker Compose or testcontainers)
- Slower than unit tests (seconds per test)
- Each test verifies a specific integration boundary works correctly
- Test data isolated per test (transaction rollback or per-test database seeding)

```python
# Integration test — tests against real PostgreSQL via testcontainers
@pytest.fixture(scope="session")
def postgres_db(docker_services):
    # Starts a PostgreSQL container for the test session
    return create_test_database(docker_services.port_for("postgres", 5432))

def test_store_and_retrieve_telemetry_event(postgres_db):
    repo = EventRepository(postgres_db)
    event = TelemetryEvent(device_id="dev-001", event_type="temperature", value=25.5)

    event_id = repo.store(event)
    retrieved = repo.get(event_id)

    assert retrieved.device_id == "dev-001"
    assert retrieved.event_type == "temperature"
```

### Property-based testing

**What it tests:** Invariant properties that must hold for any valid input — not just the examples a developer thought of. A property-based test generates hundreds of random inputs and verifies a stated property holds for all of them.

**When to use:** Functions with complex input spaces, serialisation/deserialisation round-trips, idempotency verification, any logic where "all valid inputs" can be described but individual examples are insufficient.

**Use Hypothesis (Python) or fast-check (TypeScript) as the testing framework.**

```python
# Hypothesis example: serialisation round-trip property
from hypothesis import given, strategies as st
from hypothesis.strategies import composite

@given(
    device_id=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoints=1),
        min_size=1,
        max_size=64
    ),
    event_type=st.sampled_from(["temperature_reading", "pressure_reading", "heartbeat"]),
    value=st.floats(min_value=-273.15, max_value=9999.99, allow_nan=False)
)
def test_telemetry_event_serialisation_round_trip(device_id, event_type, value):
    """Property: serialise → deserialise produces an equal event for all valid inputs."""
    event = TelemetryEvent(device_id=device_id, event_type=event_type, value=value)
    assert TelemetryEvent.from_json(event.to_json()) == event


# Hypothesis example: idempotency property
@given(
    event=st.builds(TelemetryEvent, ...),
    idempotency_key=st.uuids().map(str)
)
def test_ingest_is_idempotent(ingestion_service, event, idempotency_key):
    """Property: ingesting the same event twice produces exactly one stored event."""
    event.idempotency_key = idempotency_key
    result_1 = ingestion_service.ingest(event)
    result_2 = ingestion_service.ingest(event)

    assert result_1.event_id == result_2.event_id
    assert len(ingestion_service.get_by_idempotency_key(idempotency_key)) == 1
```

**What to put in property tests vs unit tests:**
- Property tests: round-trips, invariants, idempotency, monotonicity ("adding an item never decreases the count"), commutativity
- Unit tests: specific business rules, error messages, specific edge cases you know about
- Both are needed — property tests find the unknown unknowns; unit tests document the known requirements.

**Start small:** write one property test per critical invariant. Ten well-chosen properties are more valuable than a hundred specific examples for logic with large input spaces.

### Contract tests

**What they test:** That a service consumer and provider agree on the API contract. Run by both companies independently, giving each confidence that the contract is honoured.

**Use Pact or a similar consumer-driven contract testing framework.** The consumer defines what it expects; the provider verifies it can honour those expectations. Run by consumer and provider independently so each has confidence the contract is honoured.

```python
# Consumer side — defines what the consumer expects
@consumer("ingestion-service")
@provider("device-registry-api")
def test_device_validation_contract(pact):
    (pact
     .given("device dev-001 is registered")
     .upon_receiving("a request to validate device dev-001")
     .with_request("GET", "/devices/dev-001/status")
     .will_respond_with(200, body={"device_id": "dev-001", "status": "active"}))

    with pact:
        result = DeviceRegistryClient(pact.uri).get_status("dev-001")
    assert result.status == "active"
```

The consumer publishes the contract (pact file) to a shared Pact Broker. The provider runs contract verification tests in their CI pipeline.

### Acceptance tests

**What they test:** Complete business scenarios from end to end, written in terms of business behaviour (BDD). These are the tests that prove a requirement is met.

Acceptance tests are co-authored with the product/business representative. They define "done."

```gherkin
Feature: Telemetry event ingestion
  Background:
    Given device "dev-001" is registered in the device registry

  Scenario: Successfully ingest a valid telemetry event
    Given I have a valid API key for device "dev-001"
    When I POST a telemetry event with:
      | field      | value                   |
      | device_id  | dev-001                 |
      | event_type | temperature_reading     |
      | timestamp  | 2024-01-15T10:00:00Z    |
      | value      | 23.5                    |
    Then the response status is 202
    And the response body contains an event_id
    And the event is published to the Kafka topic within 5 seconds

  Scenario: Reject telemetry from an unregistered device
    Given I have a valid API key for device "dev-999"
    And device "dev-999" is not registered
    When I POST a telemetry event for device "dev-999"
    Then the response status is 422
    And the error code is "DEVICE_NOT_REGISTERED"
```

---

## Performance and load testing

Performance tests verify that the system meets its NFRs under load. They are not a replacement for load testing in production but are a gate before production.

### Performance test types

Two types cover most situations. Add others only when a specific NFR demands it.

| Type | Purpose | When to run |
|------|---------|-------------|
| Smoke | Verify the system works at minimal load (1 user) after deployment | Every deployment to staging |
| Load | Verify NFRs are met at expected peak load | Before each production release |

If you have a specific need beyond these two (memory leak detection, spike tolerance, breaking point), add a targeted test for that scenario — do not run all five types as a matter of course.

### Load test scenario: ingestion API

```javascript
// k6 load test — ingestion API
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '5m', target: 100 },   // Hold at 100 users (normal load)
    { duration: '2m', target: 500 },   // Spike to 500 users
    { duration: '5m', target: 500 },   // Hold at 500 users (peak load)
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(99)<500', 'p(50)<100'],  // NFR: p99 < 500ms
    'http_req_failed': ['rate<0.001'],                 // NFR: < 0.1% error rate
  },
};

export default function () {
  const payload = JSON.stringify({
    device_id: `dev-${Math.floor(Math.random() * 1000)}`,
    event_type: 'temperature_reading',
    timestamp: new Date().toISOString(),
    payload: { temperature: (Math.random() * 50).toFixed(1) },
  });

  const res = http.post(`${__ENV.BASE_URL}/v1/events`, payload, {
    headers: { 'Content-Type': 'application/json', 'X-API-Key': __ENV.API_KEY },
  });

  check(res, {
    'status is 202': (r) => r.status === 202,
    'has event_id': (r) => r.json('event_id') !== undefined,
  });

  sleep(1);
}
```

---

## LLM and AI feature testing

AI features need a different testing approach. LLM outputs are non-deterministic — the same prompt can return different text on each run. Prompts are code — they break silently when models update, when temperature changes, or when the context window shifts. Evaluation requires both automated scoring and human judgment; neither alone is sufficient.

### Why standard testing patterns break

- **Exact string matching fails.** Two outputs can be semantically identical but textually different. `assert output == expected_string` is wrong for LLM output.
- **Prompts break silently.** A model update or prompt rewrite can degrade quality without raising an exception. Nothing fails; quality just quietly drops.
- **Flakiness is structural.** At temperature > 0, the same test can pass and fail on different runs. You need a strategy that handles this, not just retries.

### Eval-based testing (primary pattern)

Evals replace unit tests as the primary quality mechanism for LLM features. An eval defines the input and the expected *behaviour* — not the expected *string*.

**Golden dataset format:**

```python
eval_case = {
    "input": "Summarize this device telemetry: ...",
    "passing_criteria": [
        "mentions latency anomaly",
        "response under 200 tokens",
        "no hallucinated device IDs"
    ]
}
```

Each criterion is a testable property, not an exact match. Criteria examples:
- Contains a required concept ("mentions latency anomaly")
- Structural constraint ("response under 200 tokens", "always returns valid JSON")
- Safety property ("no hallucinated device IDs", "never discloses credentials")

**LLM-as-judge:** When semantic correctness is needed and regex/heuristics are insufficient, use a second LLM call to evaluate the output against the criteria. This is slower and costs tokens — use it selectively for criteria that cannot be checked programmatically.

**Tracking eval scores in CI:**
- Run the full eval suite on every PR that changes a prompt or model version
- Store eval scores as CI artifacts (JSON file per run, not just pass/fail)
- Fail the CI check if any eval score drops > 5% relative to the baseline on `main`
- Review eval score trends weekly — a slow drift is as dangerous as a sudden drop

### Prompt regression testing

Prompts are versioned artifacts. They belong in version control, loaded from files or a prompt registry — not hardcoded in application code.

Rules:
1. **Prompts in files, not strings.** `prompts/summarise_telemetry.md`, not `PROMPT = "Summarize this..."` buried in a function.
2. **Run eval suite on every prompt change** before merging. A prompt change with no eval run is the same as code with no tests.
3. **A/B test prompt changes** on a sample of real inputs before full rollout. Compare eval scores between old and new prompt versions; the new version ships only if it matches or improves baseline scores.

### Non-determinism handling

| Scenario | Strategy |
|----------|----------|
| Deterministic output needed (structured extraction, JSON output) | Set `temperature=0`. Outputs are stable. |
| Creative or varied output (summaries, explanations) | Test behavioural invariants, not exact strings. |
| Multi-run flakiness detection | Run the same prompt 3 times; if outputs differ significantly by the eval criteria, flag for human review — do not auto-fail. |

**Behavioural invariants to test** (instead of exact string matching):
- Always responds in valid JSON
- Always includes required fields (`device_id`, `event_type`)
- Never produces output matching a harmful content pattern
- Response length within expected range
- Sentiment or tone classification is stable across runs

```python
# Behavioural invariant test — not exact match
def test_telemetry_summary_is_valid_json(llm_client):
    response = llm_client.complete(prompt=SUMMARISE_PROMPT, input=SAMPLE_TELEMETRY)
    parsed = json.loads(response)  # Fails if not valid JSON
    assert "summary" in parsed
    assert "anomalies" in parsed
    assert isinstance(parsed["anomalies"], list)
```

### Tool use and agent behaviour testing

When LLMs use tools (function calling, MCP, ReAct loops), test each layer independently before testing the full agent.

**Unit test each tool function independently** — the tool itself must work correctly before testing whether the agent calls it.

**Integration test the agent's tool selection and chaining:**

| What to test | How |
|-------------|-----|
| Tool selection | Given a prompt that clearly requires Tool A, verify Tool A is called |
| Tool chaining | Tool A output fed to Tool B; verify the pipeline produces correct final output |
| Tool failure handling | Return an error from the tool; verify the agent handles it gracefully (retry, fallback, or honest failure — not hallucination) |
| Empty tool results | Return `[]` or `null`; verify the agent says "no results found", not fabricates data |
| Unexpected tool output format | Return a schema mismatch; verify the agent does not silently produce garbage output |

**Boundary conditions for agent tests:**
- What does the agent do when all tools return errors?
- Does it loop indefinitely or does it have a max-iterations guard?
- Does it expose tool error details to the user (security concern) or handle them internally?

### Eval dataset management

- Store golden eval datasets in `tests/evals/` as versioned JSON or YAML files
- Each dataset file covers one feature or prompt variant
- When adding a new LLM feature, the first PR must include at least 10 eval cases
- Eval cases must cover: happy path, edge inputs (empty, very long, unexpected format), and at least one safety property

**Minimal eval harness (portable — no framework dependency):**

```python
import json

def run_eval(eval_cases: list[dict], model_fn) -> dict:
    results = []
    for case in eval_cases:
        output = model_fn(case["input"])
        passed = []
        failed = []
        for criterion in case["passing_criteria"]:
            # Replace with your criterion checker — regex, LLM-as-judge, or heuristic
            ok = check_criterion(output, criterion)
            (passed if ok else failed).append(criterion)
        results.append({
            "input": case["input"],
            "output": output,
            "passed": passed,
            "failed": failed,
            "score": len(passed) / len(case["passing_criteria"])
        })
    overall_score = sum(r["score"] for r in results) / len(results)
    return {"overall_score": overall_score, "cases": results}
```

This harness is framework-agnostic. Swap in any LLM client for `model_fn` and any criterion checker for `check_criterion`. Track `overall_score` in CI.

---

## Test data management

Poorly managed test data is one of the most common sources of flaky tests and slow test suites. Clean, consistent test data is part of the test strategy — not an afterthought.

### Principles

1. **Each test owns its data.** Tests should not depend on data created by other tests. Test data is created at test start and cleaned up at test end (or via transactions).
2. **No production data in tests.** Test environments use synthetic or anonymised data only. PII must never appear in test fixtures.
3. **Test data reflects real domain constraints.** `"test"` string and `0` integer everywhere produces tests that pass for the wrong reasons. Use realistic values that respect domain rules (valid timestamps, proper device ID formats, realistic sensor ranges).
4. **Fast construction, easy customisation.** Use builders or factories so tests specify only the fields they care about, with sensible defaults for everything else.

### Factory pattern (Python)

```python
import factory
from factory import LazyFunction, Sequence
from datetime import datetime, timezone

class TelemetryEventFactory(factory.Factory):
    class Meta:
        model = TelemetryEvent

    device_id = Sequence(lambda n: f"dev-{n:04d}")
    event_type = "temperature_reading"
    timestamp = LazyFunction(lambda: datetime.now(timezone.utc))
    value = 23.5
    idempotency_key = LazyFunction(lambda: str(uuid.uuid4()))

# In tests — only specify what you care about
def test_reject_future_timestamp():
    event = TelemetryEventFactory(timestamp=datetime(2099, 1, 1, tzinfo=timezone.utc))
    with pytest.raises(ValidationError, match="timestamp must be within 24 hours"):
        service.validate_event(event)
```

### Builder pattern (TypeScript)

```typescript
class TelemetryEventBuilder {
  private event: Partial<TelemetryEvent> = {
    deviceId: "dev-0001",
    eventType: "temperature_reading",
    timestamp: new Date().toISOString(),
    value: 23.5,
  };

  withDeviceId(id: string): this { this.event.deviceId = id; return this; }
  withTimestamp(ts: string): this { this.event.timestamp = ts; return this; }
  withFutureTimestamp(): this { 
    this.event.timestamp = new Date(Date.now() + 86400000 * 2).toISOString(); 
    return this; 
  }

  build(): TelemetryEvent { return this.event as TelemetryEvent; }
}

// Usage
const event = new TelemetryEventBuilder().withFutureTimestamp().build();
```

### Database test isolation strategies

| Strategy | When to use | Trade-offs |
|----------|-------------|-----------|
| Transaction rollback | Unit/integration tests with a single DB connection | Fast; doesn't work with multiple connections or async |
| Truncate between tests | Integration tests; full cleanup needed | Slower but reliable; works with any setup |
| Per-test schema (testcontainers) | Full isolation per test; CI environments | Slowest; best isolation; use for critical integration scenarios |
| Shared fixtures (session-scoped) | Read-only data (lookup tables, reference data) | Fast; only for data tests never mutate |

```python
# Transaction rollback pattern (pytest)
@pytest.fixture
def db_session(postgres_db):
    """Provides a DB session that rolls back after each test."""
    connection = postgres_db.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

### Synthetic data for time-series and IoT workloads

For services dealing with device telemetry, generating realistic synthetic data matters:

```python
import random
from datetime import datetime, timezone, timedelta

def generate_device_telemetry_stream(
    device_id: str,
    num_events: int,
    start_time: datetime = None,
    interval_seconds: int = 60,
    base_value: float = 23.0,
    noise_range: float = 2.0
) -> list[TelemetryEvent]:
    """
    Generates a realistic telemetry stream with natural variation.
    Values follow a random walk, not pure noise — more realistic for sensors.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(seconds=num_events * interval_seconds)

    events = []
    current_value = base_value
    for i in range(num_events):
        current_value += random.gauss(0, noise_range / 3)
        current_value = max(base_value - noise_range * 2, min(base_value + noise_range * 2, current_value))
        events.append(TelemetryEvent(
            device_id=device_id,
            event_type="temperature_reading",
            timestamp=start_time + timedelta(seconds=i * interval_seconds),
            value=round(current_value, 2),
            idempotency_key=str(uuid.uuid4())
        ))
    return events
```

### Test data versioning

When schemas change, test fixtures must change with them. Rules:
- Factories/builders are the source of truth for test object shape — never raw dicts or hard-coded JSON
- When adding a required field: update the factory with a sensible default; don't update every test individually
- When removing a field: remove from factory first; the compiler or tests will tell you what else needs updating
- For JSON fixtures committed to the repo: keep them minimal and document which test uses them

---

## Test environment strategy

| Environment | Purpose | Data | Refresh |
|-------------|---------|------|---------|
| Local (dev) | Developer testing during development | Generated test data; no production data | Per developer |
| CI | Automated test execution on every PR | Ephemeral containers; no production data | Per PR |
| Staging | Integration and acceptance testing | Anonymised production-like data | Weekly from sanitised production snapshot |
| Performance | Load and stress testing | Synthetic data at production volume | Before each performance test run |
| Production | Live system | Real production data | N/A |

**No production data in lower environments.** All PII must be anonymised or synthetically generated before use in non-production environments.

---

## Test reporting

### CI test report format

```
## Test run: {Service name} — {Branch} — {Date}

**Result:** PASS | FAIL
**Duration:** {total time}

| Layer | Tests | Passed | Failed | Skipped | Coverage |
|-------|-------|--------|--------|---------|----------|
| Unit | 342 | 342 | 0 | 2 | 84% |
| Integration | 47 | 45 | 2 | 0 | — |
| Contract | 12 | 12 | 0 | 0 | — |
| Acceptance | 18 | 17 | 1 | 0 | — |

### Failures
| Test | Layer | Error | Since |
|------|-------|-------|-------|
| test_device_validation_timeout | Integration | Timeout after 10s — device registry did not respond | This run |
```

### Performance test pass/fail criteria

```
## Performance test result: {Test name} — {Date}

**NFR under test:** p99 latency < 500ms; error rate < 0.1% at 500 concurrent users
**Result:** PASS | FAIL

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| p50 latency | < 100ms | 67ms | ✅ PASS |
| p99 latency | < 500ms | 412ms | ✅ PASS |
| Error rate | < 0.1% | 0.03% | ✅ PASS |
| Max throughput | — | 1,247 req/s | — |
```

---

## Output format

### Test strategy definition

```
## Test strategy: {Service name}

**Pyramid ratios:** Unit {n}% / Integration {n}% / E2E {n}%
**Coverage targets:** Unit functions: {n}%; Integration: all boundary interactions; Acceptance: all BDD scenarios

### Test types active
| Type | Framework | When run | Purpose |
|------|-----------|----------|---------|
| Unit | {e.g. pytest, jest} | Every commit | Business logic, isolated |
| Integration | {e.g. pytest + testcontainers} | Every commit | Service + DB, service + queue |
| Contract | {e.g. Pact} | Every commit | API consumer-provider agreements |
| Acceptance | {e.g. pytest-bdd, Cucumber} | Pre-merge / staging | BDD scenarios from requirements-tracer |
| Performance | {e.g. k6} | Pre-release | NFR verification under load |

### Test data approach
{Describe factory/builder pattern used, database isolation strategy, and where synthetic data generators live}

### LLM/AI eval strategy (if applicable)
{Eval dataset location, criteria format, CI threshold, non-determinism handling}
```

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md`:

```
[YYYY-MM-DD] comprehensive-test-strategy — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] comprehensive-test-strategy — Defined test pyramid for device-registry service
[2026-04-20] comprehensive-test-strategy — Diagnosed flaky integration tests in event-consumer
[2026-04-20] comprehensive-test-strategy — Added property-based tests for telemetry validation
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for test pyramid templates, BDD scenario examples, contract testing setup guides, and performance test harnesses as they are developed.
