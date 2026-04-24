# Windowing and watermarks

Streams are unbounded. Aggregations need bounds. Windowing is how you carve a stream into finite pieces, and watermarks are how you decide when a piece is "done" so you can emit a result. Getting either wrong produces wrong answers — usually silently, usually discovered in production by an analyst who notices numbers do not match.

---

## Window types

### Tumbling windows

Fixed-size, non-overlapping, contiguous. Every event belongs to exactly one window. Use for periodic aggregations with no overlap — hourly counts, per-minute p99 latency, daily totals.

### Sliding windows

Fixed-size, overlapping by a slide interval. Each event belongs to `window_size / slide_interval` windows. Use for rolling averages and moving sums with smoothing — "messages per minute averaged over the last 5 minutes, updated every minute".

Cost: with small slides, each event fans out to many windows. A 1-hour window sliding every 1 second = 3600 windows per event. State balloons. Tune slide against query frequency and memory budget.

### Session windows

Dynamically sized, bounded by inactivity gaps. Windows close after a gap timeout with no events for the session key. Use for user activity sessions and session-scoped aggregations — "total actions per user session", "session duration distribution". Session windows are keyed; each key has its own session timer.

### Global windows

A single window covering all events forever. Only useful with a custom trigger (count-based, for example). Use when custom triggering is needed — emit after every 100 events regardless of time.

---

## Event time vs processing time

**Event time** is the timestamp embedded in the event, set by the producer, representing when the thing actually happened.

**Processing time** is the wall-clock time on the stream processor when the event is observed.

These are different because of network delay, producer clock skew, retries, and — most importantly — partitioned brokers where one partition may lag another by seconds or minutes. Computing "events in the last 5 minutes" against processing time is easy but wrong: during a partition lag event, your "5-minute window" in processing time could cover 30 minutes of event time from one partition and 1 minute from another.

**Use event time almost always.** Use processing time only when:

- The event carries no reliable timestamp and you cannot add one.
- The aggregation is explicitly about observation latency (for example, "events received in the last 5 seconds" for SLA measurement).
- You are doing best-effort debug tooling and precision does not matter.

Every production streaming system should assign event time at the producer, serialize it into the event, and configure the processor to use event time.

---

## Watermarks

A watermark is the stream processor's declaration: "I do not expect any more events with timestamp less than T." When the watermark passes a window's end boundary, the window is closed and its result emitted. Watermarks bridge the gap between unbounded event time and the need to emit finite results.

### Watermark generation strategies

**Perfect watermark** — watermark equals max event timestamp seen. Correct only with strict in-order arrival per partition, which almost never holds.

**Heuristic (bounded out-of-orderness)** — watermark = max event time seen − fixed lateness bound. Default in Flink and Kafka Streams. Pick the bound against observed producer-side delay.

```java
// Flink — bounded out-of-orderness of 10 seconds
WatermarkStrategy<Event> strategy = WatermarkStrategy
    .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
    .withTimestampAssigner((event, ts) -> event.getEventTime());
```

Ten seconds is a starting point; measure actual producer-side delay and set the bound to the p99. Too tight and you drop legitimate late data; too loose and results emit too slowly.

**Per-partition watermarks** — each input partition emits its own watermark and the operator watermark is the **minimum** across partitions. This is the correct behaviour and the default in Flink. A single idle partition stalls the global watermark, which is why idle partition detection is essential.

```java
WatermarkStrategy<Event> strategy = WatermarkStrategy
    .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
    .withIdleness(Duration.ofMinutes(1))  // treat partition as idle after 1min no data
    .withTimestampAssigner((event, ts) -> event.getEventTime());
```

Without `withIdleness` (or equivalent in Kafka Streams via `max.task.idle.ms`), a single partition with no traffic holds the entire job's watermark back and no windows close.

---

## Late data handling

Data arrives late — after the watermark has passed its window's end. Every real system has late data; the only question is what to do with it.

### Option 1: drop and count

Drop the late event, increment a counter, emit a metric. Simple, lossy, acceptable for best-effort analytics. Flink's default behaviour when no allowed lateness and no side output is configured — always add a metric so the drops are visible.

### Option 2: allowed lateness

Keep the window's state around for an extra period after the watermark passes. Late events within the lateness window re-fire the computation and emit updated results.

