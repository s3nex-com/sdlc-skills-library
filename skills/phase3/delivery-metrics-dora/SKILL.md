---
name: delivery-metrics-dora
description: >
  Activate when measuring or reporting delivery performance, calculating DORA metrics,
  evaluating a team's delivery velocity, investigating why deployment frequency has dropped,
  analysing lead time regressions, reporting on change failure rate after a string of
  incidents, or building a metrics dashboard for engineering leadership. Use when delivery
  data needs to be turned into insights, or when leadership needs evidence to support an
  investment decision about engineering capability.
---

# Delivery metrics and DORA

## Purpose

What gets measured gets managed. DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, MTTR) provide a research-validated, objective view of engineering delivery capability. They create a shared language for discussing delivery performance and make it obvious when something in the process is slowing the team down.

---

## When to use

- The monthly delivery performance report is due and DORA metrics need to be calculated and presented
- Deployment frequency has dropped and the cause needs to be diagnosed
- Lead time has increased over the last sprint or two and the team needs to find the bottleneck
- Change failure rate is trending up and correlates with a recent process change
- MTTR is consistently poor and the team needs to understand why incident response is slow
- A new project is starting — instrument for DORA from day one and establish proxy metrics for the cold-start period
- Engineering leadership needs evidence to support an investment in CI/CD tooling or process improvement

## When NOT to use

- **SLO, error budget, or reliability metrics** — use `observability-sre-practice`. DORA measures delivery capability; SLOs measure runtime reliability.
- **Sprint velocity, story points, or team health signals** — use `team-coaching-engineering-culture`. DORA is delivery throughput, not team-process metrics.
- **Performance or latency metrics** — use `performance-reliability-engineering`. DORA does not cover application performance.
- **Pipeline health or CI/CD configuration problems** — use `devops-pipeline-governance`. DORA surfaces symptoms; pipeline governance fixes the toolchain.
- **Final delivery report at project end** — use `project-closeout`, which incorporates the DORA final report alongside other closeout artefacts.

---

## Process

### Monthly report

1. Run the four DORA SQL queries (Deployment Frequency, Lead Time, Change Failure Rate, MTTR) against the deployments and incidents tables for the last 30 days.
2. If the sample size is below the statistical threshold (see "When to switch to real DORA metrics"), report proxy metrics instead and note the sample size.
3. Compare results against the previous month. Note the direction of each metric (improving / stable / degrading).
4. Populate the monthly delivery performance report template.
5. For any metric that has degraded for two consecutive sprints: start the performance degradation response process.

### Cold start (new project)

6. Create the deployments and incidents tables immediately — even a spreadsheet is acceptable initially.
7. Log every production deployment from day one: service, version, environment, deployed_at, status, caused_incident.
8. Log every incident: severity, detected_at, resolved_at.
9. Use proxy metrics for the first 2–3 months.

### Performance degradation response

10. Identify the primary driver: which of the four metrics is worst?
11. Look at the leading indicators: PR cycle time for Lead Time, WIP for Frequency, test coverage trends for Change Failure Rate, runbook quality and alert accuracy for MTTR.
12. Produce a root cause analysis and improvement plan with a 4-week tracking commitment.

### All sub-tasks

13. Append the execution log entry.

## DORA metrics defined

### Deployment Frequency (DF)

**Definition:** How often code is successfully deployed to production.

**Why it matters:** High frequency means small batches, which means lower risk per deployment, faster feedback, and less work in progress. Teams that deploy infrequently accumulate large, risky changes that take longer to test and more to roll back.

**How to measure:**
```sql
-- Deployments per day (30-day rolling average)
SELECT
  COUNT(*) / 30.0 AS deployments_per_day,
  COUNT(*) AS total_deployments
FROM deployments
WHERE environment = 'production'
  AND deployed_at >= NOW() - INTERVAL '30 days'
  AND status = 'success';
```

**Performance bands:**
| Elite | High | Medium | Low |
|-------|------|--------|-----|
| Multiple/day | Once/day – once/week | Once/week – once/month | < once/month |

### Lead Time for Changes (LT)

