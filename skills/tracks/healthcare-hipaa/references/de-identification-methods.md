# De-identification methods — Safe Harbor, Expert Determination, Limited Data Set

Under HIPAA §164.514, data that has been properly de-identified is **no longer PHI** and is not subject to the Privacy Rule. That's the prize. The two official paths to get there are Safe Harbor and Expert Determination. A third category, the Limited Data Set, is still PHI but permits broader use under a Data Use Agreement.

Pick the method **before** you design the dataset. Retrofitting de-identification onto a production table is expensive and often impossible without losing analytic value.

---

## Safe Harbor — the mechanical rulebook

Defined in §164.514(b)(2). A dataset is de-identified under Safe Harbor if **all 18 HIPAA identifiers are removed** (see `phi-classification.md` for the full list) AND the covered entity has no actual knowledge that the remaining information could be used, alone or combined, to identify an individual.

Key mechanics:

- **Names** — all forms removed (full, last, initials if combined with anything else).
- **Geography** — strip anything more granular than state. ZIP is allowed only as the first 3 digits, and only if the resulting 3-digit area contains more than 20,000 people per US Census. Around 17 low-population 3-digit ZIPs must be changed to `000` — maintain the list, don't guess. (Safe Harbor §164.514(b)(2)(i)(B))
- **Dates** — strip any date related to an individual (birth, admission, discharge, death, visit). Years alone are permitted. Ages are permitted up to 89; aggregate 90+ into a single bucket.
- **All other identifiers** — removed entirely. No hashed versions, no tokenized versions unless the mapping is destroyed.

Pros: deterministic, defensible, no statistician needed.
Cons: significant utility loss. Longitudinal analysis suffers because exact dates are gone. Rare-disease research often fails Safe Harbor because small cohorts + 3-digit ZIP + year-of-birth re-identify.

**Use Safe Harbor when:** the analytic questions survive date-coarsening and geographic coarsening. Operational dashboards, aggregate trend reporting, most BI use cases.

---

## Expert Determination — the risk-based path

Defined in §164.514(b)(1). A qualified statistician (or person with appropriate experience — OCR does not license this role, but the work is scrutinised if challenged) determines that the risk of re-identification is "very small" given the dataset's intended recipients and the methods they might reasonably employ. The expert must document the methods and results of the analysis.

What "very small" actually means in practice: commonly operationalised as a re-identification probability below 0.05 or 0.09 per record (the HITRUST and various hospital system thresholds; OCR has not set a number).

This path permits more granular data than Safe Harbor — exact dates, 5-digit ZIP, higher-resolution ages — provided the expert's analysis shows the combination remains unidentifiable to the intended recipient.

Pros: preserves far more analytic utility; supports longitudinal and rare-cohort research.
Cons: requires real statistical work, typically a qualified biostatistician, and a signed report. Needs redo when the dataset changes materially.

**Use Expert Determination when:** you need date-level precision, 5-digit ZIP, or other identifiers that Safe Harbor strips, AND the cost of the statistician is justified by the research/product value.

---

## Limited Data Set (LDS) — still PHI, but broader use

Defined in §164.514(e). An LDS is not de-identified — it retains some direct identifiers — but permits broader use for research, public health, and healthcare operations under a signed Data Use Agreement (DUA).

An LDS may retain:

- Dates of service, birth, death, admission, discharge (exact).
- Geography more granular than state (city, county, 5-digit ZIP — but NOT street address).

An LDS must strip the other 16 identifiers: names, SSN, MRN, phone, email, etc.

Pros: keeps dates and fine-grained geography without a statistician.
Cons: it's still PHI. Requires a DUA with the recipient. Still must be logged, still controlled.

**Use an LDS when:** the recipient is a research partner or public health agency who needs dates/geography but not direct identifiers, and both parties sign a DUA.

---

## Decision matrix — pick the method

| Intended use | Need exact dates? | Need fine geography? | Recipient? | Method |
|--------------|------------------|---------------------|-----------|--------|
| Internal BI dashboard, aggregate trends | No | 3-digit ZIP is fine | Internal | Safe Harbor |
| External partner analytics with stat report | Yes | Maybe | External, via contract | Expert Determination |
| Public release / open data | Prefer no | Prefer coarse | Public (worst case) | Safe Harbor + k-anonymity ≥ 20 |
| Research collaboration, exact encounters | Yes | 5-digit ZIP | Research partner with DUA | Limited Data Set |
| Customer-facing ML feature (not PHI) | No | No | End user | Full de-identification; if ambiguous, treat as PHI |
| Model training where data stays in-scope | N/A | N/A | Your own pipeline | Keep as PHI, do not de-identify; train with full controls |

---

## Re-identification risk assessment — how to do the math when it's your call

Not every team has a biostatistician. You can still reason about risk. Two primary metrics:

### k-anonymity

A dataset satisfies **k-anonymity** if every combination of quasi-identifier values appears in at least `k` records. If `k = 20` and the quasi-identifiers are `{age_band, zip3, gender}`, then for every observed combination of those three there are at least 20 individuals — no single record can be isolated.

