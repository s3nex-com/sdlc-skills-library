# Acceptance criteria patterns

Given/When/Then patterns for five requirement types. Each section provides a template structure and three concrete examples.

---

## Type 1: Functional requirements (happy path)

**Template:**
```
Given [the preconditions that make this the normal/expected scenario]
When [the specific action the user or system takes]
Then [the observable outcomes that confirm success]
And [additional outcomes if needed]
```

**Example 1.1 — API creates a resource**
```
Given a valid API key with write scope
And a well-formed device registration payload with all required fields
When I POST to /v1/devices with the payload
Then the response status is 201 Created
And the response body contains a device_id field with a non-empty UUID
And the Location header contains the URL of the new resource
And subsequent GET /v1/devices/{device_id} returns the registered device
```

**Example 1.2 — User authenticates**
```
Given a registered user account with email "user@example.com"
And the user navigates to the login page
When they enter their correct email and password and submit
Then they are redirected to the dashboard
And the response sets a session cookie with HttpOnly and Secure flags
And the dashboard displays their name in the navigation header
```

**Example 1.3 — Background job processes a message**
```
Given a telemetry event message is published to the ingestion Kafka topic
And the event processor consumer group is running
When the consumer processes the message
Then the event is written to the TimescaleDB telemetry table within 30 seconds
And the event's device_id, timestamp, and payload are stored accurately
And the consumer group offset is committed (message is not reprocessed)
```

---

## Type 2: Error and negative cases

**Template:**
```
Given [preconditions that set up the error scenario]
When [the action that should trigger the error]
Then [the observable error response — HTTP status, error body, side effects]
And [confirm no unintended side effects occurred]
```

**Example 2.1 — API rejects invalid input**
```
Given a valid API key
When I POST to /v1/devices with a payload missing the required "device_type" field
Then the response status is 422 Unprocessable Entity
And the response body is:
  {
    "error": "validation_error",
    "message": "Required field missing: device_type",
    "field": "device_type"
  }
And no device record is created in the database
And the error is logged at WARN level with the request ID
```

**Example 2.2 — Unauthorised access**
```
Given a request with no Authorization header
When I GET /v1/devices
Then the response status is 401 Unauthorized
And the response body is:
  {
    "error": "authentication_required",
    "message": "A valid API key is required"
  }
And no data is returned
And the request is logged with source IP and timestamp (for security audit)
```

**Example 2.3 — Resource not found**
```
Given a valid API key
When I GET /v1/devices/nonexistent-device-id-00000000
Then the response status is 404 Not Found
And the response body is:
  {
    "error": "not_found",
    "message": "Device not found"
  }
And the response does not reveal whether the device exists but is in a different organisation
```

---

## Type 3: Performance requirements

**Template:**
```
Given [the environment and load configuration]
When [the load test scenario runs for the specified duration]
Then [the specific measurable outcomes — latency percentiles, error rates, throughput]
And [additional stability or recovery assertions]
```

**Example 3.1 — Latency SLO under normal load**
```
Given the staging environment with the production-equivalent configuration
And a k6 load test configured with 500 virtual users each making 10 requests/second
When the load test runs for 10 minutes (steady state — ramp-up excluded from measurement)
Then the p50 response time for GET /v1/devices is ≤ 80ms
And the p99 response time for GET /v1/devices is ≤ 300ms
And the error rate (4xx + 5xx) is ≤ 0.1%
```

**Example 3.2 — Throughput target**
```
Given the staging environment
And a k6 load test sending POST /v1/telemetry/events at 10,000 requests/second
When the test runs for 5 minutes at that rate
Then 0% of requests return 429 Too Many Requests or 503 Service Unavailable
And 99% of requests complete within 200ms
And all events are durably written to Kafka (verified by consumer lag remaining < 1000)
```

**Example 3.3 — Recovery after load spike**
```
Given the service is operating normally at 1,000 requests/second
When a traffic spike of 5,000 requests/second lasts for 60 seconds then returns to 1,000
Then error rate during the spike is ≤ 2%
And within 30 seconds of the spike ending, p99 latency returns to ≤ 300ms
And no memory leaks are observed (heap size stabilises within 2 minutes)
```

---

## Type 4: Security requirements

**Template:**
```
Given [the security preconditions or attack scenario]
When [the action or attack attempt]
Then [the security outcome — access denied, input rejected, audit logged]
And [confirm the attack had no unintended effect]
```

**Example 4.1 — Authentication boundary**
```
Given a request to the management API using a valid device API key (not a user token)
When the request attempts to access POST /v1/admin/users
Then the response is 403 Forbidden
And the response body does not reveal the existence of the /v1/admin/users endpoint
And the unauthorised access attempt is logged with the API key ID and timestamp
```

**Example 4.2 — Input validation against injection**
```
Given a valid API key with write scope
When I POST to /v1/devices with a device_name field containing:
  "test'); DROP TABLE devices; --"
Then the response is 422 Unprocessable Entity (device_name exceeds 64 characters or contains invalid characters)
And no SQL is executed against the devices table beyond the validation query
And the devices table is unmodified
```

**Example 4.3 — Rate limiting**
```
Given a valid API key
When I send more than 100 requests per minute to any endpoint using that API key
Then subsequent requests within that minute receive 429 Too Many Requests
And the response includes a Retry-After header indicating when the rate limit resets
And legitimate requests resume successfully after the rate limit window expires
```

---

## Type 5: Integration requirements

**Template:**
```
Given [the integration parties and their states]
When [the integration operation occurs]
Then [the observable outcomes from both sides of the integration]
And [contract compliance assertions]
```

**Example 5.1 — API contract compliance**
```
Given the ingestion service is deployed
And the OpenAPI spec for POST /v1/telemetry/events is version 2.1.0 (frozen)
When the Pact contract test suite for the telemetry ingestion consumer runs against the service
Then all 12 consumer pact interactions pass
And the response schema for the 201 Created response matches the spec exactly
And the error response schema for 400 and 422 responses matches the spec exactly
```

**Example 5.2 — Event downstream consumption**
```
Given the ingestion service has processed a valid telemetry event
When the event processing consumer reads the event from the Kafka topic
Then the event payload conforms to the Avro schema registered in the Schema Registry
And the event is written to TimescaleDB with the correct device_id, timestamp, and payload fields
And the end-to-end latency from POST /v1/telemetry/events to database write is ≤ 10 seconds at p99
```

**Example 5.3 — Webhook delivery to partner system**
```
Given a device alert has been triggered for device "device-abc-123"
And the organisation has configured a webhook endpoint at "https://partner.example.com/webhooks/alerts"
When the alert notification service delivers the webhook
Then the partner endpoint receives a POST request within 30 seconds of the alert being triggered
And the request body matches the AlertNotification schema in the AsyncAPI spec
And if the partner endpoint returns a non-2xx response, the delivery is retried with exponential backoff
And after 3 failed attempts, the delivery is moved to the dead-letter queue and an alert is raised
```
