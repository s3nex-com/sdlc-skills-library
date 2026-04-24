# A/B testing — experiment design

An experiment that is not designed in advance is a story told after the fact. Before a single user sees the treatment, write down the hypothesis, the metric, the minimum detectable effect, the guardrails, the sample size, and the stop rule. If any of those are missing, the experiment is not ready to ship.

---

## The design artefact

Every experiment has a one-page design that names:

1. **Null hypothesis (H0):** the treatment has no effect on the primary metric versus control.
2. **Alternative hypothesis (H1):** the treatment changes the primary metric by at least the minimum detectable effect (MDE).
3. **Primary success metric:** one metric. Not three. Not "and also revenue". One.
4. **Minimum detectable effect (MDE):** the smallest lift worth shipping. Business decision, not statistical.
5. **Guardrail metrics:** metrics that must NOT regress. Latency, crash rate, revenue, long-term retention.
6. **Unit of randomisation:** user, session, device, account. Must match the unit of analysis.
7. **Sample size:** computed from MDE, baseline rate, power, and significance level. See formula below.
8. **Planned duration:** the wall-clock time required to accrue the sample size at current traffic, with a minimum of one full weekly cycle.
9. **Stop rule:** the pre-registered rule for ending the experiment — reach sample size, reach sequential-testing boundary, or guardrail breach.

If you cannot fill in all nine before launch, the experiment is not designed.

---

## Picking the metric

The primary metric must be:

- **Sensitive:** moves measurably within the planned duration.
- **Attributable:** changes in the metric are plausibly caused by the treatment.
- **Aligned:** improving the metric corresponds to improving the product outcome you care about.

Proxy metrics (click-through rate, time on page) are sensitive but often not aligned. North-star metrics (revenue, 90-day retention) are aligned but often not sensitive within a two-week experiment. Pick a middle-layer metric that is both — for example, 7-day active retention rather than lifetime revenue.

One primary metric. Additional metrics are secondary and do not gate the decision.

---

## Sample size calculation

For a two-sample test of proportions with equal-sized groups, per-arm sample size is:

```
n = 2 * ( (z_{1-α/2} + z_{1-β})^2 * p * (1 - p) ) / δ^2
```

Where:
- `α` = significance level (typical: 0.05 → `z_{1-α/2}` = 1.96)
- `β` = 1 − power (typical: power 0.80 → `β` = 0.20 → `z_{1-β}` = 0.84)
- `p` = pooled baseline conversion rate
- `δ` = absolute minimum detectable effect (e.g. lift from 10% to 11% → δ = 0.01)

### Worked example

Baseline signup conversion is 8%. You want to detect a relative lift of 10% (absolute δ = 0.008). Power 0.80, α 0.05.

```
n = 2 * (1.96 + 0.84)^2 * 0.08 * 0.92 / 0.008^2
n = 2 * 7.84 * 0.0736 / 0.000064
n = 1.1538 / 0.000064
n ≈ 18,028 per arm
```

You need about 18,000 users per arm, 36,000 total. If you have 5,000 visitors per day flowing through the funnel split 50/50, that is roughly 7–8 days to accrue, rounded up to one full week plus one weekend for day-of-week effects: plan for 9 days minimum.

For continuous metrics (revenue per user, time on page), replace `p * (1 − p)` with the pre-experiment variance `σ²` and use the same form.

---

## A/B vs multi-armed bandit vs pre-post

| Design | When to use | When to avoid |
|--------|-------------|---------------|
| A/B (fixed split) | You want an unbiased estimate of effect size. Regulated decisions. Learnings that feed future experiments. | Traffic is too low to reach sample size in any reasonable time. |
| Multi-armed bandit | Many variants, you care about cumulative reward during the experiment, you will not re-run this test. Onboarding copy, notification tuning. | You need a clean effect estimate. Only two variants and a simple decision — A/B is simpler. |
| Pre-post (no concurrent control) | True A/B impossible (system-wide change, pricing rollout, marketplace effects). | Any time concurrent A/B is feasible — pre-post is confounded by seasonality, macro trends, and concurrent shipping. Use it only as a last resort and never as the primary evidence for a reversible decision. |

Bandits optimise regret, A/B optimises inference. Know which one the decision needs.

---

## Common pitfalls

### Peeking

