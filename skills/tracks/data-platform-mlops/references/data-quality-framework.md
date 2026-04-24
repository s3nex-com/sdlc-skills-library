# Data quality framework

Data quality is not a vibe. It is a set of measurable dimensions with tests, SLOs, and alerts. Bugs in request-response code surface immediately; data quality bugs can sit silently for a week before a dashboard owner notices the number is wrong. By then the damage — bad decisions made on bad data — is done. This framework names the dimensions, picks the tools, and wires them to SLOs so quality regressions surface within the freshness window, not at the quarterly review.

---

## The six dimensions

Every published dataset or topic should have tests across these six dimensions. Not every dimension applies to every dataset — but each one should be evaluated explicitly and either covered or consciously skipped with a written reason.

### 1. Freshness

How recent is the data? Freshness failures look like: "the dashboard shows yesterday's number because the pipeline stalled." Tested by comparing the max timestamp in the dataset to now; alerting when the lag exceeds the SLA.

- SLO example: "`fact_orders.order_timestamp` max is never more than 15 minutes behind wall clock."

### 2. Completeness

Are all the expected rows present? Are required fields populated? Completeness failures: a connector dropped 3% of events; a nullable column that should never be null has nulls.

- SLO example: "row count for `fact_orders` today is within ±5% of the 28-day median for the same day of week"; "`order_id` is never null."

### 3. Uniqueness

Is the primary key unique? Duplicates double-count revenue, inflate user counts, corrupt joins. Tested with simple `COUNT(*) == COUNT(DISTINCT pk)` assertions.

- SLO example: "`user_id` in `dim_user` is unique. Zero duplicates tolerated."

### 4. Referential integrity

