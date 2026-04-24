# DR drill runbook

Templates and scripts for running drills. Load when SKILL.md step 5 (distinct playbooks) or step 6 (schedule drills) applies.

---

## Runbook template — single failure mode

Every playbook in a DR plan follows this structure. Keep each to 1–2 pages.

```
# Playbook: <failure mode name>
# Applies to: <system name, tier>

## Trigger
Explicit conditions that activate this playbook (not "things seem bad").
Example: "Cross-region replication lag >5min for 10+ minutes AND primary region health
check failing AND PagerDuty severity SEV-1 confirmed by on-call."

## Decision authority
Named role(s) with authority to declare the DR event and initiate failover.
Example: "On-call engineer may initiate read-only failover. Full failover (writes to DR
region) requires approval from Engineering Lead or CTO."

## Preconditions check (≤5 min)
1. Confirm failure mode — is this really a region outage, or is it the load balancer?
2. Check DR region health and replication freshness.
3. Confirm no in-flight maintenance that would conflict.

## Steps
Numbered, imperative, each with expected duration and success signal.
1. [2 min] Update status page: "investigating."
2. [5 min] Promote DR region replica to primary — run: `./scripts/promote-replica.sh --region eu-central-1`
3. [3 min] Shift DNS — run: `./scripts/shift-traffic.sh --target eu-central-1 --percent 100`
4. [5 min] Verify: synthetic smoke tests green in DR region.
5. [5 min] Update status page: "service restored, investigating root cause."

## Verification checklist
See SKILL.md step 8. Must complete before closing incident.

## Rollback path
If failover itself fails partway through, how to revert.
Example: "If step 3 fails, revert DNS to primary region. Replica promotion in step 2 is
reversible within 30 min by re-establishing replication from primary."

## Communication plan
- SEV-1 bridge open at T+0
- Customer-facing status page update at T+5min, every 30min thereafter
- Executive notification at T+15min via Slack #exec-incidents
- Post-restoration customer email if outage >30min

## Dependencies on other systems
What else must be working for this playbook to succeed?
Example: "Requires Route 53 control plane (if Route 53 is down, see alt-dns playbook)."
```

---

## Drill types

### 1. Tabletop walkthrough (quarterly, all tiers)

Goal: verify that the playbook still matches reality. No infra changes.

**Script:**

1. Schedule 60 min with on-call engineer, service owner, and one outside reviewer.
2. Pick a failure scenario. Announce it as the starting condition.
3. On-call walks through the playbook step by step. At each step:
   - Is the command accurate? (Does the script still exist? Same arguments?)
   - Is the expected signal still visible? (Is the dashboard still there?)
   - Would the preconditions check catch this scenario?
4. Reviewer flags any "I would actually do X instead" divergence from the playbook.
5. Record: time through the walkthrough, issues found, actions assigned.

Typical outputs: 2–5 minor updates to the runbook per tabletop. If a tabletop finds zero issues, the tabletop was shallow.

### 2. Real restore drill (semi-annual, Tier 1 / Tier 2)

Goal: prove that a backup actually restores, in the target region, within RTO.

**Script:**

1. Select a real backup (not the most recent — pick one 3–7 days old to test retention).
2. Restore into an isolated non-prod environment in the DR region.
3. Start timing at "initiate restore." Stop at "all verification checks pass."
4. Run the full restore verification checklist from SKILL.md step 8.
5. Compare wall-clock duration to RTO target. If restore+verify took 2h and RTO is 1h, the plan is broken.
6. Record RPO-delta: time of last write in the restored copy vs time the original was taken. Confirm within RPO target.
7. Tear down the non-prod restore environment.

**Evidence captured:**
- Start and end timestamps
- Data-volume restored
- Verification results (row counts, checksums, schema version)
- Issues found
- Cost of the drill (storage + compute for the restore env)

### 3. Full-region failover (annual, Tier 1)

Goal: cut real production traffic to the DR region. This is a real event, not a simulation.

**Prerequisites before running:**
- Previous tabletop and restore drill complete with no blocking issues
- Change request approved, customer-facing maintenance window if required
- All Tier 1 on-call staff available
- Leadership pre-informed

**Script:**

1. T-24h: Confirm DR region health. Verify replication lag within RPO target. Snapshot current state.
2. T-0: Declare drill start on #dr-drill Slack channel. Begin timing.
3. Execute the failover playbook exactly as written — no shortcuts. If something in the playbook is wrong, that is a finding; fix it after, not during.
4. Verify end-to-end customer traffic flows through DR region — synthetic transactions, real customer tail latency.
5. Hold in DR region for at least 30 min. This catches the "DR region works for 5 min then falls over" case.
6. Execute failback. Failback is its own procedure with its own risks — test it.
7. Declare drill end. Post results to the drill log.

**Do not do a full-region failover for the first time in prod.** Run the drill in a production-mirror environment first, then graduate.

### 4. Ransomware restore drill (annual, Tier 1 data)

Goal: prove the immutable copy is usable without the compromised IAM plane.

**Script:**

1. Create an **isolated** restore account / subscription / project. No trust relationship with production.
2. From a workstation with credentials that do NOT exist in the production IAM plane, authenticate to the isolated account.
3. Locate the immutable backup (read access should be pre-provisioned in the isolated account).
4. Restore into the isolated account's infrastructure.
5. Verify per checklist.
6. Document: how long from "we are compromised" to "we have a verified clean copy of data."
7. Tear down.

This drill is the specific defence test for ransomware. Do not skip on the assumption that a regular restore drill covers it — the IAM isolation is the thing being tested.

---

## Post-drill report template

```
# DR drill report — <drill type> — <date>

## Scope
System(s), failure scenario, participants.

## Targets
RTO: <target>
RPO: <target>

## Actual
RTO achieved: <actual duration>
RPO achieved: <actual data-loss delta>
Within target? YES / NO

## Timeline
T+0    Drill start
T+...  Each significant step with timestamp
T+end  Verification complete

## Issues found
1. <issue> — severity: blocking | major | minor — owner: <name> — due: <date>
2. ...

## Changes to plan
- <update to runbook step X>
- <new precondition check>

## Evidence
Links to logs, screenshots, verification outputs.

## Next drill
Date and type.
```

Drill reports are durable artefacts — link them from the DR plan. A drill with no written report didn't really happen for audit purposes (relevant for SOC 2 availability evidence).

---

## Common drill failure modes

- **Runbook drift** — command names have changed, URLs have moved, team Slack channel renamed.
- **Missing permissions** — the drill account can read the backup but cannot restore it.
- **Toolchain gaps** — the `promote-replica.sh` script assumes a tool that is not installed on the on-call laptop.
- **Unmeasured dependencies** — the restored service starts, but a dependency (secrets, DNS, CA cert) was not in scope of the drill and is still broken in DR.
- **Verification theatre** — "readiness probe green = done." Real verification is business-level: can a customer complete a transaction?

Any of these in a drill: record as a finding, assign an owner, track to closure before the next drill. The pattern "same finding 2 drills running" is a plan failure, not a team failure.

---

## When the drill goes wrong

Drills can cause real incidents. Precautions:

- Never drill without a rollback path defined.
- Never drill without a time-boxed abort criterion ("if not restored in 2x RTO, abort the drill and investigate").
- Protect customer traffic — drills that include live traffic shifts require the same change-approval process as a production deploy.
- If the drill triggers a real customer impact, treat as an incident, not a drill — invoke `incident-postmortem`.
