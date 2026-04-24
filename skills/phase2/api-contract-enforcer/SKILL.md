---
name: api-contract-enforcer
description: >
  Activate when verifying that a service implementation actually matches its API contract,
  running contract tests between consumer and provider services, detecting contract drift
  between what the spec says and what is deployed, setting up Pact or schema-registry based
  contract verification in CI, investigating a production incident caused by a contract
  violation, comparing two spec versions to identify breaking changes, validating partner
  company deliverables against the agreed OpenAPI spec, or enforcing that no spec changes
  are deployed without going through the change control process. Use this when something is
  broken at an integration boundary and you need to determine whether it is a contract
  violation or an implementation bug.
---

# API contract enforcer

## Purpose

The contract between two services is the agreement that allows them to evolve independently. A contract violation — one service behaving differently from what the contract specifies — is the most common root cause of integration failures in microservices and cross-company integrations. This skill provides the tools and processes to detect, prevent, and resolve contract violations before they reach production.

---

## When to use

- Setting up Pact or schema-registry-based contract verification in CI for the first time
- An integration failure has occurred and you need to determine whether it is a contract violation or an implementation bug
- Adding consumer-driven contract tests between two services or two companies
- Running a periodic contract drift check between the deployed API and the frozen spec
- A provider changed their implementation and you need to verify it still satisfies consumer contracts
- Investigating why a Kafka consumer is failing after a producer was updated
- Comparing two spec versions to determine whether a change is breaking for current consumers

## When NOT to use

- Authoring or freezing the spec (OpenAPI, Protobuf, AsyncAPI) itself — use `specification-driven-development`.
- General unit/integration test strategy and pyramid design — use `comprehensive-test-strategy`.
- Running a postmortem after a contract-related incident has already occurred — use `incident-postmortem`.
- Defining the CI stages and gates that run contract tests — use `devops-pipeline-governance`.
- Verifying end-user acceptance criteria with BDD scenarios — use `executable-acceptance-verification`.
- Contract governance at the product/decision level (when to version, when to deprecate) — use `architecture-decision-records` to record the decision.

---

## Process

### Setting up contract tests (first time)

1. Identify all integration boundaries where a consumer depends on a provider contract.
2. For REST APIs: implement Pact consumer tests on the consumer side, defining the interactions expected. Publish the pact file to a Pact Broker.
3. For Kafka/event streams: configure the Confluent Schema Registry with FULL or BACKWARD_TRANSITIVE compatibility mode for cross-service topics.
4. On the provider side: add a Pact verification job to CI that fetches and verifies all consumer pacts from the broker. The CI job fails if any verification fails.
5. Add the `can-i-deploy` check to the consumer's CI pipeline before any production deployment.

### Investigating a contract violation

6. Confirm the violation is real (not a test or tooling misconfiguration).
7. Determine which side violated: did the provider change an existing contract, or did the consumer misuse it?
8. Assess impact: are live consumers broken right now?
9. Follow the violation response procedure (triage → immediate mitigation → root cause → formal incident record if it reached production).

### Drift detection (ongoing)

10. Set up the scheduled CI job (see "Contract drift detection") to run daily against the frozen spec and the deployed API.
11. For any drift detected: triage as breaking vs non-breaking. Breaking drift blocks the next deployment until resolved.

### All sub-tasks

12. Append the execution log entry.

## What is a contract violation?

A contract violation occurs when a service's runtime behaviour diverges from the agreed API specification:

| Type | Example | Severity |
|------|---------|---------|
| Undeclared field removed | Response no longer includes `event_id` | Breaking — consumers are broken |
| Required field made optional | `device_id` no longer validated as required | Breaking — consumers may rely on validation |
| Type changed | `timestamp` changed from ISO 8601 string to epoch integer | Breaking |
| Status code changed | 200 changed to 201 for existing operation | Breaking |
| Endpoint removed | `GET /events/{id}` no longer exists | Breaking |
| New required field added | Request now requires `organisation_id` | Breaking |
| New optional field added in response | Response now includes `metadata` | Non-breaking (additive) |
| Validation changed | `device_id` now validated against a stricter pattern | Breaking for existing values |
| Error code changed | `DEVICE_NOT_FOUND` → `ENTITY_NOT_FOUND` | Breaking for consumers parsing error codes |

---

## Consumer-driven contract testing (Pact)

Consumer-driven contract testing inverts the traditional "provider publishes spec" model. The consumer defines what it needs from the provider (its expectations), and the provider runs those expectations as tests in its own CI pipeline.

### Why consumer-driven?

In a cross-company engagement, Company A (consumer) cannot dictate Company B's internal design, but Company A can express its requirements as executable tests. Company B's CI pipeline fails if their implementation no longer satisfies Company A's expressed needs.

