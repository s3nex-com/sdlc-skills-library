---
name: iot-embedded
description: >
  firmware, embedded system, RTOS, real-time operating system, FreeRTOS, Zephyr,
  connected device, IoT, Internet of Things, Industrial IoT, IIoT, edge computing,
  edge device, OTA update, over-the-air update, MQTT, CoAP, Zigbee, Z-Wave,
  Bluetooth Low Energy, BLE, constrained device, microcontroller, MCU, Arduino,
  ESP32, STM32, Nordic, sensor, actuator, gateway, fleet management,
  device provisioning, device certificate, mTLS, mutual TLS,
  secure boot, device attestation, TPM, hardware security module,
  memory-constrained, power budget, battery life, watchdog timer,
  device shadow, digital twin, telemetry pipeline
---

# IoT / Embedded track

## Purpose

Embedded and IoT systems carry risks that cloud services do not: devices ship to the physical world where patching is slow (OTA pipelines are complex), failures may have safety implications, and the attack surface includes hardware (JTAG, UART, physical access). A bug that passes staging can reach 10,000 devices before the next OTA window. This track enforces the discipline required to ship device firmware and connected-device software safely: threat modelling at the hardware boundary, OTA rollback by default, fleet-safe rollout gates, and ongoing fleet health monitoring.

---

## When to activate

**Keyword signals:**
- "firmware", "embedded", "RTOS", "OTA update", "over-the-air"
- "IoT", "connected device", "edge device", "edge computing"
- "MQTT", "CoAP", "Zigbee", "BLE", "device provisioning"
- "secure boot", "device attestation", "mTLS device"
- "fleet management", "device shadow", "digital twin"
- "microcontroller", "MCU", "STM32", "ESP32", "Nordic", "FreeRTOS", "Zephyr"

**Architectural signals:**
- Software runs on or communicates with a device deployed in the physical world
- OTA update pipeline exists or is being designed
- Device fleet size is > 1 (any deployed volume)
- Device has network connectivity but limited compute or storage
- Safety or reliability consequences from device failure (industrial, medical-adjacent, automotive)

---

## When NOT to activate

- Mobile app that communicates with IoT devices but runs only on iOS/Android — use Mobile track for the app; IoT track for the firmware/backend
- Pure cloud-side IoT backend with no firmware or edge code in scope — no device-specific obligations apply
- Analytics dashboard consuming IoT telemetry — no device code, no elevated requirements
- Prototype or one-off device with no fleet deployment intent — apply Standard mode manually without this track

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| security-audit-secure-sdlc | Mandatory + device threat model | Mandatory + device threat model | Mandatory + hardware attack surface (JTAG/UART disabled, debug flags off) | Mandatory + third-party hardware security review |
| devops-pipeline-governance | Advisory | Mandatory + OTA pipeline | Mandatory + OTA pipeline + testnet fleet gate | Mandatory + signed firmware, staged rollout gates |
| disaster-recovery | Advisory | Mandatory (OTA rollback plan) | Mandatory + dual-partition OTA tested | Mandatory + factory reset and re-provisioning runbook |
| performance-reliability-engineering | Advisory | Mandatory (memory + power budget) | Mandatory + cold start + watchdog timeout + power regression tests | Mandatory + soak test on target hardware |
| observability-sre-practice | Advisory | Mandatory (device telemetry + fleet error rate) | Mandatory + per-device-class breakdown + OTA success rate | Mandatory + anomaly detection on fleet telemetry |
| release-readiness | Advisory | Mandatory + fleet rollout plan | Mandatory + staged fleet rollout (canary → 10% → 100%) | Mandatory + staged rollout + kill switch + rollback criteria |
| data-governance-privacy | Advisory | Mandatory (PII from device sensors classified) | Mandatory | Mandatory |

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | Identify device constraints (memory, CPU, power budget); define minimum OS version and target hardware; classify safety implications of failure |
| Stage 2 (Design) | OTA update strategy documented (dual-partition / single-partition + validation); rollback trigger conditions defined; device threat model (physical access, JTAG, supply-chain) produced; certificate provisioning scheme chosen |
| Stage 3 (Build) | Secure boot enabled; debug interfaces (JTAG, UART) disabled or access-controlled in production builds; watchdog timer configured; memory-safe coding patterns applied |
| Stage 4 (Verify) | Tested on physical target hardware (not emulator only); OTA rollback tested end-to-end; memory leak test (minimum 24-hour soak); power consumption measured against budget |
| Stage 5 (Ship) | Staged fleet rollout (canary cohort before full fleet); rollback plan documented and rehearsed; firmware signed and signature verified on device; device provisioning runbook complete |
| Phase 3 (Ongoing) | Weekly OTA success rate and fleet error rate review; quarterly firmware version spread report (EOL version identification); annual hardware end-of-life assessment |

---

## Reference injection map

| When this skill fires | Also load these references |
|-----------------------|---------------------------|
| security-audit-secure-sdlc | `references/device-security-guide.md` |
| devops-pipeline-governance | `references/ota-update-patterns.md` |
| disaster-recovery | `references/ota-update-patterns.md` |
| performance-reliability-engineering | `references/edge-computing-patterns.md` |
| observability-sre-practice | `references/edge-computing-patterns.md` |
| release-readiness | `references/ota-update-patterns.md` |

---

## Reference files

- `references/device-security-guide.md` — secure boot, device attestation, certificate provisioning, mTLS device-to-cloud, JTAG/UART hardening, common IoT CVE patterns, supply-chain risks
- `references/ota-update-patterns.md` — dual-partition A/B updates, delta updates, rollback triggers and validation, staged fleet rollout (canary → rings → full fleet), update failure handling and recovery
- `references/edge-computing-patterns.md` — offline-first for devices, sync reconciliation after reconnect, data compression for constrained bandwidth, power budgeting, edge-to-cloud data reduction patterns

---

## Skill execution log

Track activation:
```
[YYYY-MM-DD] track-activated: iot-embedded | mode: [Mode] | duration: project
```

Skill firings under this track:
```
[YYYY-MM-DD] devops-pipeline-governance | outcome: OK | note: OTA pipeline with dual-partition rollback; staged rollout plan approved | track: iot-embedded
```
