# Risk register template

## Instructions

Record every identified risk here. Update status at each sprint review. Escalate Critical and High risks immediately — do not wait for the next scheduled review.

**Composite score = Probability × Impact**
**Priority: 20-25=Critical🔴 | 12-19=High🟠 | 6-11=Medium🟡 | 1-5=Low🟢**

---

## Risk register

| Risk ID | Title | Category | P | I | Score | Priority | Status | Mitigation | Contingency | Owner | Early Warning | Review |
|---------|-------|----------|---|---|-------|----------|--------|-----------|-------------|-------|--------------|--------|
| RISK-001 | Kafka throughput does not meet 50k events/sec target | Architecture | 3 | 5 | 15 | 🟠 High | Being mitigated | Performance spike in Sprint 3 using realistic payload sizes and concurrent producers | If spike fails: evaluate Confluent Cloud throughput tiers; consider event batching to reduce per-event overhead | TL-B | Producer send latency >50ms at 10k events/sec in dev environment | Sprint 3 review |
| RISK-002 | Company B capacity reduced by 30% in Sprint 5 due to other commitments | Delivery | 3 | 4 | 12 | 🟠 High | Identified | Confirm Company B capacity commitment by end of Sprint 1; identify sprint 5 scope that can defer to Sprint 6 without milestone impact | Defer non-critical features from M2 scope; negotiate deadline extension with evidence | EM-B | Company B sprint velocity drops >20% from baseline in Sprint 3 or 4 | Sprint 1 close |
| RISK-003 | Third-party geolocation API changes pricing or availability | Dependency | 2 | 3 | 6 | 🟡 Medium | Identified | Review geolocation API terms of service; confirm SLA; evaluate fallback providers | Switch to backup provider (ipinfo.io identified); fallback: return null geolocation and continue processing | TL-B | Geolocation API response time increases by >100ms | Monthly steering |
| RISK-004 | Authentication vulnerability in JWT implementation | Security | 2 | 5 | 10 | 🟡 Medium | Being mitigated | Security review of JWT implementation in Sprint 2; use established library (PyJWT 2.x), do not implement custom JWT parsing | Revoke all issued tokens; force re-authentication of all sessions; patch and redeploy within 24h | SEC | Security scan flags JWT-related CVE; any authentication bypass reported in testing | Pre-release security gate |
| RISK-005 | Scope interpretation disagreement over "real-time" alerting SLA | Contractual | 3 | 3 | 9 | 🟡 Medium | Resolved | Both companies agreed in ADR-015 that "real-time" means ≤30 second end-to-end latency from event to alert delivery. Documented and signed off. | N/A — risk resolved | VPE-A | N/A | Resolved 2024-04-10 |
| RISK-006 | Key Company B engineer (sole Kafka expert) leaves project | Organisational | 2 | 4 | 8 | 🟡 Medium | Being mitigated | Knowledge transfer sessions documented in runbooks; second Company B engineer to pair on all Kafka-related work; invite Company B engineer to architecture reviews | Engage Confluent professional services; brief Company A senior engineer on Kafka operations as backup | EM-B | Key engineer's availability drops below 50% in any sprint without advance notice | Monthly steering |

---

## Risk status legend

| Status | Icon | Meaning |
|--------|------|---------|
| Identified | 📋 | Documented; mitigation not yet started |
| Being mitigated | 🔧 | Active mitigation underway |
| Resolved | ✅ | Risk no longer active |
| Accepted | 📝 | Both companies accept risk without further mitigation |
| Escalated | 🚨 | Escalated to VP level; risk is materialising |

---

## Risk trend tracker

Update at each monthly steering:

| Date | Critical | High | Medium | Low | Total | Trend |
|------|---------|------|--------|-----|-------|-------|
| [2024-03-01] | 0 | 2 | 4 | 1 | 7 | — |
| [2024-04-01] | 0 | 1 | 3 | 2 | 6 | ↓ Improving |

---

**Last reviewed:** [date]
**Reviewed by:** [Name, Company A] + [Name, Company B]
**Next scheduled review:** [date]
