# AsyncAPI 2.x guide

## Production-quality AsyncAPI specifications

AsyncAPI describes event-driven and message-based interfaces. Use it for Kafka topics, MQTT feeds, WebSocket streams, and AMQP queues.

---

## Worked example: Device event stream

```yaml
asyncapi: "2.6.0"

info:
  title: EdgeFlow Device Event Stream
  version: "1.1.0"
  description: |
    Kafka event stream for device telemetry events and device lifecycle notifications.

    ## Consumer groups
    Each consumer service should use a distinct consumer group ID to receive all events.
    Consumer groups starting with `edgeflow.` are reserved for platform services.

    ## Schema registry
    All messages use Avro schemas registered in the Confluent Schema Registry.
    The schema registry URL is configured per environment.

  contact:
    name: Company A Engineering
    email: api-support@companya.example.com

servers:
  staging:
    url: kafka.staging.edgeflow.example.com:9092
    protocol: kafka
    description: Staging Kafka cluster
    security:
      - sasl-scram: []
  production:
    url: kafka.edgeflow.example.com:9092
    protocol: kafka
    description: Production Kafka cluster
    security:
      - sasl-scram: []

channels:
  edgeflow.telemetry.events.v1:
    description: |
      Stream of all telemetry events ingested by the platform.

      **Partitioning:** Events are partitioned by device_id. All events from a single
      device are delivered in order within a partition.

      **Retention:** 7 days (configurable per environment).

      **Throughput:** Designed for up to 100,000 events/second across all partitions.

    bindings:
      kafka:
        topic: edgeflow.telemetry.events.v1
        partitions: 32
        replicas: 3
        topicConfiguration:
          cleanup.policy:
            - delete
          retention.ms: 604800000   # 7 days
          max.message.bytes: 1048576  # 1MB

    subscribe:
      summary: Receive telemetry events
      description: |
        Subscribe to receive all telemetry events ingested by the platform.
        Events are published immediately after ingestion validation.
      operationId: receiveTelemetryEvent
      bindings:
        kafka:
          groupId:
            type: string
            description: Consumer group ID. Must be unique per consuming service.
          clientId:
            type: string
            description: Client ID for connection tracking.
      message:
        $ref: "#/components/messages/TelemetryEvent"

    publish:
      summary: Publish a telemetry event (internal use only)
      description: |
        Published by the ingestion service after event validation.
        External consumers should not publish to this topic.
      operationId: publishTelemetryEvent
      message:
        $ref: "#/components/messages/TelemetryEvent"

  edgeflow.devices.lifecycle.v1:
    description: |
      Device registration and deregistration events.
      Published when devices are created, updated, or deleted via the Device Registry API.

    bindings:
      kafka:
        topic: edgeflow.devices.lifecycle.v1
        partitions: 8
        replicas: 3

    subscribe:
      summary: Receive device lifecycle events
      operationId: receiveDeviceLifecycleEvent
      message:
        oneOf:
          - $ref: "#/components/messages/DeviceRegistered"
          - $ref: "#/components/messages/DeviceUpdated"
          - $ref: "#/components/messages/DeviceDeregistered"

components:
  messages:
    TelemetryEvent:
      name: TelemetryEvent
      title: Telemetry event
      summary: A single telemetry event from an edge device.
      contentType: application/json
      headers:
        type: object
        required:
          - traceparent
          - schema-id
        properties:
          traceparent:
            type: string
            description: W3C Trace Context traceparent header for distributed tracing.
            example: "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
          schema-id:
            type: integer
            description: Confluent Schema Registry schema ID for the message value.
          event-type:
            type: string
            description: Duplicate of payload event_type for header-based routing.
      payload:
        $ref: "#/components/schemas/TelemetryEventPayload"

    DeviceRegistered:
      name: DeviceRegistered
      title: Device registered
      summary: Published when a new device is registered.
      contentType: application/json
      payload:
        $ref: "#/components/schemas/DeviceRegisteredPayload"

    DeviceUpdated:
      name: DeviceUpdated
      title: Device updated
      contentType: application/json
      payload:
        $ref: "#/components/schemas/DeviceUpdatedPayload"

    DeviceDeregistered:
      name: DeviceDeregistered
      title: Device deregistered
      contentType: application/json
      payload:
        type: object
        required: [event_id, device_id, deregistered_at, reason]
        properties:
          event_id:
            type: string
            format: uuid
          device_id:
            type: string
          deregistered_at:
            type: string
            format: date-time
          reason:
            type: string
            enum: [owner_request, inactivity, policy_violation, admin_action]

  schemas:
    TelemetryEventPayload:
      type: object
      required: [event_id, device_id, timestamp, event_type, payload, ingested_at]
      properties:
        event_id:
          type: string
          format: uuid
          description: Server-assigned unique event identifier.
        device_id:
          type: string
          description: The device that generated this event.
        timestamp:
          type: string
          format: date-time
          description: When the event occurred on the device.
        event_type:
          type: string
          description: Event classification.
        payload:
          type: object
          description: Event-specific data.
          additionalProperties: true
        ingested_at:
          type: string
          format: date-time
          description: When the platform accepted this event.

    DeviceRegisteredPayload:
      type: object
      required: [event_id, device_id, device_type, organisation_id, registered_at]
      properties:
        event_id:
          type: string
          format: uuid
        device_id:
          type: string
        device_type:
          type: string
        organisation_id:
          type: string
          format: uuid
        registered_at:
          type: string
          format: date-time
        metadata:
          type: object
          additionalProperties:
            type: string

    DeviceUpdatedPayload:
      type: object
      required: [event_id, device_id, updated_at, changed_fields]
      properties:
        event_id:
          type: string
          format: uuid
        device_id:
          type: string
        updated_at:
          type: string
          format: date-time
        changed_fields:
          type: array
          items:
            type: string
          description: Names of the fields that were changed in this update.

  securitySchemes:
    sasl-scram:
      type: scramSha512
      description: SASL/SCRAM-SHA-512 authentication for Kafka. Credentials provided by the platform team.
```

