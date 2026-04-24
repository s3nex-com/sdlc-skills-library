---
name: executable-acceptance-verification
description: >
  Activate when writing or reviewing executable acceptance tests, converting requirements into
  BDD scenarios, running acceptance test suites to determine whether a feature meets the agreed
  acceptance criteria, writing the acceptance test plan for a milestone, verifying that all
  acceptance criteria from the requirements tracer are covered by tests, or producing an
  objective sign-off report for a milestone. Use when "done" needs to be verifiable by code,
  not a matter of opinion.
---

# Executable acceptance verification

## Purpose

"Done" must be objective. The only resolution that is not a matter of opinion is executable tests that pass or fail. This skill builds the framework for making acceptance criteria verifiable by code — so that a passing suite is proof of completion, not a claim.

---

## When to use

- Acceptance criteria from `requirements-tracer` need to be converted into executable BDD scenarios
- A milestone needs an objective sign-off: all agreed BDD scenarios must be run and their results documented
- Failing acceptance tests need to be triaged to determine whether they are product bugs, test bugs, or known deferred items
- The acceptance test suite needs to be organised, tagged, and configured for selective execution (smoke vs full suite)
- A feature is claimed "done" but there is no executable test proving the acceptance criteria pass
- An acceptance test plan needs to be written before a milestone verification run

## When NOT to use

- Decomposing PRD user stories into BDD acceptance criteria and the traceability matrix — use `requirements-tracer`.
- Designing the overall test pyramid (unit/integration/contract ratios) — use `comprehensive-test-strategy`.
- Load, stress, or soak tests that prove performance NFRs — use `performance-reliability-engineering`.
- Runtime API contract verification between services — use `api-contract-enforcer`.
- Evaluating LLM output quality with eval harnesses — use `llm-app-development`.
- Generating the PR description and merge sign-off that wraps a feature — use `pr-merge-orchestrator`.

---

## Process

1. Read the traceability matrix from `requirements-tracer`. Every story that is in scope for this verification run must have at least one BDD scenario.
2. For any story without a scenario: write the Gherkin scenario now. Confirm the scenario with the product owner (or the person who wrote the acceptance criteria) before running tests against it.
3. Verify the acceptance criteria are precise enough to execute. Vague criteria must be rewritten into testable Gherkin before proceeding.
4. Implement the step definitions for any new scenarios. Test against the real service in the staging environment — not mocks.
5. Tag scenarios appropriately (@smoke, @acceptance, @security, @slow) to enable selective execution.
6. Run the full acceptance suite in the agreed environment. Capture the run output and test report.
7. Triage any failures: product bug (implementation must be fixed), test bug (test must be corrected), or known deferred item (document with rationale and track in the risk register).
8. For product bugs: do not produce a sign-off. Direct back to `code-implementer` for the fix, then re-run.
9. For all scenarios passing (or failures triaged and accepted): produce the sign-off report in the output format below.
10. Append the execution log entry.

## BDD acceptance criteria to executable tests

### Step 1: Write unambiguous acceptance criteria

Before writing any test code, the acceptance criteria must be precise enough to execute. Vague criteria cannot be tested.

**Vague (untestable):**
> The system should handle high load gracefully.

**Specific (testable):**
```gherkin
Scenario: Ingestion API handles peak load
  Given the system has been running for 1 hour with no events
  When 500 concurrent clients each send 10 events per second for 5 minutes
  Then the p99 response time is below 500ms throughout
  And the error rate is below 0.1% throughout
  And no events are lost (all accepted events appear in Kafka within 10 seconds)
```

### Step 2: Map criteria to BDD scenarios

Every requirement must have at least one executable scenario. The scenarios are co-authored with the product owner (or business representative from either company) to confirm they correctly express the intent.

### Step 3: Implement the steps

```python
# Python + pytest-bdd example
# File: tests/acceptance/test_telemetry_ingestion.py

import pytest
from pytest_bdd import given, when, then, parsers, scenarios

scenarios("../features/telemetry_ingestion.feature")

@given("device <device_id> is registered in the device registry")
def registered_device(device_id, device_registry_client):
    device_registry_client.register(device_id)

@given("I have a valid API key for device <device_id>")
def valid_api_key(device_id, api_key_store):
    return api_key_store.create_for_device(device_id)

@when(parsers.parse("I POST a telemetry event with device_id {device_id} and event_type {event_type}"))
def post_telemetry_event(device_id, event_type, api_client, context):
    context.response = api_client.post("/v1/events", json={
        "device_id": device_id,
        "event_type": event_type,
        "timestamp": "2024-01-15T10:00:00Z",
        "payload": {"value": 23.5},
    })

@then(parsers.parse("the response status is {status_code:d}"))
def check_status_code(status_code, context):
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}. Body: {context.response.json()}"

@then("the response body contains an event_id")
def check_event_id(context):
    body = context.response.json()
    assert "event_id" in body, f"event_id missing from response: {body}"
    assert body["event_id"], "event_id is empty"

@then(parsers.parse("the event is published to the Kafka topic within {seconds:d} seconds"))
def check_kafka_event_published(seconds, context, kafka_consumer):
    event_id = context.response.json()["event_id"]
    event = kafka_consumer.wait_for_event(
        topic="edgeflow.telemetry.events.v1",
        filter=lambda e: e["event_id"] == event_id,
        timeout_seconds=seconds,
    )
    assert event is not None, f"Event {event_id} not found in Kafka after {seconds} seconds"
```

