---
name: blockchain-web3
description: >
  smart contract, Solidity, Vyper, EVM, EVM-compatible, Ethereum, Polygon,
  Avalanche, Arbitrum, Optimism, Base, DeFi, decentralised finance,
  NFT, non-fungible token, fungible token, ERC-20, ERC-721, ERC-1155,
  crypto custody, Web3, dApp, decentralised application, on-chain,
  on-chain settlement, off-chain, L2, layer 2, rollup, ZK rollup,
  token, wallet integration, MetaMask, WalletConnect, RainbowKit,
  gas optimisation, gas fees, block confirmation, finality,
  oracle, Chainlink, price feed, multisig, Gnosis Safe,
  key ceremony, key management, private key, mnemonic, seed phrase,
  blockchain, distributed ledger, immutable, upgrade pattern, proxy pattern,
  UUPS, transparent proxy, diamond standard, timelock
---

# Blockchain / Web3 track

## Purpose

Blockchain systems have a failure mode that no other domain shares: transactions are irreversible. A bug in a smart contract cannot be patched like a web service — funds can be drained, tokens permanently locked, or state corrupted with no rollback. This track encodes the engineering discipline required to ship on-chain code safely: external audit requirements, key management ceremonies, formal upgrade paths, and oracle security. It applies to any system where a bug causes on-chain state changes that cannot be undone.

---

## When to activate

**Keyword signals:**
- "smart contract", "Solidity", "Vyper", "EVM", "DeFi", "NFT", "Web3", "dApp"
- "on-chain settlement", "crypto custody", "multisig", "key ceremony"
- "gas optimisation", "oracle", "Chainlink", "L2", "rollup"
- "proxy pattern", "UUPS", "timelock", "upgrade pattern"

**Architectural signals:**
- System writes state to a blockchain (not just reads)
- Users hold wallets and sign transactions
- Contract holds or moves value (ETH, ERC-20, or other tokens)
- System uses an oracle to bring off-chain data on-chain
- Team is planning a contract upgrade path

---

## When NOT to activate

- Payments processed via a hosted processor that uses crypto under the hood — if your code never touches keys or on-chain state directly, use Fintech track instead
- Read-only blockchain queries (balance checks, event indexing) with no write path — no elevated obligations apply
- Internal tooling that uses a private permissioned ledger with no external value — lower risk profile; apply Standard mode manually without this track
- NFT project where all contracts are deployed from an audited template (e.g. OpenZeppelin Contracts) without modification — review is still good practice but external audit is not mandatory

---

## Skill elevations

| Skill | In Nano | In Lean | In Standard | In Rigorous |
|-------|---------|---------|-------------|-------------|
| security-audit-secure-sdlc | Mandatory + contract threat model | Mandatory + contract threat model | Mandatory + external audit required | Mandatory + external audit + re-audit on any upgrade |
| formal-verification | N/A | Conditional (critical value-holding logic) | Mandatory for money-movement logic | Mandatory for all core contracts |
| architecture-decision-records | Advisory | Mandatory (upgrade path must be an ADR) | Mandatory | Mandatory |
| distributed-systems-patterns | Advisory | Mandatory (finality and idempotency) | Mandatory + reentrancy and front-running patterns | Mandatory |
| data-governance-privacy | Advisory | Mandatory (on-chain permanence classification) | Mandatory | Mandatory |
| disaster-recovery | N/A | Mandatory (key loss = fund loss) | Mandatory + multi-sig recovery tested | Mandatory |
| devops-pipeline-governance | Advisory | Mandatory + contract deployment pipeline | Mandatory + testnet gate before mainnet | Mandatory |

---

## Gate modifications

| Stage | Modification |
|-------|-------------|
| Stage 1 (Plan) | Identify which contracts hold or move value; classify upgrade path (immutable / proxy / diamond); define key management scheme (EOA / multisig / HSM) |
| Stage 2 (Design) | Upgrade path documented in ADR; oracle trust assumptions documented; reentrancy and integer-overflow mitigations designed; key ceremony plan written |
| Stage 3 (Build) | All value-moving logic reviewed against reentrancy checklist; no unchecked external calls; events emitted for all state changes |
| Stage 4 (Verify) | External smart contract audit completed and findings addressed before mainnet; Slither and Mythril scans clean; fuzzing with Echidna for critical paths; testnet deployment and functional sign-off |
| Stage 5 (Ship) | Mainnet deployment via multisig or timelock (no single EOA deployer for production); deployment address recorded; contract verified on block explorer; upgrade path tested on testnet before any upgrade |
| Phase 3 (Ongoing) | Quarterly key rotation review; monitor oracle feeds for anomalies; track gas cost trends; review security advisories for dependencies (OpenZeppelin, etc.) |

---

## Reference injection map

| When this skill fires | Also load these references |
|-----------------------|---------------------------|
| security-audit-secure-sdlc | `references/smart-contract-audit-checklist.md` |
| formal-verification | `references/smart-contract-audit-checklist.md` |
| disaster-recovery | `references/key-management-guide.md` |
| distributed-systems-patterns | `references/on-chain-off-chain-patterns.md` |
| devops-pipeline-governance | `references/on-chain-off-chain-patterns.md` |
| architecture-decision-records | `references/on-chain-off-chain-patterns.md` |

---

## Reference files

- `references/smart-contract-audit-checklist.md` — reentrancy, integer overflow, access control, oracle manipulation, front-running, gas limit issues, and upgrade safety; tools: Slither, Mythril, Echidna; external audit scoping guide
- `references/key-management-guide.md` — EOA vs multisig vs HSM, key ceremony procedure, rotation schedule, disaster recovery for lost keys, hardware wallet selection
- `references/on-chain-off-chain-patterns.md` — finality assumptions and confirmation depth, event sourcing from chain, rollback impossibility, upgrade patterns (transparent proxy, UUPS, diamond/EIP-2535), oracle integration patterns

---

## Skill execution log

Track activation:
```
[YYYY-MM-DD] track-activated: blockchain-web3 | mode: [Mode] | duration: project
```

Skill firings under this track:
```
[YYYY-MM-DD] security-audit-secure-sdlc | outcome: OK | note: external audit complete, 2 medium findings resolved | track: blockchain-web3
```