**Definition:** Time from code commit to that code running in production.

**Why it matters:** Short lead time means the team can respond quickly to customer feedback, fix bugs rapidly, and adapt to changing requirements. Long lead time is a sign of bottlenecks in testing, review, or deployment processes.

**How to measure:**
```sql
-- Average lead time in hours (commits to prod, 30 days)
SELECT
  AVG(
    EXTRACT(EPOCH FROM (d.deployed_at - c.committed_at)) / 3600
  ) AS avg_lead_time_hours,
  PERCENTILE_CONT(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (d.deployed_at - c.committed_at)) / 3600
  ) AS p50_lead_time_hours,
  PERCENTILE_CONT(0.95) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (d.deployed_at - c.committed_at)) / 3600
  ) AS p95_lead_time_hours
FROM deployments d
JOIN pull_requests pr ON pr.merged_sha = ANY(d.included_commits)
JOIN commits c ON c.sha = pr.first_commit_sha
WHERE d.environment = 'production'
  AND d.deployed_at >= NOW() - INTERVAL '30 days';
```

**Performance bands:**
| Elite | High | Medium | Low |
|-------|------|--------|-----|
| < 1 hour | 1 day – 1 week | 1 week – 1 month | > 1 month |

### Change Failure Rate (CFR)

**Definition:** Percentage of production deployments that cause a degradation requiring a hotfix, rollback, or incident.

**Why it matters:** High CFR indicates poor test coverage, inadequate review, or insufficient staging environments. It also erodes confidence in the deployment process, leading to longer release cycles (a vicious cycle).

**How to measure:**
```sql
-- Change failure rate (30 days)
SELECT
  COUNT(CASE WHEN caused_incident = TRUE THEN 1 END) AS failed_deployments,
  COUNT(*) AS total_deployments,
  ROUND(
    COUNT(CASE WHEN caused_incident = TRUE THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
    2
  ) AS failure_rate_pct
FROM deployments
WHERE environment = 'production'
  AND deployed_at >= NOW() - INTERVAL '30 days';
```

**Performance bands:**
| Elite | High | Medium | Low |
|-------|------|--------|-----|
| 0–5% | 5–10% | 10–15% | > 15% |

### Mean Time to Restore (MTTR)

**Definition:** Average time to restore service after a production incident.

**Why it matters:** Fast MTTR limits the business impact of incidents. MTTR is more controllable than preventing all incidents (MTTF). Good observability, runbooks, and rehearsed incident response all directly improve MTTR.

**How to measure:**
```sql
-- Mean time to restore (30 days, P1 and P2 incidents)
SELECT
  AVG(
    EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 60
  ) AS avg_mttr_minutes,
  PERCENTILE_CONT(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 60
  ) AS p50_mttr_minutes,
  COUNT(*) AS incident_count
FROM incidents
WHERE severity IN ('P1', 'P2')
  AND detected_at >= NOW() - INTERVAL '30 days'
  AND resolved_at IS NOT NULL;
```

**Performance bands:**
| Elite | High | Medium | Low |
|-------|------|--------|-----|
| < 1 hour | < 1 day | < 1 day | > 1 day |

---

## Additional delivery metrics

### PR cycle time (leading indicator for Lead Time)

```sql
-- PR cycle time breakdown
SELECT
  AVG(EXTRACT(EPOCH FROM (review_started_at - created_at)) / 3600) AS avg_time_to_first_review_hours,
  AVG(EXTRACT(EPOCH FROM (merged_at - review_started_at)) / 3600) AS avg_review_duration_hours,
  AVG(EXTRACT(EPOCH FROM (merged_at - created_at)) / 3600) AS avg_total_pr_time_hours,
  COUNT(*) AS pr_count
FROM pull_requests
WHERE merged_at >= NOW() - INTERVAL '30 days'
  AND merged_at IS NOT NULL;
```

### Deployment success rate

```sql
SELECT
  COUNT(CASE WHEN status = 'success' THEN 1 END) AS successful,
  COUNT(*) AS total,
  ROUND(COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*), 1) AS success_rate_pct
FROM deployments
WHERE environment = 'production'
  AND deployed_at >= NOW() - INTERVAL '30 days';
```