### Pact workflow

```
Company A (Consumer)                    Company B (Provider)
        │                                        │
[1] Write consumer tests                         │
    defining expectations                        │
        │                                        │
[2] Run pact tests →                             │
    generate pact file                           │
        │                                        │
[3] Publish pact to Pact Broker ─────────────> [4] CI fetches pact
        │                                        │
        │                                  [5] Run provider
        │                                      verification tests
        │                                        │
        │                                  [6] Publish results
        │                              <──────── │
[7] Can-I-Deploy check                           │
    before Company A deploys                     │
```

### Consumer test example (Python)

```python
# Company A's ingestion service consuming Company B's Device Registry API
import pytest
from pact import Consumer, Provider

@pytest.fixture
def pact():
    pact = Consumer("edgeflow-ingestion").has_pact_with(
        Provider("company-b-device-registry"),
        pact_dir="./pacts",
        publish_to_broker=True,
        broker_url="https://pact-broker.edgeflow.example.com",
    )
    pact.start_service()
    yield pact
    pact.stop_service()


def test_registered_device_returns_active_status(pact):
    expected_body = {
        "device_id": "dev-001",
        "status": "active",
        "registered_at": pact.like("2024-01-15T10:00:00Z"),
        "organisation_id": pact.like("org-abc-123"),
    }

    (pact
     .given("device dev-001 is registered and active")
     .upon_receiving("a request to get device status")
     .with_request("GET", "/v1/devices/dev-001/status",
                   headers={"X-API-Key": "test-key"})
     .will_respond_with(200, body=expected_body))

    with pact:
        from company_a.clients import DeviceRegistryClient
        client = DeviceRegistryClient(pact.uri, api_key="test-key")
        result = client.get_device_status("dev-001")

    assert result.status == "active"
    assert result.device_id == "dev-001"


def test_unregistered_device_returns_404(pact):
    (pact
     .given("device dev-999 does not exist")
     .upon_receiving("a request to get status for unknown device")
     .with_request("GET", "/v1/devices/dev-999/status",
                   headers={"X-API-Key": "test-key"})
     .will_respond_with(404, body={
         "error": pact.like("DEVICE_NOT_FOUND"),
         "message": pact.like("Device dev-999 not found"),
     }))

    with pact:
        from company_a.clients import DeviceRegistryClient
        client = DeviceRegistryClient(pact.uri, api_key="test-key")
        with pytest.raises(DeviceNotFoundError):
            client.get_device_status("dev-999")
```

### Provider verification (Company B runs this)

```python
# Company B runs this in their CI pipeline to verify they satisfy Company A's pact
import pytest
from pact import Verifier

def test_device_registry_satisfies_consumer_pact():
    verifier = Verifier(
        provider="company-b-device-registry",
        provider_base_url="http://localhost:8080",
    )

    output, _ = verifier.verify_with_broker(
        broker_url="https://pact-broker.edgeflow.example.com",
        broker_username="pact-user",
        broker_password="pact-password",
        consumer_version_selectors=[{"mainBranch": True}, {"deployed": True}],
        publish_verification_results=True,
        provider_app_version="1.2.0",
    )

    assert output == 0, "Pact verification failed — contract is broken"
```

---

## Schema registry contract enforcement (Kafka)

For event-driven contracts (Kafka topics), use the Confluent Schema Registry with schema compatibility rules.

### Compatibility levels

| Level | Meaning | Use when |
|-------|---------|---------|
| `BACKWARD` | New schema can read data from previous schema | Adding optional fields to existing messages |
| `FORWARD` | Previous schema can read data from new schema | Removing optional fields |
| `FULL` | Both backward and forward compatible | Safest; use for all cross-company topics |
| `NONE` | No compatibility checking | Never for cross-company topics |

### Enforcing schema compatibility in CI

```bash
# Register and test compatibility before deployment
# Using the Schema Registry REST API

# Check if new schema is compatible with existing version
curl -X POST \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d @new-schema.json \
  "https://schema-registry.edgeflow.example.com/compatibility/subjects/edgeflow.telemetry.events.v1-value/versions/latest"

# Expected response for compatible schema:
# {"is_compatible": true}

# If not compatible, the pipeline fails:
# {"is_compatible": false}
```

---

## Runtime contract validation (request/response validation)

Validate all requests and responses against the OpenAPI spec at runtime in staging. This catches contract violations that are not covered by unit or contract tests.

### Schemathesis (property-based API testing)

