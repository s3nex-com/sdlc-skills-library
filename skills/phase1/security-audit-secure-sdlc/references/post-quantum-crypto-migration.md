# Post-quantum cryptography (PQC) migration

A concrete roadmap for small engineering teams. The goal is not to deploy PQC everywhere tomorrow — it is to know what crypto you use, make it swappable, and migrate on a staged timeline aligned with NIST and NSA guidance.

---

## Why migrate now

- **Quantum threat timeline.** Cryptographically relevant quantum computers (CRQCs) are not here today, but credible forecasts place them in the 2030s. Waiting until they exist is too late.
- **"Harvest now, decrypt later" (HNDL)** attacks are happening today. Adversaries capture TLS traffic, encrypted archives, and signed artifacts now, intending to decrypt once a CRQC exists. Anything confidential with a shelf life past ~2030 is already at risk.
- **Long-lived certificates and signed artifacts** cannot be swapped overnight. A 10-year device certificate issued in 2026 is still valid in 2036. Root CAs, firmware signing keys, and long-term archival signatures need PQC **before** the window closes.
- **Regulatory pressure.** US federal systems have hard deadlines (see NSA CNSA 2.0 below). Teams serving those customers need PQC readiness now, not after standards are done being debated.

---

## NIST PQC standards (finalised 2024)

All three are finalised FIPS standards as of August 2024:

| Standard | Name | Purpose | Notes |
|----------|------|---------|-------|
| **FIPS 203** | **ML-KEM** (Module-Lattice Key Encapsulation) | Key establishment (replaces RSA-OAEP / ECDH) | Based on CRYSTALS-Kyber. Primary KEM for TLS, VPN, hybrid PKI. |
| **FIPS 204** | **ML-DSA** (Module-Lattice Digital Signature) | Digital signatures (replaces RSA-PSS / ECDSA) | Based on CRYSTALS-Dilithium. Primary signature algorithm for most use cases. |
| **FIPS 205** | **SLH-DSA** (Stateless Hash-based Digital Signature) | Digital signatures, conservative fallback | Based on SPHINCS+. Slower and larger than ML-DSA, but built only on hash function security — the most conservative backstop. Use for root-of-trust signatures where longevity matters most. |

A fourth standard, **FN-DSA** (FALCON-based), is still being finalised as FIPS 206 for signature use cases that need small signatures.

---

## Phase 0: crypto inventory (do this first, target: by end of 2026)

You cannot migrate what you do not know you have. Build a crypto inventory.

### What to audit

