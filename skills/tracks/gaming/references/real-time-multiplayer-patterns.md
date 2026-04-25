# Real-time multiplayer patterns

## Authoritative server model

The server is the source of truth for all game state. Clients are input terminals and display surfaces. This is the foundation of any anti-cheat system.

**Rule:** Clients submit inputs (button presses, direction vectors, actions). The server applies game logic and sends back the resulting state. Clients never dictate state — only request it.

**What must be server-authoritative:**
- Player position and velocity (otherwise speed-hacking is trivial)
- Hit detection and damage (otherwise aimbots can invent hits)
- Inventory and item state (otherwise item duplication is trivial)
- Match score and win conditions
- Any state that has economic or competitive value

**What can be client-predicted (for responsiveness):**
- Visual position of the local player (cosmetic, corrected by server)
- Particle effects and sound (purely cosmetic)
- UI state (locally predicted, no economic value)

---

## Client-side prediction

Players cannot tolerate waiting for a full round-trip to see the result of their input. Client-side prediction makes the game feel responsive while keeping the server authoritative.

**Flow:**
1. Client applies input locally and immediately (predicts the result)
2. Client sends input to server with a timestamp/sequence number
3. Server processes input, computes authoritative state, sends back
4. Client receives authoritative state and reconciles

**Reconciliation:**
- If server state matches client prediction: nothing to do
- If server state differs: snap or smoothly interpolate to authoritative state

```
Client:
  local_state = apply_input(current_state, input)  // immediate visual response
  send_to_server(input, sequence_number)

Server:
  authoritative_state = apply_input(server_state, input)
  send_to_client(authoritative_state, sequence_number)

Client on receive:
  if local_state != authoritative_state:
      reconcile(local_state, authoritative_state)  // snap or lerp
```

---

## Lag compensation

Players in different geographies have different latency to the server. Without lag compensation, a player with 200ms latency fires at where the target was 200ms ago — a miss even if the aim was perfect on their screen.

**Server-side lag compensation:**
1. Server maintains a history buffer of all game object positions (ring buffer, last 1000ms)
2. When a hit event arrives from a client, rewind server state to `timestamp - client_latency`
3. Evaluate the hit in the rewound state
4. Apply the result in present server state

**Implementation note:** This gives high-latency players a small advantage over low-latency players (they can hit people who have since moved away). Cap lag compensation at a maximum rewind time (e.g. 150ms) to bound this effect.

---

## Rollback netcode (GGPO)

Standard for fighting games and precision-critical PvP. Trades network bandwidth for frame-perfect fairness.

**Flow:**
1. Both clients run the same deterministic game simulation
2. Each client sends inputs for every frame to the other
3. When inputs arrive out of order: rollback N frames, apply the correct input, re-simulate forward
4. Both clients converge on identical state

**Requirements:**
- Deterministic simulation: same inputs must produce identical state on every machine
- No floating-point operations (use fixed-point math)
- Fast resimulation: must be able to re-simulate 8–12 frames in < 1ms
- Complete state snapshot: rollback requires snapshotting full game state per frame

**When to use:** Fighting games, racing games, any game where frame-perfect input timing matters. Not appropriate for games with large world states (too expensive to snapshot and rollback).

---

## Network architecture choices

| Architecture | Latency | Cost | Anti-cheat | Use when |
|-------------|---------|------|-----------|----------|
| Dedicated server (authoritative) | Medium (1 RTT to server) | High (server fleet cost) | Strong (server is authority) | Competitive multiplayer, FPS, any game with cheating concern |
| Relay server | Higher (2 RTT — client → relay → client) | Medium | Moderate (relay sees all traffic) | Casual games, turn-based, latency-tolerant |
| P2P with host | Lowest (direct) | Lowest | Weak (host can cheat) | Small-scale, casual, no competitive integrity requirement |
| P2P with deterministic lockstep | Low | None | Moderate (replays possible) | RTS, 4X, turn-based strategy |

---

## Matchmaking design

**Target:** Match players of similar skill within an acceptable wait time.

**Skill measurement:** ELO or TrueSkill rating. Start new players at the median rating; adjust after each match.

**Matchmaking parameters (tune to your game):**

| Parameter | Default |
|-----------|---------|
| Max skill gap in a match | ±200 ELO |
| Max wait before widening skill gap | 30 seconds |
| Skill gap expansion rate | +50 ELO per 10 seconds of waiting |
| Max skill gap (absolute cap) | ±500 ELO |
| Max wait before accepting any match | 90 seconds |

**Region selection:** Match within the same region first. Expand to cross-region only if wait exceeds threshold (60s). Measure and report cross-region match rate — if it climbs above 15%, the player base in that region is too sparse to support the game.

**Latency gating:** Measure latency between potential match participants before confirming the match. Reject if any participant's p50 latency to the server exceeds threshold (e.g. 120ms for an FPS).
