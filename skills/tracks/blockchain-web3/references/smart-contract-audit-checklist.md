# Smart contract audit checklist

Run this checklist before external audit submission and again when reviewing audit findings. An external audit does not replace this checklist — it supplements it. Teams that run this checklist first produce higher-quality code before the auditor starts, which reduces the audit cost and cycle time.

---

## Static analysis — run before manual review

| Tool | What it finds | Run command |
|------|--------------|-------------|
| Slither | Reentrancy, unchecked return values, integer issues, access control | `slither .` |
| Mythril | Symbolic execution — integer overflow, reentrancy, dangerous delegatecall | `myth analyze <contract>.sol` |
| Echidna | Property-based fuzzing — define invariants and fuzz | `echidna-test . --contract YourContract` |
| 4naly3er | Gas optimisation opportunities | `4naly3er <contract>` |

All Slither HIGH and MEDIUM findings must be resolved or documented with a risk acceptance before audit submission.

---

## Critical vulnerability checklist

### Reentrancy

- [ ] All state updates happen BEFORE external calls (checks-effects-interactions pattern)
- [ ] No external call made to an untrusted contract before state is settled
- [ ] ReentrancyGuard applied to any function that transfers ETH or calls external contracts
- [ ] Cross-function reentrancy: review all functions that share state with external-calling functions

```solidity
// Vulnerable
function withdraw(uint amount) external {
    (bool success,) = msg.sender.call{value: amount}(""); // external call first
    balances[msg.sender] -= amount; // state update after — vulnerable
}

// Safe (checks-effects-interactions)
function withdraw(uint amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount; // state update first
    (bool success,) = msg.sender.call{value: amount}("");
    require(success);
}
```

### Integer overflow / underflow

- [ ] Solidity ≥ 0.8.0 (built-in overflow protection) OR SafeMath used throughout
- [ ] No unchecked blocks around arithmetic that could overflow/underflow
- [ ] Division: verify no division-before-multiplication rounding errors

### Access control

- [ ] All admin functions protected by `onlyOwner` or role-based modifier
- [ ] `msg.sender` vs `tx.origin` — only `msg.sender` used for auth (tx.origin is phishable)
- [ ] Initializer protected: if using upgradeable contracts, initializer cannot be called twice
- [ ] No function selector collision in diamond/multi-facet patterns

### Oracle manipulation / price feed

- [ ] Price data from Chainlink or another decentralised oracle — not from a single AMM spot price
- [ ] TWAP used where available rather than spot price (AMM spot can be manipulated in a single block)
- [ ] Freshness check: oracle data has a staleness guard (`if (block.timestamp - updatedAt > threshold) revert()`)
- [ ] Circuit breaker if oracle price deviates > X% from expected range

### Front-running

- [ ] No functions where the outcome depends on ordering and users can observe pending transactions
- [ ] Commit-reveal scheme used for auctions, randomness, or any user-submitted value that can be gamed by ordering
- [ ] Slippage protection: DEX or swap functions have a `minAmountOut` parameter

### Delegatecall

- [ ] `delegatecall` only made to trusted, immutable logic contracts
- [ ] Storage layout is identical between proxy and implementation (slot collision check)
- [ ] Implementation contract cannot be self-destructed (renders proxy bricked)

---

## Upgrade pattern checklist

If the contract is upgradeable:

- [ ] Upgrade pattern chosen and documented in an ADR (transparent proxy / UUPS / diamond)
- [ ] Storage layout tracked; new variables only appended, never inserted in the middle
- [ ] Timelock on upgrade: any upgrade has a minimum delay (e.g. 48 hours) to allow users to exit
- [ ] Upgrade function access-controlled to multisig (not a single EOA)
- [ ] Upgrade tested on a testnet fork before mainnet execution

---

## External audit scoping guide

Provide the auditor with:

1. **Scope document**: list of contracts in scope (address, file name, line count)
2. **Known issues**: any issue you already know about and have risk-accepted
3. **Architecture overview**: how contracts interact, which hold value
4. **Test suite**: full test results showing coverage
5. **Static analysis output**: Slither report with triage notes
6. **Previous audits**: if any exist, include them and list which findings were remediated

Typical audit duration: 1 week per 500 lines of production Solidity. Plan accordingly.
