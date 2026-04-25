# Key management for blockchain systems

Private key loss = permanent fund loss. There is no customer support, no password reset, no recovery mechanism for a lost private key that controls on-chain value. This reference covers key management architectures, the key ceremony procedure, rotation, and disaster recovery.

---

## Key types and their custody requirements

| Key type | Controls | Recommended custody |
|----------|---------|---------------------|
| Contract deployer (production) | Deploys and upgrades contracts | Hardware HSM or multisig |
| Treasury / fund wallet | Holds protocol funds | Multisig (3/5 minimum) |
| Admin / owner key | Pauses, parameter changes | Multisig with timelock |
| Oracle signer | Signs oracle price feeds | Dedicated HSM, rotated quarterly |
| Hot wallet (operational) | Small amounts, frequent transactions | Hardware wallet per engineer, MFA |
| Developer key (testnet only) | Testnet deployments only | Software wallet acceptable |

**Rule:** Any key that controls > $10,000 in value or controls an upgrade mechanism must use multisig. No single-engineer key in production.

---

## Multisig configuration

Use Gnosis Safe (Safe{Wallet}) for production multisig. Minimum configuration:

| Use case | Threshold | Signers |
|----------|-----------|---------|
| Treasury | 3/5 | 5 different engineers on different devices |
| Admin/owner | 2/3 | 3 engineers; no two on same device or location |
| Emergency pause | 1/3 | Quick response; still requires one team member |

**Geographic distribution:** Signers must be in different physical locations. If all signers are in one office and the office burns down, funds are unrecoverable.

**Device independence:** Each signer uses a separate hardware wallet (Ledger or Trezor). Software wallets are not acceptable for multisig signers in production.

---

## Key ceremony procedure

Run this once before mainnet deployment and again for any new multisig configuration.

1. **Preparation (1 day before)**
   - All signers confirm their hardware wallet firmware is up to date
   - Identify an air-gapped device for mnemonic generation if applicable
   - Book a secure physical location (not a public space)

2. **Mnemonic generation**
   - Generate on a hardware wallet directly (never on a computer)
   - Verify the wallet address matches what the ceremony intends to control
   - Record the mnemonic on paper (minimum two copies, stored separately)
   - Do NOT photograph, type, or email the mnemonic under any circumstances

3. **Distribution (for multisig)**
   - Each signer generates their own key independently
   - Each signer adds their public address to the Safe{Wallet} configuration
   - Verify Safe{Wallet} is pointed at the correct addresses before any funds are moved

4. **Backup verification**
   - Restore from backup copy on a fresh device — confirm the address matches before using
   - Store paper backup copies in:
     - One fireproof safe at office
     - One secure off-site location (safety deposit box, secure storage)
   - Never store both copies in the same location

---

## Rotation schedule

| Key | Rotation trigger | Rotation procedure |
|-----|-----------------|-------------------|
| Oracle signer | Quarterly or immediately on suspected compromise | Deploy new key, update contract whitelist, decommission old key |
| Hot wallet | On engineer offboarding | Replace immediately with a new key; sweep any funds to treasury |
| Admin multisig | On team member change | Add new signer, remove departed signer, verify threshold |
| Treasury | On suspected compromise only | Emergency multisig vote, move all funds to new Safe |

---

## Disaster recovery — lost key scenarios

| Scenario | Recovery |
|----------|---------|
| One multisig signer loses key | Remaining signers rotate — add a new signer, remove old address. Threshold must remain satisfiable with remaining signers. |
| Below-threshold signers unavailable | If threshold cannot be reached, funds are locked. This is why geographic + device distribution matters — design for simultaneous unavailability. |
| Admin key compromised | Emergency: trigger pause function (if available) with remaining signers immediately; rotate all multisig members under a new Safe; deploy upgrade to remove compromised key from all roles |
| Full multisig loss (catastrophic) | No recovery — funds are permanently inaccessible. This is the reason for the ceremony and distributed storage requirements above. |

**Document the DR procedure in the project runbook before mainnet launch.**
