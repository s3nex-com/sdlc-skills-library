---
name: release-readiness
description: >
  Activate when assessing whether a release is ready for production, running a pre-release
  readiness review, creating a release checklist, writing a go/no-go decision, planning a
  deployment with rollback procedures, or tracking the resolution of pre-release blockers.
  Use for any production deployment decision where the consequences of getting it wrong are
  significant.
---

# Release readiness

## Purpose

A production deployment is a moment of commitment. Preparing for it rigorously prevents avoidable incidents and creates a clear audit trail if anything goes wrong. Release readiness is the systematic verification that all the conditions for a successful deployment are met before the deployment button is pressed.

---

## When to use

- A production deployment is being planned and the go/no-go decision needs to be made
- Pre-release verification is needed to confirm all quality gates have been passed
- A deployment plan needs to be written before a significant release
- There is uncertainty about whether a release is safe to proceed and a structured checklist review is needed
- Post-deployment verification is needed 24 hours after a release to confirm no degradation
- A release has been blocked and the reasons need to be formally documented and tracked

## When NOT to use

- Pre-release PR work (merging the last features, tagging, release notes) — use `pr-merge-orchestrator`.
- Designing or hardening the pipeline that executes the deployment — use `devops-pipeline-governance`.
- Running a post-incident review after a release goes wrong — use `incident-postmortem`.
- Running the milestone BDD sign-off suite against acceptance criteria — use `executable-acceptance-verification`.
- Sequencing schema changes with the release (expand-contract, lock-free DDL) — use `database-migration`.
- Defining operational SLOs and alerting that the release will be judged against in production — use `observability-sre-practice`.

---

## Process

1. Run the full release readiness checklist across all three categories: Code/build/tests, Database and data, Rollback. A single unchecked item is a no-go unless explicitly documented as a known exception with owner and resolution date.
2. For each failure: determine if it is a true blocker (must fix before deployment) or an accepted risk (can deploy with mitigation). Accepted risks require explicit documentation and an owner.
3. Answer the three go/no-go questions. If any answer is no — the deployment does not proceed.
4. Write the go/no-go decision record, even informally. Document who made the call.
5. Write the deployment plan: services being deployed, pre-deployment steps, step-by-step deployment sequence with rollback triggers, and post-deployment verification steps.
6. Name the rollback decision authority — one person who can call a rollback without further approval during the deployment window.
7. Execute the deployment plan. Monitor metrics during and after deployment.
8. 24 hours after deployment: run the post-release checklist. If any P1/P2 incident occurred, schedule a post-mortem.
9. Append the execution log entry.

## Release readiness checklist

Three categories. All must pass before deployment.

### 1. Code, build, and tests

- [ ] All changes for this release are merged; CI passes on the release branch
- [ ] Container images tagged with a specific version (not `latest`)
- [ ] All unit, integration, and contract tests pass
- [ ] Acceptance test suite passes
- [ ] Performance test done against this release; NFRs met (or deviations documented)
- [ ] Security gates passed: SAST clean, no Critical CVEs, secret scan clean

### 2. Database and data

This is the highest-risk category. Do not rush it.

- [ ] All database migrations are backward compatible with the currently deployed version
  (the old code must work against the new schema — critical for zero-downtime deploys)
- [ ] Migrations tested on staging with a production-volume data snapshot
- [ ] Migration runtime measured; estimated impact on production understood
- [ ] Each migration has a rollback script, and the rollback script is tested
- [ ] No schema change causes irreversible data loss without an explicit backup step

### 3. Rollback

- [ ] Rollback procedure is written down and available during the deployment
- [ ] Previous version's container image is accessible
- [ ] Database migration rollback tested (if applicable)
- [ ] Rollback decision authority named: who can call it, without needing further approval
- [ ] Team knows the rollback trigger criteria (what metric or error rate triggers the call)

---

## Go/no-go decision

Before deploying, answer three questions:

1. Do all three checklist categories pass? If not — no-go.
2. Is the rollback decision authority identified and available during the deployment window? If not — no-go.
3. Are there any open unknowns that could cause a production incident we have not mitigated? If yes — no-go.

Document the decision (even informally):

```
Go/no-go: {Release name} v{version}
Date: {date}
Decision: GO | NO-GO
Reason (if no-go): {what needs to be resolved}
Rollback authority: {name}
```

---

## Deployment plan

A deployment plan is the step-by-step record of what will happen during the deployment window.

### Deployment plan template

