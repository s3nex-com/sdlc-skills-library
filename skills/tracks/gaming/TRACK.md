---
name: gaming
description: >
  game development, game engine, Unity, Unreal Engine, Godot, GameMaker,
  real-time multiplayer, game server, dedicated server, authoritative server,
  matchmaking, lobby, session, anti-cheat, EAC, BattlEye,
  in-app purchase, IAP, loot box, gacha, battle pass, virtual currency,
  live ops, live service game, game economy, player progression,
  tick rate, game loop, fixed timestep, client-side prediction,
  lag compensation, server reconciliation, rollback netcode, GGPO,
  NAT traversal, relay server, netcode, latency, ping,
  daily active users, DAU, monthly active users, MAU,
  session analytics, retention, churn, D1 D7 D30 retention,
  crash-free rate, ANR, game build pipeline, IL2CPP, Mono,
  Unity Cloud, Unreal pixel streaming, Steam, Epic Games Store,
  console certification, PlayStation, Xbox, Nintendo Switch
---

# Gaming track

## Purpose

Live-service games have a performance and reliability contract that typical web products do not: frame rate and tick rate are user-visible metrics measured in milliseconds, multiplayer state must be consistent across players despite network jitter, and live ops (content drops, events, balance changes) happen continuously without the ability to take the service down. A bad deploy at 6 PM on a Friday night during a major event means hundreds of thousands of concurrent players hit an error screen simultaneously. This track encodes the disciplines required to ship and operate live games safely: latency SLOs, authoritative server design, staged rollouts with kill switches, and session-level observability.

---

## When to activate

**Keyword signals:**
- "game development", "game server", "matchmaking", "anti-cheat"
- "tick rate", "client-side prediction", "lag compensation", "rollback netcode"
- "loot box", "battle pass", "in-app purchase", "live ops", "game economy"
- "DAU", "retention", "D1/D7/D30", "session analytics"
- Unity, Unreal, Godot game project (not a game-adjacent tool like a game analytics dashboard)

**Architectural signals:**
- System includes a real-time multiplayer game server
- Feature involves monetisation (IAP, virtual currency, loot boxes)
- Service measures and optimises tick rate, frame rate, or round-trip latency
- Live ops pipeline for content and balance changes without server restarts

---

## When NOT to activate

- Gamification elements in a SaaS or consumer app (points, badges, leaderboards) — use Consumer track; this track is for actual game servers and game-first products
- Internal game jam or prototype with no production deployment intent — apply Nano/Spike without a track
- Game analytics pipeline only (no game server, no IAP) — use Data platform / ML ops track
- Game marketing site or storefront with no game server backend

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| performance-reliability-engineering | Advisory | Mandatory (latency SLOs + server tick rate) | Mandatory + frame rate budget + concurrent player load test | Mandatory + full load test + chaos under player spike |
| observability-sre-practice | Advisory | Mandatory (session analytics + concurrent users + error rate) | Mandatory + per-region breakdown + tick rate monitoring | Mandatory + player-impact alerting + anomaly detection |
| feature-flag-lifecycle | Advisory | Mandatory (live ops content flags) | Mandatory + kill switch for every IAP surface | Mandatory + per-feature kill switch + staged rollout |
| release-readiness | Advisory | Mandatory + phased player rollout plan | Mandatory + canary region → staged rollout | Mandatory + canary + rollback criteria + peak-hours freeze |
| chaos-engineering | N/A | N/A | Conditional (if real-time multiplayer) | Mandatory (server failure under concurrent player load) |
| security-audit-secure-sdlc | Advisory | Mandatory (anti-cheat threat model + IAP receipt validation) | Mandatory + server-side authority verified | Mandatory |
| data-governance-privacy | Advisory | Mandatory (player data classification + COPPA if < 13) | Mandatory | Mandatory |

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | Define tick rate and latency SLO targets; identify peak concurrent player estimate; classify age-gating and regional regulatory requirements (COPPA, GDPR for minors, loot box disclosure laws) |
| Stage 2 (Design) | Authoritative server model documented (server-side authority for all game state changes); anti-cheat approach defined; live ops flag architecture designed; IAP receipt validation strategy chosen (server-side only) |
| Stage 3 (Build) | No client-authoritative state for any value-affecting game mechanic; all IAP receipts validated server-side; kill switches implemented for every live-ops surface |
| Stage 4 (Verify) | Load test to target concurrent player count; latency p99 measured against SLO; crash-free rate baseline established; IAP flow tested end-to-end in sandbox |
| Stage 5 (Ship) | Phased player rollout (soft launch region or % of players) before full release; rollback plan documented and rehearsed; peak-hours deployment freeze policy defined |
| Phase 3 (Ongoing) | Weekly: DAU, session length, crash-free rate, latency p99; monthly: D1/D7/D30 retention; post-event: player impact report after every major live ops event |

---

## Reference injection map

| When this skill fires | Also load these references |
|-----------------------|---------------------------|
| performance-reliability-engineering | `references/real-time-multiplayer-patterns.md`, `references/gaming-performance-budgets.md` |
| observability-sre-practice | `references/gaming-performance-budgets.md` |
| security-audit-secure-sdlc | `references/game-monetisation-guide.md` |
| feature-flag-lifecycle | `references/real-time-multiplayer-patterns.md` |
| release-readiness | `references/real-time-multiplayer-patterns.md` |
| data-governance-privacy | `references/game-monetisation-guide.md` |

---

## Reference files

- `references/real-time-multiplayer-patterns.md` — client-side prediction, server reconciliation, lag compensation, authoritative server model, rollback netcode (GGPO), dedicated vs relay vs P2P architecture, matchmaking design
- `references/game-monetisation-guide.md` — IAP flows, server-side receipt validation, virtual currency design, loot box odds disclosure (regulatory landscape by country), battle pass mechanics, anti-patterns (predatory mechanics, pay-to-win)
- `references/gaming-performance-budgets.md` — frame time budgets (60fps = 16ms, 120fps = 8ms), server tick rate selection and trade-offs, bandwidth per player estimates, server-side authority cost model, profiling toolchain (Unity Profiler, Unreal Insights, custom server metrics)

---

## Skill execution log

Track activation:
```
[YYYY-MM-DD] track-activated: gaming | mode: [Mode] | duration: project
```

Skill firings under this track:
```
[YYYY-MM-DD] performance-reliability-engineering | outcome: OK | note: 64-tick server, p99 latency 45ms at 100 concurrent players | track: gaming
```
