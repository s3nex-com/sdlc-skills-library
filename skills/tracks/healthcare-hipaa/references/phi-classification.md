# PHI classification — what's in, what's out, and how combinations turn plain data into PHI

PHI = Protected Health Information. Under HIPAA, it is any individually identifiable health information held or transmitted by a covered entity or business associate. "Individually identifiable" is the trap — it doesn't mean "has a name on it." It means "could be linked to a specific person, either directly or by combination."

A field is PHI if it meets both of these conditions:

1. It relates to health status, treatment, or payment for care.
2. It identifies or could reasonably be used to identify the individual.

Fields in isolation may not identify anyone. The same fields combined may identify one person in the entire United States. That combination is PHI.

---

## The 18 HIPAA identifiers (Safe Harbor list)

Any of these, in combination with health information, makes the record PHI. Removing all 18 is the Safe Harbor method of de-identification (see `de-identification-methods.md`).

1. **Names** — full name, initials if combined with other identifiers.
2. **Geographic subdivisions smaller than a state** — street address, city, county, precinct, ZIP code. The first 3 digits of a ZIP code may remain if the resulting geographic unit has >20,000 people (otherwise those digits too are stripped).
3. **Dates related to an individual** — birth date, admission date, discharge date, death date, all ages over 89 (must be aggregated to "90+").
4. **Telephone numbers**.
5. **Fax numbers**.
6. **Email addresses**.
7. **Social Security numbers**.
8. **Medical record numbers** (MRN).
9. **Health plan beneficiary numbers**.
10. **Account numbers** (patient account, billing).
11. **Certificate/license numbers**.
12. **Vehicle identifiers and serial numbers**, including license plates.
13. **Device identifiers and serial numbers** — pacemaker serial, CGM device ID.
14. **Web URLs**.
15. **IP addresses**.
16. **Biometric identifiers** — fingerprints, retinal scans, voiceprints.
17. **Full-face photographs and comparable images**.
18. **Any other unique identifying number, characteristic, or code** — this is the catch-all. A "patient reference code" you made up is on this list.