```markdown
# Deployment plan: {Release name} v{version}

**Deployment date:** {date}
**Deployment window:** {start time} — {end time} {timezone}
**Deployment lead:** {name}
**Communication channel:** {Slack channel / war room}
**Rollback decision authority:** {name} (can call rollback without further approval)

## Services being deployed
| Service | Old version | New version | Deployment method |
|---------|------------|-------------|------------------|
| ingestion-service | 1.1.0 | 1.2.0 | Canary (10% → 50% → 100%) |
| device-worker | 0.8.0 | 0.9.0 | Rolling update |

## Pre-deployment steps (T-60 to T-0)
| Time | Step | Owner | Verification |
|------|------|-------|-------------|
| T-60 min | Enable maintenance mode for non-critical batch jobs | Platform team | Confirm batch job queue drains |
| T-30 min | Final smoke test on staging | QA lead | All smoke tests pass |
| T-15 min | Notify stakeholder: deployment starting in 15 min | Engineering lead | Slack message sent |
| T-5 min | Take production Kafka consumer lag baseline reading | On-call engineer | Screenshot of Grafana dashboard |
| T-0 | Begin deployment | Deployment lead | Canary deploy initiated |

## Deployment steps
| Step | Command / action | Expected outcome | Rollback trigger |
|------|-----------------|------------------|-----------------|
| 1. Run database migrations | `kubectl run db-migrate --image=...` | Exit code 0; migration log shows success | Exit code non-zero; migration error in log |
| 2. Deploy ingestion-service canary (10%) | `helm upgrade ingestion-service --set canary.weight=10` | 10% of pods running new version | Error rate > 1% within 5 min |
| 3. Monitor canary for 5 minutes | Watch Grafana dashboard | Error rate < 0.1%; p99 < 500ms | Error rate > 1% OR p99 > 1s |
| 4. Promote to 50% | `helm upgrade ingestion-service --set canary.weight=50` | 50% of pods running new version | As above |
| 5. Monitor for 5 minutes | Watch Grafana dashboard | Metrics stable | As above |
| 6. Promote to 100% | `helm upgrade ingestion-service --set canary.weight=100` | All pods running new version | As above |
| 7. Deploy device-worker | `helm upgrade device-worker` | Rolling update completes | CrashLoopBackOff in any pod |

## Post-deployment verification (T+0 to T+30)
| Check | Method | Pass criteria |
|-------|--------|--------------|
| Kafka consumer lag | Grafana dashboard | Lag < 1,000 messages within 10 min |
| Ingestion error rate | Grafana dashboard | Error rate < 0.1% sustained for 10 min |
| End-to-end test | Run `make e2e-smoke` | All smoke tests pass |
| Integration verification | Run `make e2e-smoke` + check dependent services | All smoke tests pass; no errors in dependent services |

## Rollback procedure
If the rollback trigger condition is met:
```bash
# Rollback ingestion-service
helm rollback ingestion-service -n edgeflow

# Verify rollback
kubectl rollout status deployment/ingestion-service -n edgeflow

# Check rolled-back version
kubectl get pods -n edgeflow -l app=ingestion-service -o jsonpath='{.items[0].spec.containers[0].image}'
```

Notify: post in {Slack channel} and email the engineering lead immediately.
```

---

## Post-release checklist (T+24 hours)

- [ ] All deployment steps completed successfully
- [ ] No P1/P2 incidents in the first 24 hours
- [ ] Kafka consumer lag returned to baseline
- [ ] Performance metrics nominal (no regressions from pre-release baseline)
- [ ] Downstream consumers / dependent services confirmed working
- [ ] Release notes sent to stakeholders
- [ ] Deployment audit log archived (CI run link, image digest, who approved)

If an incident occurred within 24 hours:
- [ ] Post-incident review scheduled within 48 hours
- [ ] Preliminary root cause identified
- [ ] Stakeholders informed with factual summary (not speculation)

---

## Output format

### Release readiness report

```
## Release readiness report: {Service name} v{version}

**Report date:** {date}
**Release planned:** {date and time}
**Report author:** {name}

### Readiness summary
| Section | Status | Blockers |
|---------|--------|---------|
| Code and build | ✅ Ready | None |
| Testing | ⚠️ Partial | Load test in progress (completes {time}) |
| Database | ✅ Ready | None |
| Configuration | ✅ Ready | None |
| Infrastructure | ✅ Ready | None |
| Observability | ✅ Ready | None |
| Rollback | ✅ Ready | None |
| Downstream verification | ⚠️ Partial | Integration smoke test pending |

**Overall status:** ⚠️ NOT READY — 2 items outstanding

### Required before go/no-go
1. Load test results (ETA: {time}) — **Owner: the QA team**
2. Stakeholder notification sent — **Owner: the engineering lead**

### Next review
Go/no-go meeting scheduled: {date and time}
```

## Skill execution log
When this skill fires, append one line to `docs/skill-log.md`:
[YYYY-MM-DD] release-readiness — [service and version, e.g., "ingestion-service v1.2.0 — GO"]
If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

---

## Reference files

- `references/database-migration-guide.md` — patterns and checklist for safely running database migrations as part of a production release, including expand-contract, lock-free DDL, and rollback procedures.