Checking the p-value repeatedly and stopping when it crosses 0.05 inflates the false-positive rate. With daily peeking over two weeks, a test designed for α = 0.05 actually runs at α ≈ 0.30. Either (a) fix the sample size in advance and do not look at significance until it is reached, or (b) use a sequential testing procedure (Bayesian, mSPRT, or always-valid p-values) that is mathematically correct under peeking.

### Novelty and primacy effects

Users react to anything new. A shiny redesign gets a 5% lift in week one and reverts to neutral by week four. Run long enough to see the novelty fade, or segment week-one users from returning users in analysis.

### Multiple comparisons

If you report 20 secondary metrics each at α = 0.05, you will find a "significant" effect on one of them by chance. Pre-register the primary metric. Secondary metrics are descriptive, not decision-grade. If you genuinely need to test multiple hypotheses, apply Bonferroni (`α / k`) or Benjamini-Hochberg.

### Sample ratio mismatch (SRM)

If the assignment split is 50/50 but you see 48.2% / 51.8%, something is broken — sticky assignments, bot filtering, or a bug in the allocation code. SRM invalidates the experiment; investigate before interpreting results. A chi-square test on the split gives a clean SRM check; run it on day one and at every analysis.

### Stratification issues

If the randomisation unit is the user but the analysis unit is the session, correlated sessions per user inflate apparent sample size and deflate variance estimates. The unit of analysis must match the unit of randomisation, or variance must be corrected (cluster-robust standard errors, delta method).

### Interaction effects

Two experiments running on overlapping users can interact. Either accept independence by random assignment and check for interaction post-hoc, or use mutually-exclusive bucketing (layers) for experiments that might collide on the same surface.

### Dilution

If only a subset of assigned users are actually exposed to the treatment (e.g. the flag fires on a page they never reach), the measured effect is diluted by the unexposed users. Report both intent-to-treat (all assigned users) and treatment-on-treated (exposed users only). Ship decisions made on intent-to-treat; diagnostics on treatment-on-treated.

### Ratio metrics

A metric like "revenue per session" is a ratio of two random variables. The naive `mean(revenue) / mean(sessions)` estimate has incorrect variance. Use the delta method, or design the experiment around the user-level numerator instead (revenue per user).

---

## Decision framework at experiment end

| Outcome | Action |
|---------|--------|
| Primary metric moves positively, stat-sig, no guardrail breach | Ship. Remove flag after ramp. |
| Primary metric flat, stat-sig guardrail breach | Kill. Post the learning to the experiment log. |
| Primary metric flat, no guardrail breach | Kill. Document why the hypothesis failed. |
| Primary metric moves negatively, stat-sig | Kill immediately. Post-mortem. |
| Primary metric moves positively, not stat-sig | Either extend (if underpowered) or kill (if the point estimate is below MDE). Do not ship on vibes. |
| Guardrail breached during ramp | Roll back instantly via kill switch. Analyse before re-launch. |

The decision-maker is named in the experiment design, not picked after the fact.

---

## Experiment log

Every experiment, win or lose, logs one row to the team's experiment registry:

```
id: exp-2026-04-checkout-redesign
hypothesis: New one-step checkout reduces abandonment vs two-step
primary_metric: checkout_completion_rate
mde: +2% absolute (baseline 62%)
sample_size_per_arm: 14,200
planned_duration_days: 14
actual_duration_days: 15
outcome: point_estimate +1.4%, 95% CI [+0.3%, +2.5%], clears MDE lower bound ambiguously
decision: extend to n=20,000 per arm, retest
decision_maker: @jsmith
```

The log is the memory of the team. Without it, the same experiment gets re-run three times over two years because nobody remembered the last result.

---

## Checklist — before you launch

- [ ] Null hypothesis and alternative hypothesis written
- [ ] One primary metric, pre-registered
- [ ] MDE set based on a business threshold, not on available sample
- [ ] Guardrail metrics defined with breach thresholds
- [ ] Unit of randomisation matches unit of analysis
- [ ] Sample size computed, traffic check done, duration known
- [ ] Stop rule pre-registered (fixed-n, sequential, or Bayesian threshold)
- [ ] Flag in place, kill switch tested in pre-production
- [ ] Event assignments property confirmed populated in staging
- [ ] SRM check configured to run on day one
- [ ] Decision-maker and review date on the calendar
- [ ] Experiment registered in the log before launch

If any box is unchecked, the experiment is not ready.