```bash
# Run Schemathesis against staging — generates and validates requests/responses
schemathesis run https://staging.api.edgeflow.example.com/v1/openapi.yaml \
  --auth "X-API-Key:${TEST_API_KEY}" \
  --checks all \
  --hypothesis-max-examples 200 \
  --report schemathesis-report.json
```

Schemathesis generates test cases from the OpenAPI spec and reports any responses that do not match the declared response schemas.

### OpenAPI request/response validation middleware

```python
# FastAPI middleware that validates all requests and responses against the spec
from openapi_core import create_spec
from openapi_core.contrib.starlette import StarletteOpenAPIRequest, StarletteOpenAPIResponse
from openapi_core import validate_request, validate_response

spec = create_spec(load_spec("openapi.yaml"))

@app.middleware("http")
async def validate_openapi_contract(request: Request, call_next):
    # Validate incoming request (only in staging/dev, not production)
    if settings.environment != "production":
        openapi_request = StarletteOpenAPIRequest(request)
        try:
            validate_request(spec, openapi_request)
        except Exception as e:
            logger.warning("Contract violation: invalid request", error=str(e),
                         path=request.url.path, method=request.method)

    response = await call_next(request)

    # Validate response
    if settings.environment != "production":
        openapi_response = StarletteOpenAPIResponse(response)
        try:
            validate_response(spec, openapi_request, openapi_response)
        except Exception as e:
            logger.error("Contract violation: invalid response", error=str(e),
                        path=request.url.path, method=request.method,
                        status_code=response.status_code)

    return response
```

---

## Contract drift detection

Scheduled CI job that compares the currently deployed API (spec endpoint) against the agreed frozen contract:

```yaml
# .github/workflows/contract-drift.yml
name: Contract drift detection

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 06:00

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{SHA}

      - name: Fetch deployed spec
        run: |
          curl -f https://staging.api.edgeflow.example.com/v1/openapi.yaml \
            > /tmp/deployed-spec.yaml

      - name: Compare with frozen contract
        run: |
          python scripts/diff_contracts.py \
            --old contracts/frozen/ingestion-api-v1.0.0.yaml \
            --new /tmp/deployed-spec.yaml \
            --output /tmp/drift-report.md \
            --fail-on-breaking

      - name: Upload drift report
        uses: actions/upload-artifact@{SHA}
        with:
          name: contract-drift-report
          path: /tmp/drift-report.md

      - name: Notify on breaking drift
        if: failure()
        uses: {slack-notify-action}
        with:
          message: "⚠️ Contract drift detected: deployed API no longer matches frozen contract"
          channel: "engineering-alerts"
```

---

## Contract violation response procedure

When a contract violation is detected in production:

### Step 1: Triage (within 1 hour)
- Confirm the violation is real (not a test or tooling issue)
- Determine which side of the contract violated (consumer or provider?)
- Assess impact: is this breaking any live consumers?

### Step 2: Immediate mitigation
- If provider changed unexpectedly: roll back the provider deployment
- If consumer is broken by a provider change: check if consumer can be patched forward
- If the violation is intentional (an unapproved contract change): escalate to both engineering leads immediately

### Step 3: Root cause
- How did the change bypass the contract validation gates in CI?
- Was the contract test not updated with the implementation?
- Was a gate bypassed?

### Step 4: Formal incident record
All contract violations that reach production are treated as incidents. See `incident-postmortem/` skill for the post-incident review process.

---

## Output format

### Contract verification report

```
## Contract verification: {Consumer} → {Provider}

**Date:** {date}
**Consumer version:** {version / commit}
**Provider version:** {version / commit}
**Pact Broker:** {URL}

**Result:** PASS | FAIL

### Verified interactions
| Interaction | State | Result |
|-------------|-------|--------|
| Get device status — active device | device dev-001 is active | ✅ PASS |
| Get device status — unknown device | device dev-999 not found | ✅ PASS |
| Get device status — inactive device | device dev-002 is inactive | ❌ FAIL: expected status "inactive", got "suspended" |

### Failures
| Interaction | Expected | Actual | Impact |
|-------------|----------|--------|--------|
| Get inactive device | `status: "inactive"` | `status: "suspended"` | Company A cannot map device status correctly |

### Required action
Company B must either:
1. Revert the status value to "inactive", OR
2. Raise a contract change request to add "suspended" as an allowed value

Timeline: resolve within 5 business days (per engagement SLA).
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] api-contract-enforcer — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] api-contract-enforcer — Pact contract tests added for device-registry consumer
[2026-04-20] api-contract-enforcer — Contract drift detected: provider broke GET /devices/{id} response schema
```

---

## Reference files

The `references/` directory is available for contract testing templates, Pact broker setup examples, and schema registry checklists as they are developed.
