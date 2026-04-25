# On-chain / off-chain patterns

## Finality and confirmation depth

Blockchain transactions are probabilistically final — a transaction is reversible until it is buried under enough subsequent blocks that reordering becomes computationally impractical.

| Chain | Recommended confirmation depth for finality |
|-------|---------------------------------------------|
| Ethereum mainnet | 12 blocks (~2.5 min) for medium value; 32 blocks (~6 min) for high value |
| Ethereum (post-Merge checkpoint finality) | 2 epochs (~12.8 min) for cryptographic finality |
| Polygon PoS | 128 checkpoints (~20 min) for Ethereum-level security |
| Arbitrum / Optimism (L2 rollups) | Wait for L1 settlement (~7 days for withdrawals); for deposits from L1 follow L1 confirmation depth |
| Bitcoin | 6 confirmations for standard transactions (~1 hour) |

**Design principle:** Systems that release funds or trigger irreversible off-chain actions (shipment, access provisioning) must wait for confirmed finality, not just transaction submission.

---

## Event sourcing from the chain

Treat blockchain events as an immutable event log — the canonical source of truth for on-chain state changes.

**Indexing pattern:**

1. Deploy a contract that emits events for all state changes (not just value transfers)
2. Run an indexer (The Graph subgraph, custom Node.js listener, or Alchemy/Infura webhook) that reads events and writes to a relational database
3. Use the database for all read queries — never query the chain directly for application reads
4. Handle chain reorganisations: mark events as tentative until confirmation depth is reached; revert tentative state on reorg

**Event replay:** Store raw events with block number and transaction hash. Replay from genesis is expensive but possible — design the indexer to be re-runnable.

**Gap detection:** Track the last processed block. On restart, re-process from last confirmed block to handle missed events during downtime.

---

## Rollback impossibility and its design implications

On-chain state cannot be rolled back. This changes how you design systems that interact with contracts:

| Situation | Implication |
|-----------|-------------|
| User sends wrong amount | Contract must implement a withdrawal mechanism for the user to recover funds |
| Bug in contract logic | Cannot patch in place (without an upgrade mechanism); funds may be locked |
| Admin mistake (wrong parameter) | No undo — design timelocks so mistakes can be caught before they take effect |
| Malicious transaction lands | Cannot be reversed — design frontrunning protection and circuit breakers |

**Checklist for irreversible operations:**
- [ ] User can always retrieve funds sent in error (withdrawal pattern)
- [ ] Admin parameter changes go through a timelock (48-hour minimum)
- [ ] Emergency pause function exists and is tested
- [ ] Maximum exposure per transaction is bounded

---

## Upgrade patterns

### Transparent proxy

- **How:** All calls to proxy are forwarded to logic contract via `delegatecall`; admin calls go directly to proxy
- **Risk:** Admin vs user slot collision; if admin calls a function that exists in the implementation, it's intercepted
- **Use when:** Standard upgradeable contract; OpenZeppelin `TransparentUpgradeableProxy` is the reference implementation

### UUPS (Universal Upgradeable Proxy Standard)

- **How:** Upgrade logic lives in the implementation contract (not the proxy); proxy is simpler and cheaper to deploy
- **Risk:** If upgrade function is removed from implementation, contract becomes permanently unupgradeable
- **Use when:** Lower deployment cost is a priority; team is comfortable managing the upgrade function in each implementation

### Diamond / EIP-2535

- **How:** Single proxy dispatches to multiple facets (logic contracts) via function selector routing
- **Risk:** Storage layout collision between facets; complex to audit
- **Use when:** Contract exceeds the 24KB deployment size limit; multiple independent modules that need to share state

**Common requirement for all upgrade patterns:**
- Storage layout must be identical and append-only — inserting variables between existing ones causes slot collisions
- Keep an append-only storage layout document in the repo
- Test every upgrade on a mainnet fork before executing on mainnet

---

## Oracle integration patterns

### Pull oracle (Chainlink Data Feeds)

- Price feed is updated on-chain by Chainlink nodes on a heartbeat or deviation threshold
- Consumer contract reads the latest value: `latestRoundData()`
- **Staleness guard required:**

```solidity
(, int256 price, , uint256 updatedAt,) = priceFeed.latestRoundData();
require(block.timestamp - updatedAt <= MAX_STALENESS, "Oracle: stale price");
require(price > 0, "Oracle: invalid price");
```

### Push oracle (custom)

- Off-chain component signs a price and pushes it on-chain
- Consumer verifies the signature from a whitelisted signer
- Rotation: signer key must be rotatable without redeploying the consumer contract

### TWAP (Time-Weighted Average Price)

- Use instead of spot price for any function where price manipulation is a risk
- Uniswap v3 provides on-chain TWAP over a configurable window
- **Rule:** For any operation that involves significant value transfer, use a 30-minute TWAP minimum
