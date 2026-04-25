# OTA update patterns

OTA (over-the-air) update is the primary mechanism for patching deployed devices. A failed OTA that bricks a fleet is a worse outcome than the bug it was fixing. Design OTA update to be safe by default: rollback-capable, staged, and signed.

---

## Dual-partition (A/B) pattern

The safest and most common approach for devices with sufficient storage.

**Layout:**
```
+------------------+
| Bootloader       | (immutable; never overwritten)
+------------------+
| Partition A      | (running firmware)
+------------------+
| Partition B      | (new firmware download target)
+------------------+
| Data partition   | (config, certs — preserved across updates)
+------------------+
```

**Update flow:**
1. Download new firmware to Partition B while Partition A continues running
2. Verify signature and checksum of Partition B
3. Set boot flag to Partition B; reboot
4. Partition B boots and runs a self-test (health check)
5. If health check passes: confirm Partition B as active; Partition A becomes next update target
6. If health check fails: bootloader detects failed confirmation; reverts to Partition A

**Rollback trigger — automatic:**
- Boot count exceeded (e.g. 3 boot attempts without confirmation) → revert
- Self-test script returns non-zero → revert
- Watchdog timeout during startup → revert

**Rollback trigger — remote:**
- Backend detects elevated error rate from fleet cohort → push a revert command via device shadow
- Operator: trigger `device.revert()` on affected device group via fleet management API

---

## Single-partition with validation (resource-constrained devices)

For devices without sufficient storage for A/B.

**Flow:**
1. Download new firmware to a staging area in flash
2. Verify signature and checksum
3. Write to primary partition
4. Reboot and run self-test
5. If self-test fails: no automatic rollback available — device must be recovered manually or via a factory-safe minimal bootloader

**Risk:** Single-partition is higher-risk. A power failure during flash write or a bug in the new firmware that prevents boot can brick the device. Use only for severely memory-constrained devices; invest in A/B if at all possible.

**Mitigation:** Implement a fail-safe bootloader that can receive firmware over USB/serial even when the main partition is corrupt.

---

## Staged fleet rollout

Never push OTA to 100% of the fleet simultaneously. A bug that passes all tests may still affect a subset of hardware revisions, configurations, or network conditions.

**Rollout rings:**

| Ring | Size | Criteria | Wait time |
|------|------|---------|-----------|
| Canary | 1–10 devices | Developer-owned devices or a single known-stable site | 24 hours — monitor error rate |
| Ring 1 | 1–5% | Diverse device sample: different hardware revisions, geographies | 24–48 hours |
| Ring 2 | 10–20% | Broader sample; monitor fleet-level metrics | 48 hours |
| Ring 3 | 50% | Half the fleet | 24 hours |
| Full rollout | 100% | Only after all previous rings clear success criteria |  |

**Success criteria per ring:**
- OTA success rate ≥ 99.5%
- Device error rate within ±10% of pre-update baseline
- No increase in connectivity drops or watchdog resets

**Abort criteria:** If any ring fails success criteria, halt rollout and push a revert to affected devices before proceeding to the next ring.

---

## Firmware signing

All firmware images must be signed before distribution. The device verifies the signature before applying.

**Signing process:**
```
# 1. Build firmware
make firmware.bin

# 2. Sign (keep private key offline / in HSM)
openssl dgst -sha256 -sign firmware_key.pem -out firmware.bin.sig firmware.bin

# 3. Package (firmware + signature + metadata)
tar czf firmware-v1.2.3.tar.gz firmware.bin firmware.bin.sig manifest.json
```

**On-device verification (C pseudocode):**
```c
bool verify_firmware(const uint8_t *firmware, size_t len, const uint8_t *sig, size_t sig_len) {
    return ed25519_verify(sig, sig_len, firmware, len, PUBLIC_KEY_FROM_SECURE_STORAGE);
}

if (!verify_firmware(new_firmware, fw_len, signature, sig_len)) {
    log_error("Firmware signature invalid — refusing to flash");
    return UPDATE_REJECTED;
}
```

---

## Update failure handling

| Failure | Response |
|---------|---------|
| Download incomplete (network drop) | Retry with exponential backoff; resume from last byte if server supports range requests |
| Checksum mismatch | Discard download; retry |
| Signature invalid | Discard download; alert backend (possible tampering); do NOT apply |
| Self-test fails after boot | Automatic rollback to previous partition |
| Device unresponsive after update | Fleet management system detects missed heartbeat; escalates to manual recovery |

---

## Recovery of bricked devices

Design a recovery path before shipping:

- **Factory reset button:** Hardware button held during boot → boots into minimal recovery firmware that accepts a signed emergency update
- **USB/serial recovery:** Fail-safe bootloader accepts firmware over USB or UART even when main flash is corrupt
- **Documented procedure:** Written runbook for field technicians to recover a bricked device without shipping it back