```java
stream
    .keyBy(Event::getKey)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .allowedLateness(Time.minutes(2))
    .sideOutputLateData(lateTag)
    .aggregate(new CountAggregator());
```

The downstream consumer must be idempotent or overwrite-safe — the same window key will produce multiple results. If the sink is a database keyed by window boundary, updates work. If the sink is an append-only topic, you need upstream deduplication or explicit retraction support.

### Option 3: side outputs

Route late events to a separate stream for manual inspection, correction pipelines, or delayed-arrival reports.

```java
OutputTag<Event> lateTag = new OutputTag<Event>("late-events"){};
SingleOutputStreamOperator<Result> main = stream
    .window(...)
    .sideOutputLateData(lateTag)
    .aggregate(...);
DataStream<Event> lateStream = main.getSideOutput(lateTag);
lateStream.addSink(lateSink);
```

### Trigger-based early/on-time/late firing

For long windows where an early estimate is useful, combine a continuous trigger with allowed lateness — the window emits every N minutes of event time (early), once when the watermark passes (on-time), and on each late event within the lateness bound. Downstream must handle multiple emissions per window and apply updates idempotently.

---

## Worked example — Flink

Requirement: count events per user per 1-minute tumbling window on event time with 15-second bounded out-of-orderness, emit late data to a side output.

```java
DataStream<Event> events = env.fromSource(
    kafkaSource,
    WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(15))
        .withIdleness(Duration.ofMinutes(1))
        .withTimestampAssigner((event, ts) -> event.getEventTime()),
    "events"
);

OutputTag<Event> lateTag = new OutputTag<Event>("late"){};

SingleOutputStreamOperator<WindowedCount> counts = events
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .allowedLateness(Time.seconds(30))
    .sideOutputLateData(lateTag)
    .aggregate(new CountAggregator(), new WindowMetadataFunction());

counts.addSink(sinkFunction);
counts.getSideOutput(lateTag).addSink(lateSinkFunction);
```

Enable checkpointing for exactly-once state recovery: `env.enableCheckpointing(30_000)` and `setCheckpointingMode(EXACTLY_ONCE)`. Without checkpointing, a task failure loses all in-memory window state.

---

## Worked example — Kafka Streams

```java
KStream<String, Event> events = builder.stream(
    "events",
    Consumed.with(Serdes.String(), eventSerde)
        .withTimestampExtractor((record, prev) -> record.value().getEventTime())
);

events.groupByKey()
    .windowedBy(TimeWindows.ofSizeAndGrace(
        Duration.ofMinutes(1),
        Duration.ofSeconds(30)))   // grace period = allowed lateness
    .count(Materialized.as("counts-store"))
    .toStream()
    .to("windowed-counts", Produced.with(windowedStringSerde, Serdes.Long()));
```

Set `max.task.idle.ms=60000` at the streams level for idle partition handling. Without it, a single quiet partition blocks stream-time advance and windows never close.

---

## Anti-patterns to reject

- **Processing time "for simplicity"**: pay the cost to propagate event time through the producer; do not save yourself a field and then explain in the postmortem why the daily report is 13% off.
- **Out-of-orderness = 0** on a multi-partition topic: first rebalance or network blip drops legitimate events.
- **Out-of-orderness = 1 hour "to be safe"**: windows emit 1 hour late. Pick the measured p99, not the paranoid maximum.
- **Allowed lateness with a non-idempotent sink**: the same window re-fires and produces inconsistent results.
- **No idle-partition handling**: works in load test where every partition has traffic; breaks in production where one partition is a tenant that went quiet at midnight.
- **Windowing in processing time then claiming exactly-once**: the broker can be exactly-once and the computation still wrong.

---

## What to document in the design doc

For every windowed aggregation, document:

1. **Window type** (tumbling / sliding / session / global) and size.
2. **Time characteristic** (event time / processing time) and justification.
3. **Watermark strategy** and bounded out-of-orderness value, with the measurement that backs the value.
4. **Idle partition handling** — explicit `withIdleness` or `max.task.idle.ms` value.
5. **Late data policy** — drop, allowed lateness, or side output; with the downstream idempotency story.
6. **Trigger** if non-default (early/on-time/late firing) and the downstream handling of multiple emissions.

If any of these is unspecified, the windowing design is incomplete and will produce wrong numbers.