Compute k by GROUP BY on quasi-identifiers and finding the smallest group:

```sql
SELECT MIN(cohort_size) AS k
FROM (
  SELECT age_band, zip3, gender, COUNT(*) AS cohort_size
  FROM analytics_dataset
  GROUP BY age_band, zip3, gender
) t;
```

Common threshold: `k ≥ 20` for external release. Some teams use `k ≥ 5` internally. `k = 1` means at least one record is unique on the quasi-identifiers — you have re-identifiable rows.

### l-diversity

k-anonymity has a known weakness: a cohort of 20 people may all share the same sensitive value (e.g., all 20 have HIV). An attacker who locates the cohort learns the sensitive attribute even without pinpointing the individual. **l-diversity** requires that each cohort has at least `l` distinct values of the sensitive attribute.

Example: `l = 3` on diagnosis means no cohort is all-one-diagnosis; at least three diagnoses are represented. This matters for rare-disease data and anywhere the sensitive field could be damaging on its own.

### t-closeness (mentioned, rarely needed)

Stricter still: the distribution of sensitive values within each cohort must not diverge too far from the distribution in the full dataset. Relevant when the sensitive attribute's distribution itself is informative. For most product work, k-anonymity + l-diversity is sufficient.

---

## Worked transformations

### Example 1 — patient demographics to Safe Harbor analytics

Source:

```
patient_id | full_name       | dob         | zip    | gender | diagnosis
-----------+-----------------+-------------+--------+--------+-----------
p_812      | John M. Smith   | 1954-03-17  | 02139  | M      | E11.9
p_813      | Alicia Reyes    | 1988-11-02  | 02142  | F      | J45.909
```

Safe Harbor output:

```
cohort_key         | age_band | zip3 | gender | diagnosis_group
-------------------+----------+------+--------+----------------
cohort_021_65_M_DM | 65-89    | 021  | M      | type_2_diabetes
cohort_021_30_F_AS | 30-44    | 021  | F      | asthma
```

Dates become age bands, ZIP is truncated to 3 digits (Cambridge MA 3-digit ZIP `021` passes the 20,000-people test), names gone, diagnosis generalised.

### Example 2 — a rare-disease problem that fails Safe Harbor trivially

Source includes 12 patients with a genetic disorder in 3-digit ZIP 021. Even after Safe Harbor, the cohort `age_band=30-44, zip3=021, diagnosis=rare_genetic_X` has 12 rows globally. If an attacker knows a person has that rare condition, they know which row set to look at.

Options:

- Drop ZIP entirely (generalise to state or region). Cohort grows; re-identification risk falls.
- Generalise the diagnosis code (`rare_genetic_X` → `genetic_metabolic_disorders`).
- Move the dataset to an LDS with a DUA; don't try to pass it off as de-identified.
- Engage Expert Determination if the rare diagnosis is analytically essential.

### Example 3 — pseudonymization is not de-identification

A team replaces `patient_id` with `sha256(patient_id || secret_salt)` and calls the dataset de-identified. It isn't. The salt is in your vault; a motivated insider reverses the mapping. Safe Harbor #18 catches this; OCR has enforced against similar schemes. Pseudonymization is a data-protection technique inside PHI systems. It is not a method of de-identification.

---

## When de-identification is the wrong answer

Sometimes the honest engineering answer is: **keep this as PHI and apply the full control set**. De-identification is appropriate when:

- You need to expose data to a population that should not see PHI (external analysts, research partners without BAAs, the public).
- You need to reduce scope so that downstream systems (marketing analytics, generic BI) can ingest the data without dragging HIPAA controls behind them.

It is the wrong answer when:

- The consumer is an authorised clinical user who needs the full record — de-identifying breaks their job.
- The downstream system would need to re-join to the source for any real use — you've added complexity without reducing risk.
- The analytic value depends on fields that Safe Harbor strips and you can't justify Expert Determination — pick a different approach (synthetic data, differential privacy, or just keep the data in-scope).

---

## Checklist — before declaring a dataset de-identified

- [ ] Method declared in writing: Safe Harbor, Expert Determination, or LDS.
- [ ] If Safe Harbor: every one of the 18 identifiers mechanically stripped; 3-digit-ZIP population test applied; all 90+ ages aggregated.
- [ ] If Expert Determination: statistician engaged, report on file, methods documented, re-evaluation scheduled if dataset changes.
- [ ] If LDS: DUA signed with recipient; remaining identifiers limited to dates and geography; other 16 identifiers removed.
- [ ] k-anonymity computed on the output; `k` recorded; threshold met.
- [ ] l-diversity evaluated for sensitive attributes; threshold met.
- [ ] No lookup table exists anywhere that reverses pseudonyms.
- [ ] Downstream systems receiving the data no longer treat it as PHI; audit logging and BAA obligations trace to the de-identification boundary.
- [ ] Re-evaluation cadence set (at least annually, or on any schema change).