---

## Message envelope standard

Every event type in this system uses a common envelope. Define these fields in `components/schemas/EventEnvelope` and `$ref` them into every message payload.

```yaml
components:
  schemas:
    EventEnvelope:
      type: object
      required: [event_id, schema_version, correlation_id, timestamp]
      properties:
        event_id:
          type: string
          format: uuid
          description: >
            Unique identifier for this event. Consumers use this for idempotent
            deduplication — processing the same event_id twice must produce the
            same result as processing it once.
        schema_version:
          type: string
          example: "1.2"
          description: >
            Schema version for this message. Consumers select a deserialiser based
            on this value. Format: MAJOR.MINOR. Minor bumps are backward-compatible
            (new optional fields). Major bumps are breaking (new channel version required).
        correlation_id:
          type: string
          description: >
            Trace context propagated from the originating request. Use the W3C
            traceparent value if available, otherwise a UUID generated at the
            origin of the request chain.
          example: "4bf92f3577b34da6a3ce929d0e0e4736"
        timestamp:
          type: string
          format: date-time
          description: >
            When the event occurred at the source (device time or service time).
            NOT the ingestion time. Consumers use this for ordering and time-series
            queries. Ingestion time is tracked separately in Kafka message metadata.
```

Usage in a message payload:

```yaml
components:
  schemas:
    TelemetryEventPayload:
      allOf:
        - $ref: "#/components/schemas/EventEnvelope"
        - type: object
          required: [device_id, event_type, payload, ingested_at]
          properties:
            device_id:
              type: string
            event_type:
              type: string
            payload:
              type: object
              additionalProperties: true
            ingested_at:
              type: string
              format: date-time
```

---

## Delivery guarantee documentation

Document the delivery guarantee for each channel in the channel `description`. This is a contract commitment, not an implementation detail.

```yaml
channels:
  edgeflow.telemetry.events.v1:
    description: |
      Stream of all telemetry events ingested by the platform.

      **Delivery guarantee:** At-least-once. Consumers must be idempotent.
      Use event_id for deduplication. Duplicate events may arrive within
      a 30-second window after a producer restart.

      **Ordering:** Ordered per partition (partitioned by device_id). No
      cross-partition ordering guarantee.

      **Retention:** 7 days.
```

Delivery guarantee options and when to use each:

| Guarantee | Spec language | Consumer requirement |
|-----------|---------------|---------------------|
| At-most-once | "At-most-once. Events may be lost on producer failure." | No deduplication needed. Not suitable for critical events. |
| At-least-once | "At-least-once. Consumers must be idempotent. Use event_id for deduplication." | Consumer deduplicates on `event_id`. Most common choice. |
| Exactly-once | "Exactly-once via Kafka transactions. Requires consumer isolation level = read_committed." | Consumer must configure `isolation.level=read_committed`. Use for financial or state-change events only. |