Search for every use of:
- **RSA** (PKCS#1, OAEP, PSS) in any form
- **ECDSA** (P-256, P-384, P-521, secp256k1)
- **ECDH / ECDHE** (key exchange)
- **Diffie-Hellman** (classical finite-field DH)
- **DSA** (legacy; should already be gone)

### Where to look

- **Source code** — grep for `RSA`, `ECDSA`, `ECDH`, `ed25519` (note: Ed25519 is not quantum-safe but is not on the initial migration list because it's a signature system that is easier to swap than RSA/ECDSA embedded in long-term signatures). Check crypto library calls, cipher suite configs.
- **Config files** — TLS cipher suite allowlists, SSH host key types, VPN configs, IPsec proposals.
- **X.509 certificates** — run `openssl x509 -text` across your cert inventory. Look at `Public Key Algorithm` and `Signature Algorithm` fields. Record issuer, subject, validity, and key algorithm for every cert.
- **PKI roots and intermediates** — your internal CA, any customer-trusted CAs. These are the longest-lived and hardest to migrate.
- **Signed artifacts** — container image signatures (cosign), SBOM attestations, firmware signatures, update bundles, JWT signing keys.
- **Dependencies** — your language crypto library, TLS library (OpenSSL, BoringSSL, rustls, Go crypto), JWT libraries.
- **Secrets managers** — HSM / KMS key types in use.
- **HSMs / hardware tokens** — most current hardware does not yet support PQC algorithms. Upgrade roadmap matters.

### Inventory output format

```
## Crypto inventory — 2026-04-20

| ID | Surface | Algorithm | Key size | Lifetime | HNDL risk | Owner | Migration phase |
|----|---------|-----------|----------|----------|-----------|-------|-----------------|
| C-001 | Public TLS edge | ECDHE + ECDSA-P256 | 256 | 1-year certs | Low (ephemeral) | Platform | 2027 hybrid |
| C-002 | Internal mTLS CA root | RSA-4096 sign | 4096 | 10-year root | High | Platform | 2027 hybrid urgent |
| C-003 | Device certificates (shipped) | ECDSA-P256 | 256 | 10-year | High (HNDL) | Device team | 2027 hybrid critical |
| C-004 | JWT signing | RSA-2048 | 2048 | Rotated 1yr | Low | Identity | 2028 PQC ready |
| C-005 | Container image signing (cosign) | ECDSA-P256 | 256 | Per release | Medium | CI team | 2028 hybrid |
| C-006 | Backup encryption (KMS) | RSA-OAEP-2048 | 2048 | Indefinite | High | Platform | 2027 hybrid critical |
```

---

## Phase 1: crypto-agility (do this in parallel with inventory)

Do not hardcode algorithm choices. Wrap crypto in an abstraction so the algorithm is a configuration choice, not a code change.

### Anti-pattern

```python
# DON'T — hardcoded
from cryptography.hazmat.primitives.asymmetric import rsa, padding
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
signature = key.sign(data, padding.PSS(...), hashes.SHA256())
```

### Pattern

```python
# DO — wrapped in abstraction with algorithm from config
class Signer:
    def __init__(self, algo: str):
        self._impl = SIGNER_IMPLS[algo]()   # RSA-PSS, ECDSA, ML-DSA, SLH-DSA

    def sign(self, data: bytes) -> bytes:
        return self._impl.sign(data)

# config: signer.algo = "ml-dsa-65"  (was "ecdsa-p256")
```

When a PQC algorithm is added to the library, swap is a config rollout, not a rewrite.

### What to abstract

- **Signature verification and signing** (most common swap target)
- **Key encapsulation** (TLS, envelope encryption)
- **Certificate issuance path** (internal CA)
- **Key rotation** (must handle mixed-algorithm periods)

### What else to design for
- **Algorithm identifiers in signed envelopes.** Every signed blob includes the algorithm used, so verifiers know which scheme to apply. This is standard in JWS, CMS, and X.509 — enforce it in your custom formats too.
- **Larger key and signature sizes.** PQC keys are bigger (ML-DSA-65 public key ~1,952 bytes, signature ~3,309 bytes; SLH-DSA signatures are tens of KB). Buffer sizes, storage columns, network MTUs, and QR codes all need review.

---

## Phase 2: hybrid (target: by 2027)

A hybrid construction combines a classical algorithm (ECDH, ECDSA) with a PQC algorithm (ML-KEM, ML-DSA). The combined output is secure if **either** one remains secure. This is the only safe way to deploy PQC in production before the algorithms are fully hardened.

- **Hybrid key establishment:** `X25519 + ML-KEM-768` is the leading TLS hybrid; IETF is standardising it (draft progressed to RFC in 2025).
- **Hybrid signatures:** composite or concatenated `ECDSA || ML-DSA` depending on protocol support. X.509 composite signatures still maturing in IETF drafts.
- **Deploy hybrid first**, PQC-only second. If the PQC algorithm is later found flawed, the classical half keeps you secure.

### Hybrid deployment order (prioritise by HNDL risk)

1. **Internal CA roots and intermediates** (ultra-long-lived, highest HNDL exposure).
2. **Device certificates** shipped on hardware with multi-year validity.
3. **Backup and archive encryption** (data at rest with indefinite shelf life).
4. **Public TLS edges** (short-lived, but foundational).
5. **Artifact signing** (container images, SBOMs, firmware).
6. **JWT and session tokens** (short-lived, lower priority).

---

## Phase 3: PQC-only (target: by 2030)

By 2030, new deployments default to PQC. Classical algorithms are phased out except where legacy compatibility is required. This aligns with NSA CNSA 2.0 (see below).

Hybrid remains acceptable indefinitely where interop demands it, but the PQC half must be the primary security assumption.

---

## Implementation status in crypto libraries (as of 2026)

| Library | ML-KEM | ML-DSA | SLH-DSA | Hybrid TLS | Notes |
|---------|--------|--------|---------|------------|-------|
| **OpenSSL 3.5+** | Yes | Yes | Yes | Yes (X25519MLKEM768) | Production-grade PQC landed in 3.5 (April 2025). |
| **BoringSSL** | Yes | Yes | Experimental | Yes | Chrome/Chromium TLS uses hybrid ML-KEM by default in 2025+. |
| **rustls** | Partial | Partial | No | Experimental feature flag | Lagging; track `rustls-post-quantum` crate. |
| **Go crypto/tls** | Yes (1.24+) | Planned | No | Yes (1.24+) | ML-KEM hybrid lands in the stdlib. |
| **liboqs** | Yes | Yes | Yes | Via oqs-provider for OpenSSL | Reference implementation; not for production crypto alone — use behind OpenSSL or a vetted library. |
| **HSMs** | Limited | Limited | Limited | Rare | Major HSM vendors shipping PQC-capable firmware through 2025–2026. Check your model. |

Always validate that the library's PQC implementation is FIPS-validated if you have compliance requirements. Implementation bugs (not algorithm weaknesses) are the near-term risk.

---

## Caveats — read before deploying

- **Performance.** ML-DSA signing is ~10× slower than Ed25519; ML-KEM is faster than RSA-2048 but slower than X25519. Benchmark your hot paths.
- **Size.** ML-DSA signatures are ~3 KB; SLH-DSA signatures are 7–50 KB. TLS handshake size grows. Mobile, embedded, and QR code scenarios need planning.
- **Memory.** PQC operations use more stack memory — review embedded device budgets.
- **Protocol support.** Not every protocol has standardised PQC yet. SSH has an early draft; IPsec/IKEv2 is draft. X.509 composite signatures still in flux.
- **Implementation maturity.** Algorithms are mathematically standardised, but library implementations are younger than classical equivalents. Prefer libraries with fuzzing coverage and public vulnerability history.
- **Don't roll your own.** This applies doubly to PQC. Use OpenSSL, BoringSSL, or a vetted language-specific wrapper. Never wire primitives directly from a research implementation into production.

---

## US federal deadlines (NSA CNSA 2.0)

The NSA's Commercial National Security Algorithm Suite 2.0 sets dates for National Security Systems. Non-federal teams with federal customers should treat these as hard dates:

- **By 2025:** CNSA 2.0 algorithms (ML-KEM, ML-DSA, SLH-DSA where applicable, plus AES-256 and SHA-384) allowed for new NSS systems.
- **By 2027:** New software and firmware acquisitions must support CNSA 2.0.
- **By 2030:** All NSS deployments exclusively CNSA 2.0 for software and firmware signing, networking equipment, public key infrastructure.
- **By 2033:** All NSS traffic protected by CNSA 2.0.

Commercial guidance (NIST IR 8547, CNSA outreach) aligns closely. Plan for: hybrid by 2027, PQC-primary by 2030.

---

## Action items for this team

1. **This quarter:** build crypto inventory. One engineer owns it; output matches the table format above.
2. **This quarter:** wrap signing and key establishment in an algorithm-agnostic abstraction. No more hardcoded algorithm choices in service code.
3. **By end of 2026:** hybrid ML-KEM on public TLS edges where the library supports it (OpenSSL 3.5+, Go 1.24+). Measure handshake size and latency impact.
4. **By end of 2027:** internal CA roots signed with hybrid or PQC signatures; device certificates with >5-year validity migrated to hybrid.
5. **Ongoing:** every new cryptographic use added to the inventory at design time, not discovered during the next audit.

See also: `secure-coding-standards.md` (cryptography rules), `threat-modeling-guide.md` (HNDL as a tampering/information-disclosure threat), `supply-chain-security.md` (signed artifact migration).
