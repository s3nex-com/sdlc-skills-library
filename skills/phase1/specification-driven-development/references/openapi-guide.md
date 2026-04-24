# OpenAPI 3.x guide

## Complete guide to production-quality OpenAPI specifications

---

## Structure overview

Every OpenAPI 3.x spec must contain these top-level sections:

```yaml
openapi: "3.0.3"        # Always specify the exact version
info: ...               # Metadata
servers: ...            # Base URLs per environment
paths: ...              # API endpoints
components: ...         # Reusable schemas, responses, parameters, security schemes
```

---

## Info block

```yaml
info:
  title: Device Telemetry Ingestion API
  version: "1.2.0"
  description: |
    API for ingesting telemetry events from edge devices and managing device registrations.

    ## Versioning
    This API uses semantic versioning. Breaking changes increment the major version.
    The current major version is included in all endpoint paths: `/v1/`.

    ## Authentication
    All endpoints require a Bearer token obtained from the authentication service.
    See the Security Schemes section for details.

  contact:
    name: Company A Engineering
    email: api-support@companya.example.com
  license:
    name: Proprietary
```

---

## Servers

```yaml
servers:
  - url: https://api.staging.edgeflow.example.com/v1
    description: Staging environment
  - url: https://api.edgeflow.example.com/v1
    description: Production environment
```

---

## Security schemes

Define security once in `components/securitySchemes`, reference everywhere:

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT Bearer token. Obtain from POST /auth/token.
        Token lifetime: 15 minutes. Use the refresh token to obtain a new access token.
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: |
        Long-lived API key for machine-to-machine access.
        Scoped to specific resources. Request from Company A operations.

# Apply globally (can be overridden per-operation):
security:
  - BearerAuth: []
  - ApiKeyAuth: []
```

---

## Paths and operations

Each path operation must have: summary, description, operationId, tags, security (if different from global), parameters, requestBody (if applicable), and responses.

```yaml
paths:
  /telemetry/events:
    post:
      summary: Ingest a telemetry event
      description: |
        Accepts a single telemetry event from an edge device and publishes it to the
        processing pipeline. Returns 202 Accepted immediately — processing is asynchronous.

        **Idempotency:** Use the `Idempotency-Key` header to safely retry failed requests.
        If a request with the same key was already processed, the original response is returned.

      operationId: ingestTelemetryEvent
      tags:
        - Telemetry
      security:
        - ApiKeyAuth: []  # Override: this endpoint uses API keys, not JWTs
      parameters:
        - name: Idempotency-Key
          in: header
          required: false
          schema:
            type: string
            format: uuid
          description: |
            Optional. A UUID to make this request idempotent.
            If provided and a request with this key was already processed within 24 hours,
            the original response is returned without reprocessing.
          example: "550e8400-e29b-41d4-a716-446655440000"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/TelemetryEventRequest"
            example:
              device_id: "dev-abc-12345"
              timestamp: "2024-05-15T10:30:00.000Z"
              event_type: "temperature_reading"
              payload:
                temperature_celsius: 23.4
                humidity_percent: 65.2
      responses:
        "202":
          description: Event accepted for processing. Processing is asynchronous.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TelemetryEventAccepted"
        "400":
          description: Malformed request — the request body is not valid JSON.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                error: malformed_request
                message: "Request body is not valid JSON"
                request_id: req-xyz-456
        "401":
          $ref: "#/components/responses/Unauthorized"
        "403":
          $ref: "#/components/responses/Forbidden"
        "422":
          description: Validation error — the request body is valid JSON but fails validation.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                error: validation_error
                message: "Required field missing: device_id"
                field: device_id
                request_id: req-xyz-456
        "429":
          $ref: "#/components/responses/TooManyRequests"
        "500":
          $ref: "#/components/responses/InternalServerError"
```

---

## Components: schemas

Define all schemas in `components/schemas`. Never inline complex schemas in path items.

```yaml
components:
  schemas:
    TelemetryEventRequest:
      type: object
      required:
        - device_id
        - timestamp
        - event_type
        - payload
      properties:
        device_id:
          type: string
          description: Unique identifier of the device sending this event. Must be a registered device.
          minLength: 1
          maxLength: 64
          pattern: "^dev-[a-z0-9-]+$"
          example: "dev-abc-12345"
        timestamp:
          type: string
          format: date-time
          description: |
            ISO 8601 timestamp of when the event occurred on the device.
            Must be within 24 hours of the server's current time (events older than 24 hours are rejected).
          example: "2024-05-15T10:30:00.000Z"
        event_type:
          type: string
          description: Classification of this event. Must be a registered event type.
          enum:
            - temperature_reading
            - pressure_reading
            - motion_detected
            - error_condition
            - heartbeat
          example: "temperature_reading"
        payload:
          type: object
          description: |
            Event-specific payload. Schema varies by event_type.
            See the event type documentation for the expected payload structure per type.
          additionalProperties: true
          example:
            temperature_celsius: 23.4
            humidity_percent: 65.2

    TelemetryEventAccepted:
      type: object
      required:
        - event_id
        - accepted_at
      properties:
        event_id:
          type: string
          format: uuid
          description: Server-assigned unique ID for this event. Use for correlation and debugging.
          example: "7f9c3e2d-1a4b-5c6d-8e9f-0a1b2c3d4e5f"
        accepted_at:
          type: string
          format: date-time
          description: Server timestamp of when the event was accepted.
          example: "2024-05-15T10:30:00.123Z"

    ErrorResponse:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          description: Machine-readable error code. Stable across API versions.
          example: validation_error
        message:
          type: string
          description: Human-readable description of the error. May change between versions.
          example: "Required field missing: device_id"
        field:
          type: string
          description: The request field that caused the error, if applicable.
          example: device_id
        request_id:
          type: string
          description: |
            Request ID assigned by the server. Include this in support requests and bug reports
            to correlate with server logs.
          example: req-xyz-456

  responses:
    Unauthorized:
      description: Authentication credentials are missing or invalid.
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            error: authentication_required
            message: "A valid API key or Bearer token is required"
            request_id: req-xyz-456
    Forbidden:
      description: The authenticated principal does not have permission to perform this operation.
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            error: forbidden
            message: "Your API key does not have write access to this resource"
            request_id: req-xyz-456
    TooManyRequests:
      description: Rate limit exceeded.
      headers:
        Retry-After:
          description: Number of seconds until the rate limit resets.
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            error: rate_limit_exceeded
            message: "Rate limit exceeded. Retry after 60 seconds."
            request_id: req-xyz-456
    InternalServerError:
      description: An unexpected server error occurred.
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            error: internal_server_error
            message: "An unexpected error occurred. Please retry. If the problem persists, contact support."
            request_id: req-xyz-456
```

---

## Versioning conventions

- Include the major version in the URL path: `/v1/`, `/v2/`
- The `info.version` field uses semantic versioning: `1.2.3`
- A version change is required when:
  - Any breaking change is made (major version bump)
  - New optional fields or operations are added (minor version bump)
  - Documentation or description fixes only (patch version bump)
- The `Deprecation` and `Sunset` HTTP headers are added to deprecated operations before removal

---

## Quality checklist before review

- [ ] Every operation has a unique `operationId`
- [ ] Every operation has a `description`
- [ ] Every operation defines 400/422, 401, 403, 500 responses
- [ ] All error responses use `$ref: "#/components/schemas/ErrorResponse"`
- [ ] Every schema field has a `description`
- [ ] Every required field is listed in the `required` array
- [ ] Every operation has at least one example
- [ ] Shared schemas are in `components/schemas`, not inlined
- [ ] Version is specified in both the URL path and `info.version`
