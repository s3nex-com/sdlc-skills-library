# skills/phase4/ — Advanced assurance

Phase 4 contains one skill: `formal-verification-chaos-engineering`. Apply it to critical systems only — not as routine practice. For a small team, applying this skill to every service is waste. Apply it where "it passes in staging" is genuinely insufficient assurance.

---

## The skill

**formal-verification-chaos-engineering** (`phase4/formal-verification-chaos-engineering/`)

Three capabilities bundled into one skill:

1. **TLA+ formal specification** — mathematical modelling of distributed protocols to prove correctness properties before implementation. Use when designing custom distributed protocols where correctness must be provable, not just tested.

2. **Chaos engineering experiments** — deliberate failure injection to validate that resilience patterns (circuit breakers, retries, fallbacks) actually hold under real failure conditions. Use before major launches and quarterly to verify the system remains resilient as it evolves.

3. **Game days** — rehearsed incident response exercises. The team executes real runbooks against real (staged) failure scenarios. Use quarterly to keep incident response skills current and runbooks accurate.

---

## When to apply this skill

Apply when "it passes in staging" is genuinely insufficient — specifically:

- **Financial transactions** — incorrect ordering, duplicate processing, or lost state has direct monetary consequences
- **Safety-critical data** — errors cannot be corrected after the fact (medical records, legal documents, audit logs)
- **Contractually-guaranteed data integrity** — SLA breach has financial or legal consequences
- **Custom distributed protocols** — leader election, two-phase commit, idempotency guarantees you have implemented yourself rather than delegated to a proven library or platform

Do not apply this skill to:
- Standard CRUD services with well-understood consistency models
- Services backed by established databases with ACID guarantees you are not overriding
- Load testing and performance validation → `performance-reliability-engineering`
- Standard unit and integration testing → `comprehensive-test-strategy`

---

## Right-sized application for a small team

A 3–5 person team running this skill at full intensity is waste. The right scale:

| Capability | Right size for a small team |
|-----------|---------------------------|
| Game days | One per quarter |
| Chaos experiment catalogue | Run the standard 5-experiment catalogue quarterly; add custom experiments only for novel failure modes |
| TLA+ | Only when designing a custom distributed protocol — not for every service |
| Property-based testing | This has moved to `phase2/comprehensive-test-strategy` — do not add it back here |

---

## Important: property-based testing is in phase 2

Property-based testing (Hypothesis, fast-check) has been moved to `phase2/comprehensive-test-strategy`. It is part of the standard test pyramid for any service, not an advanced assurance technique reserved for critical systems.

Do not add property-based testing back to this skill. If you see it appearing in `SKILL.md` for `formal-verification-chaos-engineering`, remove it and ensure it is present in `phase2/comprehensive-test-strategy`.

---

## Editing this skill

- The distinction between "standard testing" and "advanced assurance" must stay clear. The moment phase 4 techniques become routine, the signal is lost.
- The game day frequency (quarterly) and chaos experiment catalogue (5 standard experiments) are calibrated for a small team. Do not increase these without a clear reason.
- TLA+ guidance should remain practical: sketch-level specifications that prove key safety and liveness properties, not full formal proofs requiring dedicated verification engineers.
