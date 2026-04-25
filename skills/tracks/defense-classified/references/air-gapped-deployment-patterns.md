# Air-gapped deployment patterns

## What air-gapped means in practice

An air-gapped system has no network connection to less-classified or unclassified networks. Updates, code, data, and patches must be physically transferred using media that is strictly controlled. There is no `git pull`, no `apt-get update`, no cloud artifact registry — every artifact must be carried through a transfer station.

---

## Transfer station procedure

A transfer station is a controlled process for moving data between networks of different classification levels.

**Standard procedure:**

1. **Prepare the transfer package on the unclassified side:**
   - Identify what needs to move (software update, patch, configuration change)
   - Scan with security scanning tools (antivirus, SAST)
   - Package with a manifest listing every file, size, and SHA-256 hash
   - Sign the package (GPG or PKI certificate from the classified environment's CA)

2. **Media selection:**
   - Use removable media (USB, DVD) that has never been connected to a lower-classification network
   - Label all media with the destination classification level
   - Log the media in the transfer log (date, contents, handler, destination)

3. **Physical transfer:**
   - Carry by hand or courier — do not mail, ship, or leave unattended
   - Transfer in a controlled location (not a hallway, not a shared area)
   - Two-person integrity (TPI) rule for high-value transfers: two cleared individuals must be present

4. **Receive on the classified side:**
   - Verify the GPG signature from the originating CA before mounting the media
   - Verify SHA-256 hashes of every file against the manifest
   - Scan the media with the classified-side security tools before executing anything
   - Log receipt in the classified transfer log

5. **Media sanitisation after transfer:**
   - After transfer is complete and verified, sanitise the media before reuse
   - Follow DoD 5220.22-M or NIST 800-88 for sanitisation (overwrite × 3 or degauss + destroy for classified)
   - Never reuse media used in a classified environment in an unclassified environment without certified sanitisation

---

## One-way data diodes

A data diode is a hardware device that enforces one-way data flow at the physical layer. Optical data diodes send light in one direction — no electrical return path for data exists.

**Use cases:**
- Export sensor or telemetry data from a classified network to an unclassified reporting system
- Import approved software packages into a classified network without a return channel
- Real-time streaming of classified operational data to an unclassified analytics system

**Common products:** Owl Cyber Defense, Waterfall Security, Forcepoint Cross Domain Solutions.

**Design pattern — classified → unclassified telemetry export:**

```
[Classified sensor / system]
        ↓ (data diode — one direction only)
[Unclassified aggregation server]
        ↓
[Standard analytics / dashboarding]
```

**Key constraint:** No acknowledgement can travel back. Design the classified sender to operate without delivery confirmation (fire-and-forget, buffered). The receiving side must handle gaps and duplicates gracefully.

---

## Offline software update packaging

Since there is no cloud artifact registry, software updates must be bundled for physical transport.

**Update package structure:**

```
update-package-v1.2.3/
  manifest.json          — file list with SHA-256 hashes
  update.sh              — installation script (idempotent, rollback-capable)
  artifacts/
    app-v1.2.3.tar.gz
    config-schema-v1.2.3.json
    migrations/
      001_add_column.sql
  signature.asc          — GPG signature of manifest.json
  README.txt             — human-readable install instructions
```

**`manifest.json` format:**
```json
{
  "version": "1.2.3",
  "build_date": "2026-04-25T10:00:00Z",
  "classification": "CUI",
  "files": [
    {"path": "artifacts/app-v1.2.3.tar.gz", "sha256": "abc123..."},
    {"path": "artifacts/config-schema-v1.2.3.json", "sha256": "def456..."}
  ]
}
```

**On-site installation (classified side):**
```bash
# 1. Verify signature
gpg --verify signature.asc manifest.json

# 2. Verify all file hashes
python3 verify_manifest.py manifest.json

# 3. Run installation (only after both verifications pass)
./update.sh --env production --dry-run  # verify what will happen
./update.sh --env production            # apply
```

---

## Classified development environment setup

Developers working on classified systems cannot use public cloud services, external package registries, or most standard tooling.

**Internal infrastructure required:**
- Internal Git server (GitLab CE, Gitea, or equivalent) in the classified environment
- Internal artifact registry (Nexus, Artifactory) with approved packages mirrored from outside
- Internal CA for TLS certificates (no Let's Encrypt)
- Internal container registry (Harbor or equivalent)
- Offline documentation (download and host critical docs internally: NIST publications, framework docs)

**Dependency management:**
- Pin all dependency versions (no `*` or `latest`)
- Maintain a local mirror of approved packages — vetted, scanned, and approved before import
- New dependencies require an approval process: request → ISSO/security review → approved mirror → available for use

---

## Document handling in air-gapped environments

- All documents in the classified environment must be marked with their classification level on every page (header and footer)
- Electronic documents follow the same marking requirements as physical documents
- Hard copy documents require sign-out and shredder-disposal (cross-cut or micro-cut shredder, NSA-listed)
- Do not print classified material on printers connected to unclassified networks (even temporarily)
- Screen lock policy: workstations must lock after 15 minutes maximum; classified terminals must not be left unattended