Memorise the shape of the list, not the numbering. The catch-all (#18) is what trips teams: the "anonymized" internal ID you assigned still links the record to a person if the lookup table exists anywhere.

---

## Which datasets in a typical system become PHI

| Dataset | Is it PHI? | Reason |
|---------|-----------|--------|
| `patients` table with name, DOB, MRN, diagnosis | Yes | Direct identifiers + health info |
| `appointments` table with patient_id → patients, time, provider, reason | Yes | Patient_id resolves via FK; reason is health info |
| `audit_log` entries for PHI reads | Yes | The fact that Patient X's record was accessed is itself PHI |
| `email_notifications` table with to_email, subject="Your lab results are ready" | Yes | Email + implicit health status |
| `device_telemetry` with device_serial, heart_rate, timestamp | Yes | Device serial (#13) + health measurement |
| `error_logs` containing "failed to load patient 12345 diagnosis=E11.9" | Yes | Accidentally includes PHI — this is a common leak |
| `system_metrics` — request count per endpoint, no patient IDs | No | Operational data, not identifiable |
| `user_sessions` for clinicians — staff email, login time | No (not PHI) | Clinicians aren't patients; this is staff PII, still protected but not PHI |
| `anonymized_aggregates` — count of diabetics by 3-digit ZIP where each group is >20 | No | Safe Harbor-compliant aggregation |
| `feature_flag_evaluations` with hashed user_id | Depends | If the hash can be reversed via a lookup table in your infra, yes. If truly one-way with no stored mapping, no. |

Logs and error tracking are the two datasets teams most often forget. Stack traces that include patient names or diagnoses have turned Sentry, Datadog, and ELK installations into unauthorised PHI repositories. Scrub before shipping, or don't send those fields.

---

## Quasi-identifiers — when non-PHI attributes combine to re-identify

A single attribute may not identify anyone. Several together often do. Sweeney's 2000 paper showed that **87% of the US population is uniquely identifiable by the combination of 5-digit ZIP + date of birth + gender**. None of those three, alone, is obviously a person's name. Together they narrow to one individual for almost everyone.

Common quasi-identifiers:

- ZIP code (even 3-digit, in low-population areas)
- Date of birth (even year-only, for very young or very old)
- Gender / sex
- Race, ethnicity
- Rare diagnosis (e.g., a specific genetic disorder — the patient population is small enough that diagnosis + region identifies them)
- Admission date + discharge date + hospital
- Occupation in a small town
- Device model + deployment location

If your "de-identified" dataset contains three or more of these, assume it is re-identifiable until you prove otherwise. See `de-identification-methods.md` for k-anonymity and risk assessment.

---

## Worked example — device table that is PHI by combination

Initial schema of a connected-device product:

```sql
CREATE TABLE devices (
    device_serial     TEXT PRIMARY KEY,          -- HIPAA #13
    owner_name        TEXT NOT NULL,             -- HIPAA #1
    owner_dob         DATE NOT NULL,             -- HIPAA #3
    owner_zip         CHAR(5) NOT NULL,          -- HIPAA #2
    owner_email       TEXT NOT NULL,             -- HIPAA #6
    last_reading_bpm  INT,                       -- health info
    last_reading_at   TIMESTAMP
);
```

This table is unambiguously PHI. Heart rate reading + name + DOB + ZIP + email + device serial = five Safe Harbor identifiers plus health data.

The team wants to keep an analytics-friendly dataset for trend analysis. Below are two rewrites — one wrong, one right.

### Wrong — pseudonymization with a reachable mapping

```sql
CREATE TABLE devices_analytics (
    pseudonym_id      TEXT PRIMARY KEY,          -- still PHI (#18)
    owner_age         INT NOT NULL,              -- derived from DOB
    owner_zip3        CHAR(3) NOT NULL,          -- first 3 of ZIP
    last_reading_bpm  INT,
    last_reading_at   DATE                       -- day precision
);

CREATE TABLE pseudonym_map (                     -- the lookup table
    pseudonym_id      TEXT,
    real_serial       TEXT
);
```

This is not de-identified. The `pseudonym_map` table exists in your infrastructure, so the pseudonym resolves to a real device and therefore a real person. Safe Harbor #18 catches this. You've reduced exposure but you have not de-identified.

### Right — Safe Harbor aggregation

```sql
CREATE TABLE devices_analytics_v2 (
    cohort_id         SERIAL PRIMARY KEY,
    age_band          TEXT NOT NULL,             -- '18-29', '30-44', '45-64', '65-89', '90+'
    zip3              CHAR(3) NOT NULL,          -- only if zip3 population > 20,000
    device_model      TEXT NOT NULL,
    cohort_size       INT NOT NULL CHECK (cohort_size >= 20),
    mean_bpm          INT,
    reading_month     CHAR(7) NOT NULL           -- 'YYYY-MM', no day
);
```

A row here is a cohort, not a person. The cohort_size constraint enforces k-anonymity (k=20). No serial, no DOB, no full ZIP, no day-level timestamp. This dataset supports trend analysis without carrying identifiable information.

The original `devices` table still exists, still has PHI, and is still subject to the full HIPAA control set — encryption, audit logging, BAA coverage, access review. The analytics derivative is a separate dataset with separate rules.

---

## Classification checklist — apply to every new table, index, log stream

- [ ] Does this data include any of the 18 HIPAA identifiers?
- [ ] Does it include health information (diagnosis, medication, procedure, payment for care, physical/mental condition)?
- [ ] Can an identifier be re-derived by combining fields (quasi-identifiers)?
- [ ] Is there a lookup table anywhere in the infrastructure that resolves pseudonyms back to individuals?
- [ ] Does this data end up in logs, error reports, analytics pipelines, or downstream caches that don't have the same controls as the source?
- [ ] If the answer to any of the above is "yes", the dataset is PHI. Apply the full control set: encryption at rest and in transit, access control, audit logging, BAA coverage for every third party that sees it, 6-year retention discipline.

Put this checklist in the PR template for any migration that adds or renames tables in a PHI-handling service. Reviewers check it. If any box is unchecked, the migration does not merge.
