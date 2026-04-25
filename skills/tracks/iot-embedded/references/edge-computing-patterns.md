# Edge computing patterns

## Offline-first for devices

Devices lose connectivity. Design the system to operate correctly during network outages and to reconcile state cleanly when connectivity returns.

**Core rule:** A device should never be in a permanently broken state because the backend was unreachable. All operations must succeed locally first, then sync.

### Local operation with queued sync

```
Device → Local state store (always) → Sync queue → Cloud (when connected)
```

- Device writes all state changes to local storage first
- Sync agent reads the queue and uploads to the backend when connected
- Backend processes uploads idempotently (duplicate delivery from retry must not cause double processing)
- Backend sends an acknowledgement; sync agent marks items as delivered

### Conflict resolution on reconnect

When a device reconnects after an outage, both the device and backend may have made state changes.

| Strategy | When to use |
|----------|------------|
| Last-write-wins (timestamp) | Simple state (settings, configuration) where the most recent value is always correct |
| Server wins | Configuration pushed from backend that should always override device-local changes |
| Device wins | Sensor readings and events — the device observed them; the backend did not |
| Merge | Additive state (event logs, telemetry batches) — append all records from both sides |
| Manual resolution | Complex state (orders, transactions) — flag the conflict and require human review |

---

## Data compression for constrained bandwidth

Devices on cellular (NB-IoT, LTE-M, 2G) pay per kilobyte. Uncompressed JSON telemetry is expensive.

### Format comparison (single sensor reading with 10 fields)

| Format | Size |
|--------|------|
| Verbose JSON | 380 bytes |
| Compact JSON | 180 bytes |
| MessagePack | 95 bytes |
| Protobuf | 45 bytes |
| Custom binary | 20–30 bytes |

**Recommendation:** Use Protobuf for all device-to-cloud telemetry on bandwidth-constrained devices. Define the schema in a `.proto` file committed to the repo.

### Payload batching

Instead of sending one reading per message, batch multiple readings into one payload:

```protobuf
message TelemetryBatch {
  string device_id = 1;
  repeated SensorReading readings = 2;
}

message SensorReading {
  int64 timestamp_ms = 1;
  float temperature_c = 2;
  float humidity_pct = 3;
  int32 battery_mv = 4;
}
```

**Batching interval:** Tune based on bandwidth cost and latency tolerance. Common: 60 seconds for monitoring telemetry; 5 seconds for control-loop feedback.

---

## Power budgeting

Battery-powered devices must survive their target lifetime on a single charge or between charge cycles.

### Power states

| State | Typical current | When to use |
|-------|----------------|------------|
| Active (transmitting) | 200–500 mA | Minimise; transmit in bursts |
| Active (processing, no radio) | 10–50 mA | Computation without radio |
| Light sleep (CPU sleep, radio on) | 1–10 mA | Waiting for incoming messages |
| Deep sleep (radio off, MCU sleep) | 10–100 µA | Between readings |
| Hibernate (RTC only) | 1–10 µA | Long idle periods |

### Power budget model

```
Average current = (Active current × Active time) + (Sleep current × Sleep time)
                  ──────────────────────────────────────────────────────────────
                                    Total time

Battery life (hours) = Battery capacity (mAh) / Average current (mA)
```

**Example:** Device reads sensors every 60s, transmits for 500ms, then deep sleeps.
- Active: 350 mA × 0.5s = 175 mAs
- Deep sleep: 50 µA × 59.5s = 2975 µAs ≈ 3 mAs
- Average: (175 + 3) / 60 = 2.97 mAs/s = 2.97 mA
- 2000 mAh battery → ~672 hours ≈ 28 days

**Power regression test:** Measure average current draw before and after every significant firmware change. A spike in average current that reduces battery life by > 10% is a regression.

---

## Edge-to-cloud data reduction

Devices often generate more data than is useful to send to the cloud. Filter and aggregate at the edge.

### Filtering patterns

| Pattern | What it does | When to use |
|---------|-------------|------------|
| Threshold trigger | Send reading only when value crosses a threshold | Environmental monitoring (alert on anomaly, not every reading) |
| Delta trigger | Send only when value changes by > N | Slow-changing sensors (temperature, fill level) |
| Time aggregation | Send min/max/avg over a window | Battery-constrained device with high-frequency sensor |
| Change-of-state | Send only state transitions (on/off, open/closed) | Digital I/O monitoring |

**Rule:** Define the reporting interval and triggering policy in the device firmware config, not hardcoded. Push config updates via OTA to tune without reflashing.