Do foreign keys actually resolve? Orphan rows (`order.user_id` pointing to a user that doesn't exist) cause silent data loss in joins.

- SLO example: "100% of `fact_orders.user_id` resolves to a row in `dim_user`."

### 5. Timeliness

Does the data arrive on the expected schedule? Related to freshness but distinct: freshness asks how recent the data is; timeliness asks whether the scheduled run produced on time. A run that silently skipped yesterday passes freshness checks today but has a timeliness failure.

- SLO example: "daily `dim_user` refresh completes by 06:00 UTC. Missed schedule is a failure regardless of data age."

### 6. Conformance

Does the data match its stated schema, enum values, and value ranges? A `country_code` field that accepts `"USA"`, `"US"`, `"United States"` fails conformance even if it isn't null.

- SLO example: "`country_code` is a valid ISO-3166-1 alpha-2 code in 100% of rows. Unknown value is a failure."

---

## Tooling

Three tools cover the space. Pick one primary per team; mixing is fine at the boundaries.

| Tool | Best for | Strength | Weakness |
|------|----------|----------|----------|
| **dbt tests** | Warehouse models (SQL-based pipelines) | Tests live next to the model; runs as part of `dbt build`; free if you're already using dbt | Limited to SQL; no good story for streaming topics |
| **Great Expectations (GX)** | Any Python-accessible data (warehouse, parquet, streaming batches) | Rich expectation library; data docs generated; checkpoint pattern for CI | Heavier setup; YAML config grows |
| **Soda (Soda Core / Soda Cloud)** | Warehouse + files; SQL-first DSL | Compact `SodaCL` syntax; good monitoring integration | Less flexible than GX for custom checks |

For a 3-5 person team on a modern stack: dbt tests for warehouse models (they're free and already there), Great Expectations for anything outside dbt. Add Soda only if you need its monitoring UI.

---

## Per-dataset quality SLOs

Every dataset has an owner and an SLO document. Keep it in the contract file (see `data-contracts.md`) or in a sibling `quality.yaml`. Example:

```yaml
dataset: warehouse.fact_orders
owner: commerce-team
quality_slos:
  freshness:
    sla: "max(order_timestamp) within 15 minutes of wall clock"
    target: "99.5% of checks pass over 30-day window"
  completeness:
    sla: "row count within ±5% of 28-day DOW median; order_id never null"
    target: "99% of checks pass"
  uniqueness:
    sla: "order_id is unique"
    target: "100% of checks pass (zero tolerance for duplicates)"
  referential_integrity:
    sla: "user_id resolves to dim_user"
    target: "99.9% of checks pass; orphans logged and alerted"
  timeliness:
    sla: "hourly refresh completes within 10 minutes of schedule"
    target: "99% on-time"
  conformance:
    sla: "currency is a valid ISO-4217 code; amount >= 0"
    target: "100% of checks pass"
alerting:
  page: [freshness, uniqueness, referential_integrity]     # wake someone up
  ticket: [completeness, timeliness, conformance]          # file it for the next business day
error_budget_window: "30 days rolling"
```

### Alert classes

- **Page-worthy:** data is wrong now, users are seeing wrong numbers, or a downstream billing/ML system is poisoned. Freshness miss beyond SLA, uniqueness violation, referential integrity collapse.
- **Ticket-worthy:** data will be wrong soon or coverage is degraded. Completeness drift, timeliness miss, conformance regression.

Match the alert class to the business impact, not to how interesting the failure is technically.

---

## Worked example — dbt tests for `fact_orders`

File: `models/warehouse/fact_orders.yml`

```yaml
version: 2
models:
  - name: fact_orders
    description: One row per completed order, loaded hourly from the orders service.
    config: { contract: { enforced: true } }
    columns:
      - name: order_id
        data_type: string
        constraints: [{type: not_null}, {type: primary_key}]
        tests: [unique, not_null]
      - name: user_id
        data_type: string
        constraints: [{type: not_null}]
        tests:
          - not_null
          - relationships: { to: ref('dim_user'), field: user_id }
      - name: order_timestamp
        data_type: timestamp
        tests:
          - not_null
          - dbt_utils.expression_is_true: { expression: "order_timestamp <= current_timestamp() + interval 5 minute" }
      - name: amount
        data_type: numeric
        tests:
          - not_null
          - dbt_utils.expression_is_true: { expression: "amount >= 0" }
      - name: currency
        tests:
          - accepted_values: { values: ['USD','EUR','GBP','JPY','CAD','AUD'] }
    tests:
      - dbt_utils.recency: { datepart: minute, field: order_timestamp, interval: 15 }
```

Run this with `dbt test --select fact_orders` in CI and on every scheduled pipeline run. Failing tests block the downstream build by default.

**Alert wiring**: dbt test failure in the scheduled pipeline posts to `#data-quality-alerts`. Tests in the `page_worthy` list page the on-call via PagerDuty. All failures open a ticket with the failing test, sampled rows, and the lineage pointer.

---

## Worked example — Great Expectations suite for a Parquet landing zone

Use case: raw events land as Parquet in S3 before being loaded into the warehouse. dbt doesn't cover this. GX does.

Suite: `expectations/user_signup_landing.json` (summary)

```yaml
expectation_suite_name: user_signup_landing
data_asset_name: s3://events-landing/user_signup/
expectations:
  - expect_column_to_exist:
      column: user_id
  - expect_column_to_exist:
      column: email
  - expect_column_to_exist:
      column: signup_timestamp
  - expect_column_values_to_not_be_null:
      column: user_id
  - expect_column_values_to_be_unique:
      column: user_id
  - expect_column_values_to_match_regex:
      column: email
      regex: '^[^@]+@[^@]+\.[^@]+$'
  - expect_column_values_to_be_between:
      column: signup_timestamp
      min_value: "2020-01-01T00:00:00Z"
      max_value_fn: "now + 5 minutes"
  - expect_table_row_count_to_be_between:
      min_value_fn: "0.95 * rolling_28d_dow_median"
      max_value_fn: "1.05 * rolling_28d_dow_median"
  - expect_column_distinct_values_to_be_in_set:
      column: source
      value_set: [organic, referral, paid, partner]
```

A checkpoint runs the suite after every hourly landing, storing validation results, updating data docs, and notifying Slack on failure. Failure halts the downstream warehouse load; a partial hour does not poison the tables.

---

## Alerting and error budget

- Every SLO has an error budget. For the 99.5% freshness target, that's 3.6 hours of allowed failure per 30-day window.
- Burn rate monitored. Alert when burn is 10x expected — the budget will be gone in days, not weeks.
- Monthly data quality report lists every dataset's error budget consumption (see `TRACK.md` Phase 3 modification).

---

## Anti-patterns

- **Quality tests that only run at build time.** A test that passes on Monday's sample and is never run again against Wednesday's data is decorative. Tests must run on every scheduled pipeline execution.
- **Noisy tests nobody reads.** If a test fires daily for a month and nobody fixes it, either the SLO is wrong or the test is wrong. Either way, fix it. Test fatigue turns real failures invisible.
- **Testing the warehouse but not the source.** If the ingest landing zone is untested, every warehouse test is really a test of the loader too. Test at the landing edge.
- **One giant `models.yml` with no owner.** Every model needs an owner in its metadata. Unowned tests rot.

---

## Quick checklist per new dataset

- [ ] All six quality dimensions considered; coverage or skip-reason written down.
- [ ] SLO numbers agreed with consumers (not invented unilaterally).
- [ ] Tests wired to run on every scheduled pipeline execution, not only at build time.
- [ ] Alert class (page / ticket) chosen per test.
- [ ] Error budget and burn rate monitored.
- [ ] Owner named.
- [ ] Failures link to a runbook entry.