### WIP (Work in Progress)

High WIP is the single most common cause of long lead time. Track:
- Open PRs per engineer (target: ≤ 2 per engineer)
- PRs open > 3 days (ageing PRs create context-switching overhead)
- Stories in progress per engineer (target: 1 focus story + 1 support task)

---

## Metrics collection infrastructure

### Option A: GitHub Actions + data warehouse

```yaml
# .github/workflows/collect-metrics.yml
name: Collect delivery metrics

on:
  deployment_status:
  pull_request:
    types: [closed]

jobs:
  record-metrics:
    if: github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    steps:
      - name: Record deployment
        run: |
          curl -X POST ${{ secrets.METRICS_API_URL }}/deployments \
            -H "Authorization: Bearer ${{ secrets.METRICS_API_KEY }}" \
            -d '{
              "service": "${{ github.repository }}",
              "environment": "${{ github.event.deployment.environment }}",
              "sha": "${{ github.sha }}",
              "deployed_at": "${{ github.event.deployment_status.created_at }}",
              "status": "success"
            }'
```

### Option B: Linear / Jira integration

For teams using issue trackers, track:
- Story cycle time (opened → in progress → done)
- Bug escape rate (bugs found in production vs in testing)
- Planned vs actual sprint velocity

---

## DORA metric reporting

### Monthly delivery performance report

```
## Delivery performance report: {Team/Service} — {Month}

**Period:** {start} to {end}
**Report date:** {date}
**Prepared by:** {name}

### DORA metrics
| Metric | This month | Previous month | Target | Band |
|--------|-----------|----------------|--------|------|
| Deployment frequency | 2.3/day | 1.8/day | ≥ 1/day | Elite |
| Lead time | 4.2 hours | 6.1 hours | < 8 hours | Elite |
| Change failure rate | 3.2% | 4.7% | < 5% | Elite |
| MTTR | 18 min | 31 min | < 60 min | Elite |

### Deployment activity
Total deployments: 71 (67 success, 4 caused incidents)
Rollbacks: 2
Deployments requiring hotfix within 24h: 2

### Incidents summary
| Incident | Severity | MTTR | Root cause |
|----------|----------|------|-----------|
| INC-047 | P2 | 22 min | Device registry circuit breaker open — connection pool exhausted |
| INC-048 | P1 | 14 min | Kafka producer misconfiguration in v1.2.0 deploy — rolled back |

### Lead time breakdown (this month)
| Stage | Avg time | Previous month |
|-------|---------|----------------|
| First review response | 3.1 hours | 4.8 hours |
| PR review to merge | 2.7 hours | 3.9 hours |
| Merge to deploy | 0.4 hours | 0.4 hours |
| Total lead time | 6.2 hours | 9.1 hours |

### Highlights
- Lead time improved 32% month-over-month due to PR review SLA enforcement
- Change failure rate remains below target despite higher deployment volume

### Focus areas for next month
1. Investigate Monday morning latency spikes (possible cron job contention)
2. Add chaos engineering for device registry dependency (prevent repeat of INC-047)
```

### Quarterly trend review

At the end of each quarter, compare metrics quarter-over-quarter:

```
## Quarterly delivery trends: {Team/System}

| Metric | Q{n} | Q{n+1} | Change |
|--------|------|--------|--------|
| Deployment frequency | 0.8/day | 2.3/day | ↑ 188% |
| Lead time | 6.1 hours | 4.2 hours | ↓ 31% |
| Change failure rate | 4.7% | 3.2% | ↓ 32% |
| MTTR | 31 min | 18 min | ↓ 42% |

### Observations
{What drove the changes? What still needs attention?}

### Commitments for next quarter
{1–3 specific improvements with owners and success criteria}
```

## Month 0–3: Cold start

DORA metrics require historical data to be meaningful. A new project has no deployment frequency baseline, no failure rate, no MTTR. Don't skip measurement — start cheap.

### Instrument from day one (1–2 hours of setup, not a project)

