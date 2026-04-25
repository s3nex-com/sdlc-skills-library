# Device security guide

## Threat model for embedded / IoT systems

IoT devices face threats that cloud services do not: physical access (attacker can open the device, probe JTAG, dump flash), supply-chain attacks (malicious firmware at manufacturing), and fleet-scale exploits (one bug deployed to 10,000 devices simultaneously). Model threats in these five areas before shipping firmware.

| Threat area | Attack surface | Mitigation |
|-------------|---------------|-----------|
| Physical access | JTAG, UART, debug ports, flash read | Disable debug interfaces in production builds; use fuse bits or eFuse to lock JTAG after manufacturing |
| Firmware tampering | OTA delivery, local flash write | Firmware signing + signature verification on boot |
| Communication interception | Device-to-cloud channel | mTLS with device certificate; no plain HTTP |
| Identity spoofing | Device impersonation to backend | Unique per-device certificate provisioned at manufacture; certificate pinning |
| Supply chain | Malicious pre-installed firmware | Secure boot anchored to hardware root of trust; attestation on first connection |

---

## Secure boot

Secure boot ensures that only cryptographically signed firmware runs on the device.

**Chain of trust:**
1. Hardware root of trust (ROM bootloader, hardware immutable) verifies Stage 1 bootloader signature
2. Stage 1 bootloader verifies Stage 2 / OS signature
3. OS verifies application firmware signature

**Implementation requirements:**
- [ ] Public key of the signing authority burned into hardware (eFuse, OTP, or TPM) — not in firmware where it can be replaced
- [ ] Failed signature verification prevents boot (does not fall through to unsigned firmware)
- [ ] Revocation: mechanism exists to update trusted keys without relying on the key being revoked
- [ ] Tested: physically flashed with tampered firmware and verified it refuses to boot

---

## Device certificate provisioning

Every device must have a unique identity credential. Shared credentials mean a compromise of one device compromises all.

**Provisioning at manufacture (preferred):**
1. Unique key pair generated on-device during manufacturing (key never leaves the device)
2. CSR (Certificate Signing Request) sent to a PKI CA
3. Signed device certificate written to secure storage
4. Certificate bound to device serial number in manufacturing database

**Provisioning on first boot (alternative for small fleets):**
1. Device generates key pair on first boot
2. Claims a one-time registration token (pre-loaded) to authenticate to the provisioning service
3. Provisioning service issues a signed certificate and invalidates the token

**Certificate requirements:**
- [ ] Unique per device (never shared)
- [ ] Contains device serial number or hardware ID as Subject CN or SAN
- [ ] Short validity period with automatic renewal (≤ 2 years)
- [ ] Rotation procedure: new cert provisioned via OTA before expiry

---

## mTLS — device-to-cloud communication

All device-to-cloud communication must use mutual TLS. One-way TLS (only the server presents a certificate) is not acceptable for IoT — the backend cannot verify which device it is talking to.

**mTLS handshake:**
1. Server presents its certificate → device verifies against pinned CA
2. Device presents its certificate → backend verifies against device certificate database
3. If both pass: connection established; device identity confirmed

**Certificate pinning on the device:**
- Pin the backend CA certificate (not the leaf) to allow backend cert rotation without firmware update
- Reject any connection where the backend certificate does not chain to the pinned CA

**AWS IoT Core / GCP Cloud IoT / Azure IoT Hub:** All three support device certificates and mTLS natively. Use the platform's device registry to store and verify device identity.

---

## Debug interface hardening

| Interface | Production requirement |
|-----------|----------------------|
| JTAG | Disabled (eFuse or fuse bit) after manufacturing test |
| UART | Disabled or password-protected in production builds |
| USB DFU | Disabled or restricted to signed payloads only |
| Debug logging | Stripped from production builds (no verbose logging to UART) |
| Serial console | Disabled or login-protected |

Use build flags to enforce this:
```c
// production_build.h
#define DISABLE_JTAG 1
#define DISABLE_UART_DEBUG 1
#define STRIP_DEBUG_SYMBOLS 1
```

---

## Common IoT CVE patterns

| Pattern | Example | Prevention |
|---------|---------|-----------|
| Hardcoded credentials | Factory default password never changed | Unique per-device credentials; no defaults |
| Unencrypted protocol | MQTT without TLS | mTLS mandatory |
| Missing firmware signature | OTA update accepts any binary | Signed firmware, signature verified before flash |
| Verbose error messages | Stack trace in UART output | Strip debug output in production |
| No rate limiting on auth | Brute-force on device portal | Lockout after N failures; no open admin portal |
| Outdated dependencies | Known-vulnerable mbedTLS version | Pin dependency versions; monitor for CVEs; OTA for security patches |
