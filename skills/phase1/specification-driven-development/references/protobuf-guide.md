# Protobuf / gRPC schema guide

## Key rules for production Protobuf schemas

### Field numbering
- Field numbers 1-15 use 1 byte encoding; 16-2047 use 2 bytes. Use 1-15 for the most frequently set fields.
- **Never reuse a field number** once it has been assigned, even after removing the field.
- Mark removed fields as `reserved` to prevent accidental reuse:

```proto
message DeviceEvent {
  reserved 3, 7;           // These field numbers were used and removed
  reserved "old_name";     // The field name was also used

  string device_id = 1;
  google.protobuf.Timestamp timestamp = 2;
  string event_type = 4;
}
```

### Backward compatibility rules
| Change | Backward compatible? |
|--------|---------------------|
| Add optional field | ✅ Yes |
| Add new message type | ✅ Yes |
| Add new RPC to service | ✅ Yes |
| Remove field (with reserved) | ✅ Yes (old clients ignore unknown fields) |
| Rename field (keeping number) | ✅ Yes (wire format uses number, not name) |
| Change field type | ❌ No (wire format changes) |
| Change field number | ❌ No |
| Remove field (without reserved) | ❌ No (number may be reused) |
| Make repeated field singular | ❌ No |

### Well-known types
Use Google's well-known types instead of primitives for semantic types:
```proto
import "google/protobuf/timestamp.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/wrappers.proto";  // For nullable primitives
import "google/protobuf/empty.proto";     // For void responses
```

---

## Worked example: TelemetryService

```proto
syntax = "proto3";

package edgeflow.telemetry.v1;

option go_package = "github.com/companya/edgeflow/gen/go/telemetry/v1";
option java_package = "com.companya.edgeflow.telemetry.v1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// TelemetryService handles ingestion and retrieval of device telemetry events.
service TelemetryService {
  // IngestEvent accepts a single telemetry event for asynchronous processing.
  rpc IngestEvent(IngestEventRequest) returns (IngestEventResponse);

  // IngestEventStream accepts a stream of telemetry events (client streaming).
  // Use for high-frequency devices to reduce per-event overhead.
  rpc IngestEventStream(stream IngestEventRequest) returns (IngestEventStreamResponse);

  // GetEvent retrieves a specific event by its server-assigned ID.
  rpc GetEvent(GetEventRequest) returns (TelemetryEvent);

  // ListDeviceEvents returns all events for a device within a time range.
  // Uses server-side streaming for large result sets.
  rpc ListDeviceEvents(ListDeviceEventsRequest) returns (stream TelemetryEvent);
}

message IngestEventRequest {
  // device_id is the registered identifier of the sending device.
  // Must match a device registered via the Device Registry service.
  string device_id = 1;

  // timestamp is when the event occurred on the device.
  // Must be within 24 hours of the server's current time.
  google.protobuf.Timestamp timestamp = 2;

  // event_type classifies this event for routing and processing.
  EventType event_type = 3;

  // payload contains event-specific data as key-value pairs.
  map<string, string> payload = 4;

  // idempotency_key is optional. If provided, duplicate requests with the
  // same key within 24 hours return the original response without reprocessing.
  string idempotency_key = 5;

  // Reserved: fields 6 and 7 were used in internal testing and must not be reused.
  reserved 6, 7;
}

message IngestEventResponse {
  // event_id is the server-assigned unique identifier for this event.
  string event_id = 1;

  // accepted_at is when the server accepted the event.
  google.protobuf.Timestamp accepted_at = 2;
}

message IngestEventStreamResponse {
  // accepted_count is the number of events accepted in the stream.
  int64 accepted_count = 1;

  // failed_count is the number of events that failed validation.
  int64 failed_count = 2;

  // failures contains details on individual event failures, indexed by
  // the 0-based position of the event in the stream.
  repeated EventFailure failures = 3;
}

message EventFailure {
  int64 stream_index = 1;
  string error_code = 2;
  string error_message = 3;
}

message GetEventRequest {
  string event_id = 1;
}

message ListDeviceEventsRequest {
  string device_id = 1;
  google.protobuf.Timestamp start_time = 2;
  google.protobuf.Timestamp end_time = 3;
  // max_events limits the number of events returned. Defaults to 1000 if not set.
  int32 max_events = 4;
}

message TelemetryEvent {
  string event_id = 1;
  string device_id = 2;
  google.protobuf.Timestamp timestamp = 3;
  EventType event_type = 4;
  map<string, string> payload = 5;
  google.protobuf.Timestamp ingested_at = 6;
}

enum EventType {
  EVENT_TYPE_UNSPECIFIED = 0;  // Proto3 requires a zero-value enum
  EVENT_TYPE_TEMPERATURE_READING = 1;
  EVENT_TYPE_PRESSURE_READING = 2;
  EVENT_TYPE_MOTION_DETECTED = 3;
  EVENT_TYPE_ERROR_CONDITION = 4;
  EVENT_TYPE_HEARTBEAT = 5;
}
```