Log these four fields for every production deployment from day one:

```sql
CREATE TABLE deployments (
  id          SERIAL PRIMARY KEY,
  service     TEXT NOT NULL,
  version     TEXT NOT NULL,
  environment TEXT NOT NULL,
  deployed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status      TEXT NOT NULL CHECK (status IN ('success', 'failed', 'rolled_back')),
  caused_incident BOOLEAN NOT NULL DEFAULT FALSE
);
```

Track incidents with start and end timestamps:

```sql
CREATE TABLE incidents (
  id          SERIAL PRIMARY KEY,
  severity    TEXT NOT NULL CHECK (severity IN ('P1', 'P2', 'P3')),
  detected_at TIMESTAMPTZ NOT NULL,
  resolved_at TIMESTAMPTZ,
  deployment_id INT REFERENCES deployments(id)
);
```

Track PR lead time via GitHub API or manually in the PR description (created_at, merged_at, deployed_at). A spreadsheet is fine until you have a real data store.

### Proxy metrics for weeks 1–8

Before you have enough deployments for DORA to be statistically meaningful, track these proxies:

| DORA metric | Proxy (weeks 1–8) | How to collect |
|-------------|------------------|----------------|
| Deployment Frequency | PRs merged to main per week | GitHub API or manual count |
| Change Failure Rate | Hotfixes or rollbacks per week | Incident log |
| MTTR | Time from alert to incident closed | Incident log (spreadsheet OK) |
| Lead Time | PR cycle time: opened → merged | GitHub PR timestamps |

These proxies move in the same direction as the real metrics and give you early signal without waiting for 50+ deployments.

### When to switch to real DORA metrics

| Metric | Switch when | Typically |
|--------|------------|-----------|
| Deployment Frequency | ≥ 20 production deployments | Month 2–3 |
| Change Failure Rate | ≥ 50 production deployments | Month 3–4 |
| MTTR | ≥ 5 incidents | Whenever you have them |
| Lead Time | ≥ 30 PRs merged | Month 1–2 |

Before these thresholds, report "n=X, not yet statistically meaningful" rather than a number that looks precise but isn't.

### Minimal tooling to start

A Postgres table beats a complex dashboard at month 0. The SQL queries in the DORA metrics section above work against the schema defined here. Start querying as soon as you have enough rows — no separate tool needed.

Don't spend more than 2 hours on DORA tooling before you have 3 months of data. The best metric infrastructure is the one you actually maintain.

---

## Output format

### Monthly delivery performance report

```
## Delivery performance: {Team/Service} — {Month YYYY}

**Period:** {start} to {end}
**Prepared by:** {name}

### DORA metrics
| Metric | This month | Previous month | Target | Band |
|--------|-----------|----------------|--------|------|
| Deployment frequency | {n}/day | {n}/day | {target} | Elite/High/Medium/Low |
| Lead time | {n} hours | {n} hours | {target} | Elite/High/Medium/Low |
| Change failure rate | {n}% | {n}% | < 5% | Elite/High/Medium/Low |
| MTTR | {n} min | {n} min | < 60 min | Elite/High/Medium/Low |

### Deployments
Total: {n} ({n} success, {n} caused incidents)

### Incidents
| Incident | Severity | MTTR | Root cause |
|----------|----------|------|-----------|

### Focus areas for next month
1. {specific improvement with owner}
```

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] delivery-metrics-dora — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] delivery-metrics-dora — April DORA report: Elite on DF and LT; High on CFR
[2026-04-20] delivery-metrics-dora — Velocity drop investigated: MTTR doubled due to infra flakiness
```

---

### Performance degradation response

If any DORA metric trends negative for more than one sprint:

1. Identify the primary driver (lead time? failure rate? frequency?)
2. Analyse the leading indicators (PR cycle time, WIP, test coverage, deployment success rate)
3. Produce a root cause analysis and improvement plan
4. Track against the improvement plan for the next 4 weeks

---

## Reference files

No reference files exist yet — the `references/` directory is available for DORA metrics dashboard templates, SQL query libraries for git-based metrics, and improvement plan templates as they are developed.
