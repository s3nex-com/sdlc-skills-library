# Gaming performance budgets

## Frame time budgets

Frame rate is a user-visible metric. Players notice frame rate drops immediately. Define targets before implementation.

| Target FPS | Frame time budget | Typical use case |
|-----------|-----------------|-----------------|
| 30 FPS | 33.3 ms | Mobile games, console (base hardware) |
| 60 FPS | 16.7 ms | Standard PC and console; most multiplayer games |
| 120 FPS | 8.3 ms | Competitive PC, high-refresh consoles (PS5 Performance mode, Xbox Series X) |
| 144 FPS | 6.9 ms | High-refresh-rate PC monitors |

**Frame time allocation (example for a 60 FPS game):**

| System | Budget (ms) | Notes |
|--------|------------|-------|
| Game logic update | 2.0 ms | Physics, AI, game state |
| Rendering (CPU side) | 3.0 ms | Draw call submission, culling |
| Rendering (GPU side) | 8.0 ms | Actual GPU rendering |
| Network (input send + state receive) | 0.5 ms | Non-blocking; async |
| Audio | 0.5 ms | Mixing |
| UI | 1.0 ms | HUD, menus |
| Headroom | 1.7 ms | Spikes, GC pauses, OS preemption |

**Regression test:** Measure frame time in a standardised scene before every major release. Alert if p99 frame time exceeds budget × 1.5.

---

## Server tick rate

Tick rate is how many times per second the server processes the game state. Higher tick rate = more responsive gameplay at higher server cost.

| Tick rate | Update interval | Suitable for | Server cost |
|-----------|----------------|-------------|------------|
| 20 Hz | 50 ms | Casual/mobile, large battle royale | Low |
| 30 Hz | 33 ms | Standard multiplayer, MOBA | Low-medium |
| 60 Hz | 16.7 ms | Competitive FPS, action games | Medium |
| 128 Hz | 7.8 ms | Pro-tier FPS (CS2 matchmaking) | High |

**Trade-off:** Doubling tick rate roughly doubles server CPU cost and network bandwidth per connected player. Select the tick rate that matches your game's competitive integrity requirements — not the highest you can afford.

**Input buffering:** At 60 Hz tick rate, inputs arriving between server ticks are buffered and applied on the next tick. Design input buffering to be predictable (FIFO, bounded buffer).

---

## Bandwidth per player

Network bandwidth is a key cost and latency driver. Calculate before deploying server infrastructure.

**Typical bandwidth estimates:**

| Game type | Upstream per player | Downstream per player | Notes |
|-----------|-------------------|----------------------|-------|
| Turn-based | < 1 kbps | < 1 kbps | Input-only, very low frequency |
| MOBA / RTS | 5–15 kbps | 10–30 kbps | Fewer, slower state updates |
| Battle royale (100 players) | 10–20 kbps | 30–80 kbps | Large state, spatial culling critical |
| FPS (60 Hz tick, 10 players) | 20–40 kbps | 50–120 kbps | High tick rate, frequent updates |
| FPS (128 Hz tick, 10 players) | 40–80 kbps | 80–200 kbps | Pro-tier; significant infrastructure cost |

**Bandwidth optimisation techniques:**
- **Interest management / spatial culling:** Only send a player state updates for objects within their visible area. In a 100-player battle royale, only send updates for the 20–30 nearest players.
- **Delta compression:** Send only changed fields, not the full state every tick.
- **Snapshot interpolation:** Client renders between received snapshots, reducing the required update frequency.

---

## Server-side authority cost model

Running authoritative game servers is expensive at scale. Model costs before committing to architecture.

**Example: FPS, 10 players, 60 Hz tick, 1000 concurrent matches**

| Resource | Estimate |
|---------|---------|
| CPU per match | 0.25 vCPU |
| Memory per match | 512 MB |
| Bandwidth per match | 1 Mbps aggregate |
| Total CPU (1000 matches) | 250 vCPU |
| Total memory | 512 GB |
| Total bandwidth | 1 Gbps |

At ~$0.04/vCPU-hour on a compute-optimised instance:  
250 vCPU × $0.04 = $10/hour = ~$7,200/month at 100% utilisation

Real games have variable utilisation (peak hours vs off-peak). Use spot instances for game servers where match lengths are predictable (< 30 min); use reserved/on-demand for minimum viable capacity.

---

## Profiling toolchain

| Engine | CPU profiler | GPU profiler | Network profiler |
|--------|------------|-------------|-----------------|
| Unity | Unity Profiler, Deep Profile mode | Xcode Instruments (iOS), RenderDoc (PC) | Unity Multiplayer Profiler |
| Unreal | Unreal Insights, Unreal Frontend | RenderDoc, PIX (Windows), Xcode (iOS) | Unreal Network Profiler |
| Godot | Godot Profiler (built-in) | RenderDoc | Wireshark + custom logging |
| Custom | perf (Linux), VTune (Intel), Instruments (macOS) | RenderDoc, PIX, NSight | Wireshark, custom metrics |

**Profiling cadence:**
- Before every release: run the profiler in the standard scene and compare to baseline
- After every significant feature: profile in isolation to measure its contribution
- Monthly: measure a production sample (add server-side frame time metrics to observability stack)
