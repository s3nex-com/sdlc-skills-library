# Game monetisation guide

## In-app purchase (IAP) flows

### Server-side receipt validation — mandatory

Never trust the client to report a successful purchase. Clients can be modified to fake purchase receipts.

**Correct flow:**
1. Player initiates purchase in-game
2. Platform (App Store / Google Play / Steam) processes payment
3. Platform delivers a signed receipt to the client
4. Client sends the receipt to YOUR backend (not directly acting on it)
5. Your backend validates the receipt against the platform's receipt validation API
6. Your backend confirms authenticity → grants the purchase in your database
7. Backend responds to client with the granted items

**Receipt validation APIs:**

| Platform | Endpoint | Notes |
|----------|---------|-------|
| Apple App Store | `https://buy.itunes.apple.com/verifyReceipt` | Production; sandbox: `buysandbox.itunes.apple.com` |
| Google Play | Google Play Developer API → `purchases.products.get` | Requires OAuth2 service account |
| Steam | Steam Web API → `ISteamMicroTxn/QueryTxn` | Requires Steam Web API key |

**Idempotency:** Use the receipt transaction ID as an idempotency key. Granting the same receipt twice is a serious exploit.

---

## Virtual currency design

Virtual currency (gems, coins, gold) is the layer between real money and game items. Design it carefully — it has real legal and economic implications.

**Hard currency** (purchased with real money): gems, diamonds, premium currency  
**Soft currency** (earned in-game): coins, experience, reputation

**Rules:**
- Hard currency rates must be clearly disclosed at point of purchase (EU and many jurisdictions require this)
- Hard currency → item conversions must be shown in both currencies (how many gems AND what that costs in USD)
- Never make it easy to calculate the real-money value of an item (dark pattern) — most jurisdictions now require transparency
- Loot box probabilities must be disclosed publicly in Belgium, Netherlands, South Korea, China, and increasingly in the UK and EU (check current jurisdiction before launch)

**Exchange rate:** Set hard currency conversion rates to obscure real prices (99 gems for $0.99 — it works but is increasingly regulated). Consider moving to transparent pricing (direct item purchase) in regulated markets.

---

## Loot box odds disclosure — regulatory landscape

As of 2025–2026, the following jurisdictions require or strongly recommend odds disclosure:

| Jurisdiction | Status | Requirement |
|-------------|--------|------------|
| Belgium | Banned (2018) | Paid loot boxes classified as gambling; prohibited |
| Netherlands | Partially banned | Prohibited if prizes are tradeable/sellable |
| South Korea | Disclosure required | All individual item probabilities must be shown |
| China | Disclosure required | Must show probability of each item in each loot box type |
| Germany | Grey area; guidance pending | Disclosure strongly recommended |
| UK | Not yet regulated; DCMS review ongoing | Voluntary disclosure recommended |
| EU (DSA/DMA context) | Emerging regulation | Monitor; disclose proactively |
| Australia | Not yet regulated | Voluntary disclosure recommended |
| USA | State-by-state; no federal law | Disclose to avoid reputational risk |

**Practical guidance:** Disclose probabilities globally. The reputational cost of being caught without disclosure is higher than the implementation cost of showing odds.

---

## Battle pass mechanics

Battle passes (season-length progression with tiered rewards) are lower regulatory risk than loot boxes because rewards are deterministic (known in advance).

**Design checklist:**
- [ ] All rewards visible before purchase (player knows exactly what they are buying)
- [ ] Progression achievable by free players (even if slower) — reduces pay-to-win criticism
- [ ] Premium pass accelerates, not gatekeeps (free players can reach the same content eventually)
- [ ] Season length and XP requirements calibrated: target 50–80 hours of play for a 6-week season
- [ ] Overpowered items in the premium track only → pay-to-win risk, avoid or balance carefully

---

## Anti-patterns

| Pattern | Why it is harmful (ethical and business) |
|---------|----------------------------------------|
| Pay-to-win (power advantage for money) | Drives away non-paying players; shrinks the pool matchmaking draws from |
| Predatory timers (arbitrary waits unless you pay) | Player resentment; drives churn long-term even if it converts short-term |
| Designed confusion (currency layers making real cost opaque) | Increasing regulatory target; class action risk in some markets |
| FOMO manipulation (limited-time offers with countdown timers and anxiety-inducing copy) | Short-term conversion boost; long-term brand damage and player burnout |
| Targeting minors with loot boxes or high-pressure monetisation | Regulatory risk; reputational risk; legally prohibited in some jurisdictions |
| Removing previously available free content and locking it behind IAP | Player trust destruction; review-bomb risk |