---

## Schema evolution and compatibility

### Backward-compatible changes (minor version bump: 1.0 → 1.1)

Adding an optional field is backward-compatible. Existing consumers continue to function unchanged — they simply ignore the new field.

**Spec change:**
```yaml
# v1.1 — added optional field 'firmware_version'
TelemetryEventPayload:
  allOf:
    - $ref: "#/components/schemas/EventEnvelope"
    - type: object
      required: [device_id, event_type, payload]
      properties:
        device_id:
          type: string
        event_type:
          type: string
        payload:
          type: object
        firmware_version:
          type: string
          description: "Added in v1.1. Optional. Firmware version of the device at event time."
```

**Consumer validation test for forward compatibility** — run this before deploying the producer update:

```python
# tests/contract/test_telemetry_schema_evolution.py

import json
import jsonschema

def test_consumer_ignores_new_optional_field():
    """
    Verify that the v1.0 consumer schema validates a v1.1 message correctly.
    New optional fields must not break existing consumers.
    """
    v1_1_message = {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "schema_version": "1.1",
        "correlation_id": "abc123",
        "timestamp": "2026-04-20T10:00:00Z",
        "device_id": "dev-001",
        "event_type": "temperature_reading",
        "payload": {"temperature": 23.5},
        "firmware_version": "2.4.1"    # New field in v1.1
    }

    # Load the v1.0 consumer schema (what the existing consumer validates against)
    with open("schemas/telemetry_event_v1_0.json") as f:
        v1_0_schema = json.load(f)

    # v1.0 schema must use additionalProperties: true (or omit it)
    # so that the new firmware_version field does not cause a validation failure
    jsonschema.validate(v1_1_message, v1_0_schema)  # Must not raise


def test_consumer_handles_missing_optional_field():
    """
    Verify that a v1.1 consumer schema handles messages that omit the new optional field.
    Producers on v1.0 will not include firmware_version.
    """
    v1_0_message = {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "schema_version": "1.0",
        "correlation_id": "abc123",
        "timestamp": "2026-04-20T10:00:00Z",
        "device_id": "dev-001",
        "event_type": "temperature_reading",
        "payload": {"temperature": 23.5}
        # firmware_version absent — this is valid for v1.0 producers
    }

    with open("schemas/telemetry_event_v1_1.json") as f:
        v1_1_schema = json.load(f)

    jsonschema.validate(v1_0_message, v1_1_schema)  # Must not raise
```

### Breaking changes (major version: new channel v2)

Removing a field, changing a field type, or adding a required field requires a new channel version. Never modify the schema of a live channel in a breaking way.

**Process:**
1. Define the new channel in the AsyncAPI spec (`edgeflow.telemetry.events.v2`) alongside the existing `v1` channel.
2. Update the producer to publish to both `v1` and `v2` simultaneously during the migration window.
3. Migrate consumers to `v2` one by one.
4. Once all consumers have migrated, remove `v1` from the spec and deprecate the channel (set retention to minimum, add deprecation notice to the channel description).
5. After retention window expires, stop publishing to `v1`.

**Spec deprecation notice:**
```yaml
channels:
  edgeflow.telemetry.events.v1:
    description: |
      **DEPRECATED as of 2026-05-01. Migrate to edgeflow.telemetry.events.v2.**
      This channel will stop receiving events on 2026-06-01.
      See migration guide: docs/migrations/telemetry-v1-to-v2.md
```

### Consumer validation checklist

Before merging any schema change to a channel:

- [ ] Change is classified: backward-compatible (minor) or breaking (major/new channel)
- [ ] For backward-compatible: consumer forward-compatibility test passes (consumer on old schema validates new message)
- [ ] For backward-compatible: producer backward-compatibility test passes (consumer on new schema validates old message)
- [ ] For breaking: new channel defined in spec; migration process documented
- [ ] Delivery guarantee documented in channel description
- [ ] `event_id`, `schema_version`, `correlation_id`, `timestamp` present in all message payloads
- [ ] `additionalProperties: true` on all schemas (or omitted — the default in JSON Schema is `true`) so future optional fields do not break existing consumers
