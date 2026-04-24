# Experiment statistics — frequentist, Bayesian, and how long to run

The choice between frequentist and Bayesian is about what question you want to answer, not which camp you belong to. Most teams that claim to be Bayesian are running frequentist tests with Bayesian vocabulary. Pick one framework per experiment platform and apply it consistently.

---

## Frequentist: what it answers

"If the null hypothesis were true, how likely is data at least this extreme?"

- **p-value:** probability of the observed (or more extreme) effect under H0. Not the probability that H1 is true.
- **Confidence interval (95%):** range of effect sizes compatible with the data. If the experiment were repeated many times, 95% of such intervals would contain the true effect. Not "95% probability the true effect is in this range".
- **Power (1 − β):** probability of detecting a true effect of size MDE. Standard: 0.80.
- **α:** acceptable false-positive rate. Standard: 0.05.

Use frequentist when:
- The team and tooling are already frequentist.
- The decision is a binary ship / kill with a pre-registered MDE.
- Regulators or reviewers expect p-values.

---

## Bayesian: what it answers

"Given a prior and the data, what is the probability distribution over the true effect?"

- **Posterior:** probability distribution over the effect size given the data and the prior.
- **Credible interval (95%):** range within which the true effect lies with 95% posterior probability. This *is* the intuitive interpretation.
- **P(lift > 0):** probability the treatment beats control. Easier to communicate.
- **Expected loss:** expected regret if you pick the wrong variant. Useful decision quantity.

Use Bayesian when:
- You want peeking-robust early-stop decisions without sequential-testing gymnastics.
- Decisions are graduated (ramp a bit if promising, ramp more if stronger) rather than binary.
- You have a sensible prior (similar past experiments on the same surface).

Bayesian methods let you ask "should I roll out now?" at any time without inflating error rates. Frequentist methods require either a pre-committed sample size or a sequential procedure.

---

## Effect size and practical significance

Statistical significance tells you the effect is not zero. Practical significance tells you the effect is worth shipping. A test with 10 million users will find a 0.01% lift statistically significant; nobody should ship it.

Report three numbers:

1. **Point estimate** of the effect (e.g. +2.3% conversion lift)
2. **Confidence / credible interval** (e.g. [+0.8%, +3.8%])
3. **Comparison to MDE** (e.g. MDE was 2%, estimate clears MDE, lower bound does not)

Ship when the point estimate beats MDE and the lower bound is positive. Kill or extend otherwise.

---

## How long should an experiment run?

Minimum duration is bounded by three constraints, whichever is longest wins:

1. **Sample size:** time to accrue the required `n` at current traffic. From the formula in `ab-testing-design.md`.
2. **One full business cycle:** at least one complete week (usually two) to cover day-of-week and weekend/weekday effects. B2C traffic patterns on Monday look nothing like Saturday.
3. **Novelty decay:** if the feature is visibly new, extend until the novelty curve flattens. Compare week 1 users to week 2 users as a check.

Maximum duration is bounded by:

1. **Opportunity cost:** every day the experiment runs is a day the losing variant is served to half the users.
2. **External confounds:** marketing campaigns, competitor launches, and seasonal shifts start to contaminate the result.
3. **Team patience:** experiments that run for three months rarely get shipped at all.

Default: design for 2 weeks. Short enough to preserve learning velocity, long enough to cover cycles and novelty. Extend only if underpowered at the planned stop.

---

## Stopping rules and sequential testing

A fixed-sample-size design says: pre-commit to `n`, do not look at results before `n` is reached, decide at `n`. This is statistically clean but operationally painful.

Sequential testing lets you look early and stop if the evidence is strong enough, without inflating α. Choose one of:

- **Group sequential (O'Brien-Fleming, Pocock):** pre-specified interim analysis boundaries at fixed fractions of `n`. Requires declaring interim points in advance.
- **mSPRT (mixture Sequential Probability Ratio Test):** always-valid p-values, look whenever you want, the false-positive rate stays at α.
- **Bayesian with decision thresholds:** stop when `P(lift > 0) > 0.95` and expected loss is below a threshold. Natural peeking tolerance.

Pre-commit to the procedure. Mixing "fixed-sample-size" with "I peeked on day 3 and it looked good" is how teams convince themselves into shipping noise.

### The stop rule is pre-registered

Every experiment design names its stop rule before launch:

- "Stop at n = 18,000 per arm. Ship if lower bound of 95% CI exceeds +1% lift."
- "Stop at n = 18,000 per arm or earlier if mSPRT always-valid p < 0.01. Ship if point estimate > MDE."
- "Stop when P(lift > 0) > 0.95 and expected loss < 0.5% revenue. Ship."

After-the-fact stop rules are not stop rules.

---

## Variance reduction: CUPED

CUPED (Controlled-experiment Using Pre-Experiment Data) reduces variance by adjusting the post-experiment metric using a covariate measured before the experiment started.

Mechanism: for user `i`, replace the metric `Y_i` with:

```
Y_i_adjusted = Y_i − θ * (X_i − E[X])
```

Where `X_i` is the user's pre-experiment metric (e.g. sessions in the 4 weeks before launch) and `θ = Cov(Y, X) / Var(X)` estimated from pre-period data.

If `X` is a strong predictor of `Y`, variance drops by up to 50%. Halved variance means halved required sample size, or equivalently the ability to detect effects half as large in the same time.

CUPED requires:
- Pre-experiment data per randomisation unit — needs stable user identifiers and historical events.
- A covariate measured on the same unit as randomisation.
- `θ` estimated on pre-period data, not on experiment data (avoid leakage).

Worth the complexity above ~10,000-sample experiments. Below that, the variance reduction does not justify the pipeline work.

---

## Quick-reference table

| Question | Frequentist | Bayesian |
|----------|-------------|----------|
| How do I stop the experiment early? | Sequential test (mSPRT, group sequential) | Posterior threshold, any time |
| How do I interpret the result? | p-value and CI, "compatible with" | Credible interval, "probability of" |
| How do I handle peeking? | Correct for it or pre-commit to n | Inherently peeking-robust |
| How do I use past experiment data? | Power calculations only | Informative priors |
| How do I report to a non-technical stakeholder? | "Stat-sig at 95%" | "85% probability treatment wins" |
| What if the effect is tiny but real? | Requires large `n` to detect | Requires large `n` to detect (no free lunch) |

Both frameworks answer the underlying decision question. Pick one, document the pick, apply it consistently.