---

## Feature file organisation

```
tests/
  features/
    telemetry_ingestion.feature   ← One feature per major capability
    device_validation.feature
    error_handling.feature
    rate_limiting.feature
    bulk_ingestion.feature
  acceptance/
    test_telemetry_ingestion.py   ← Step definitions and tests
    test_device_validation.py
    conftest.py                   ← Fixtures: API client, Kafka consumer, DB setup
```

---

## Complete feature file example

```gherkin
# tests/features/telemetry_ingestion.feature

Feature: Telemetry event ingestion
  As Company B's device fleet
  I want to send telemetry events to the EdgeFlow platform
  So that Company A can process and store device data

  Background:
    Given the EdgeFlow ingestion API is running
    And device "dev-001" is registered in the device registry

  # ────────────────────────────────────────
  # Happy path scenarios
  # ────────────────────────────────────────

  Scenario: Successfully ingest a temperature reading
    Given I have a valid API key for device "dev-001"
    When I POST a telemetry event:
      | field       | value                |
      | device_id   | dev-001              |
      | event_type  | temperature_reading  |
      | timestamp   | 2024-01-15T10:00:00Z |
      | value       | 23.5                 |
    Then the response status is 202
    And the response body contains an event_id
    And the event is published to the Kafka topic "edgeflow.telemetry.events.v1" within 5 seconds
    And the Kafka message contains:
      | field       | expected value       |
      | device_id   | dev-001              |
      | event_type  | temperature_reading  |

  Scenario: Successfully ingest with idempotency key
    Given I have a valid API key for device "dev-001"
    And I have an idempotency key "idem-abc-123"
    When I POST the same telemetry event twice with the same idempotency key
    Then both responses return status 202
    And both responses contain the same event_id
    And only one event is published to Kafka

  # ────────────────────────────────────────
  # Validation error scenarios
  # ────────────────────────────────────────

  Scenario: Reject event from unregistered device
    Given I have a valid API key for device "dev-999"
    And device "dev-999" is not registered
    When I POST a telemetry event for device "dev-999"
    Then the response status is 422
    And the error code is "DEVICE_NOT_REGISTERED"
    And no event is published to Kafka

  Scenario: Reject event with timestamp more than 24 hours in the past
    Given I have a valid API key for device "dev-001"
    When I POST a telemetry event with timestamp "2020-01-01T00:00:00Z"
    Then the response status is 422
    And the error code is "TIMESTAMP_OUT_OF_RANGE"

  Scenario Outline: Reject event with missing required fields
    Given I have a valid API key for device "dev-001"
    When I POST a telemetry event missing the "<field>" field
    Then the response status is 422
    And the error message mentions "<field>"

    Examples:
      | field       |
      | device_id   |
      | event_type  |
      | timestamp   |

  # ────────────────────────────────────────
  # Security scenarios
  # ────────────────────────────────────────

  Scenario: Reject request with invalid API key
    Given I have an invalid API key "invalid-key-xyz"
    When I POST a telemetry event
    Then the response status is 401
    And the error code is "INVALID_API_KEY"

  Scenario: Reject request with no API key
    Given I do not provide an API key
    When I POST a telemetry event
    Then the response status is 401

  Scenario: Reject event for device that does not belong to the API key's organisation
    Given I have a valid API key for organisation "org-a"
    And device "dev-001" belongs to organisation "org-b"
    When I POST a telemetry event for device "dev-001"
    Then the response status is 403
    And the error code is "DEVICE_NOT_IN_ORGANISATION"

  # ────────────────────────────────────────
  # Rate limiting scenarios
  # ────────────────────────────────────────

  Scenario: Rate limit exceeded returns 429 with Retry-After header
    Given I have a valid API key with a rate limit of 10 requests per second
    When I send 15 requests within 1 second
    Then at least 5 requests receive status 429
    And each 429 response contains a "Retry-After" header
```

---

## Acceptance test suite management

### Test tagging strategy

Tag scenarios by type to allow selective execution:

```gherkin
@smoke @acceptance
Scenario: Successfully ingest a temperature reading
  ...

@acceptance @security
Scenario: Reject request with invalid API key
  ...

@acceptance @performance @slow
Scenario: Handle 500 concurrent clients
  ...
```

Run subsets:
```bash
# Run smoke tests only (fast, after every deployment)
pytest tests/acceptance/ -m "smoke" --tb=short

# Run all acceptance tests (before release)
pytest tests/acceptance/ -m "acceptance" -v

# Exclude slow performance tests
pytest tests/acceptance/ -m "acceptance and not slow"
```

### Environment configuration

```python
# conftest.py — environment-aware test configuration
import pytest
import os

@pytest.fixture(scope="session")
def api_base_url():
    env = os.environ.get("TEST_ENVIRONMENT", "staging")
    urls = {
        "staging": "https://staging.api.edgeflow.example.com",
        "local": "http://localhost:8080",
        "uat": "https://uat.api.edgeflow.example.com",
    }
    return urls[env]

@pytest.fixture(scope="session")
def kafka_consumer(kafka_bootstrap_servers):
    return TestKafkaConsumer(
        bootstrap_servers=kafka_bootstrap_servers,
        consumer_group=f"acceptance-tests-{uuid.uuid4()}",  # Unique group per run
    )
```

---

## Acceptance sign-off process

When a milestone includes acceptance testing as a deliverable gate:

### Step 1: Acceptance test plan
Before the milestone, the team agrees on which scenarios constitute acceptance. The plan includes:
- Feature list to be verified
- Scenario count per feature
- Environment (staging or dedicated UAT)
- Pass/fail criteria (all scenarios pass, or list of known deferred failures)
- Sign-off by whom

### Step 2: Execution
Run the full acceptance suite in the agreed environment. Generate a report.

### Step 3: Findings triage
For any failing scenarios:
- Is this a product bug? (Company B must fix)
- Is this a test bug? (Test needs correcting; fix the test, re-run)
- Is this a known deferred item? (Both parties acknowledge it; track in risk register)
- Is this a contract violation? (Escalate to contract change process)

### Step 4: Sign-off report

```
## Acceptance test sign-off: {Milestone name}

**Date:** {date}
**Environment:** {URL}
**Test run ID:** {CI job URL}

### Summary
| Feature | Scenarios | Passed | Failed | Deferred |
|---------|-----------|--------|--------|----------|
| Telemetry ingestion | 18 | 17 | 1 | 0 |
| Device validation | 12 | 12 | 0 | 0 |
| Error handling | 9 | 9 | 0 | 0 |
| Rate limiting | 5 | 4 | 0 | 1 |

**Total:** 44 scenarios | 42 passed | 1 failed | 1 deferred

### Failing scenarios
| Scenario | Feature | Failure description | Action |
|----------|---------|--------------------|----|
| Idempotency key returns same event_id | Telemetry ingestion | Returns different event_id on second call | Company B to fix by {date} |

### Deferred scenarios
| Scenario | Reason | Agreed resolution |
|----------|--------|------------------|
| Rate limit — burst handling | Rate limiting not yet implemented for burst mode | Tracked in risk register; target Q2 |

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] executable-acceptance-verification — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] executable-acceptance-verification — Acceptance run: all 18 BDD scenarios pass for ST-001 to ST-008
[2026-04-20] executable-acceptance-verification — Sprint 14 milestone sign-off complete
```

---

### Decision
☐ ACCEPTED — all scenarios pass
☑ ACCEPTED WITH CONDITIONS — 1 failing scenario to be fixed by {date}; deferred item acknowledged
☐ REJECTED — blocking failures prevent acceptance

**Engineering sign-off:** {name, role, date}
**Product/stakeholder sign-off:** {name, role, date}
```

## Output format

### Acceptance test run summary

```
## Acceptance verification: {Feature / Milestone}

**Date:** {date}
**Environment:** {URL}
**Test run CI link:** {link}

| Feature | Scenarios | Passed | Failed | Deferred |
|---------|-----------|--------|--------|----------|
| {Feature name} | {n} | {n} | {n} | {n} |

**Overall: {n} passed / {n} failed / {n} deferred**

### Failures
| Scenario | Failure | Classification | Action |
|----------|---------|----------------|--------|
| {description} | {what failed} | Product bug / Test bug / Deferred | {who fixes by when} |

### Sign-off
☐ ACCEPTED — all scenarios pass
☐ ACCEPTED WITH CONDITIONS — {n} failing scenarios to be fixed by {date}; deferred items acknowledged
☐ REJECTED — blocking failures prevent acceptance

**Engineering sign-off:** {name, date}
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for Gherkin scenario templates, acceptance test framework setup guides, and sign-off report examples as they are developed.
