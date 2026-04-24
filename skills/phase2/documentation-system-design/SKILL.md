---
name: documentation-system-design
description: >
  Activate when creating system design documents, writing runbooks, producing architecture
  diagrams, documenting API usage guides, writing onboarding documentation for a new
  engineer, reviewing documentation quality for a milestone or production release, creating
  incident response runbooks, producing system context diagrams, or evaluating whether
  documentation meets the standard required for a production deployment. Use when a system
  lacks sufficient documentation for the team to operate it safely, or when docs need to
  be assessed before a release gate.
---

# Documentation system design

## Purpose

Documentation is an engineering artefact, not an afterthought. A system that cannot be operated, debugged, or extended without the original author is not a complete delivery — regardless of how good the code is. Documentation is what lets the next engineer (or you in six months) run this safely.

---

## When to use

- A new service or feature is approaching production and documentation does not yet exist for on-call engineers
- The root README is absent, stale, or insufficient for a new engineer to set up the project
- An operational handover is planned and the receiving team needs documentation to operate the system safely
- A documentation quality assessment is required as part of a release gate
- A system context diagram is needed to communicate the architecture to stakeholders
- Runbooks need to be written for P1/P2 operational scenarios before go-live
- An API usage guide (distinct from the spec) needs to be written for consuming developers

## When NOT to use

- Producing the upstream `DESIGN.md` that feeds implementation — use `design-doc-generator`.
- Writing architecture decision records for significant design choices — use `architecture-decision-records`.
- Writing or freezing API specifications (OpenAPI, Protobuf) — use `specification-driven-development`.
- Producing the PRD that captures product intent — use `prd-creator`.
- Recording a postmortem narrative and corrective actions after an incident — use `incident-postmortem`.
- Final handover artefacts at the end of an engagement — use `project-closeout`.

---

## Documentation types and when to create each

| Type | When created | Owner | Audience |
|------|-------------|-------|---------|
| System context diagram | Architecture design phase | Architect | All technical stakeholders |
| Architecture decision record | When a significant technical decision is made | Decision author | Future engineers |
| API reference | When an API is designed (specification-first) | API author | Consuming developers |
| Runbook | Before production deployment | Engineering lead | On-call engineers |
| Incident response playbook | Before production deployment | Engineering lead | On-call engineers |
| Onboarding guide | Before a new team member starts | Team lead | New engineers |
| Root README | At project creation; kept current | Engineering lead | Any new developer |
| Data dictionary | When new data stores are created | Data owner | All engineers |
| Operational handover | Before handover milestone | Delivering company | Receiving company |

---

## Root README

Every project must have a `README.md` at the repo root. It is the first thing any new developer sees and must answer four questions without requiring them to read code.

### Root README template

```markdown
# {Project name}

{One sentence: what this system does and who uses it.}

## Quickstart

```bash
# Prerequisites: {list runtime/tool versions}
git clone {repo}
cd {repo}
{install command}
{run command}
```

Open {URL or describe what they should see}.

## Project structure

| Directory | Purpose |
|-----------|---------|
| `{dir}` | {what's in it} |

## Key links

- API reference: {link to rendered spec or /docs route}
- Architecture decision records: `docs/adr/`
- Runbooks: `docs/runbooks/`
- Changelog: `CHANGELOG.md`

## Contributing

{One paragraph or link to CONTRIBUTING.md}
```

**What to avoid:** Do not put operational details, environment-specific config, or secrets guidance in the root README. Those belong in runbooks and the onboarding guide.

---

## System context diagram

Every system must have a context diagram showing:
1. The system itself (the black box)
2. External actors and systems that interact with it
3. The data flows between them (what, not how)

Use the C4 model level 1 (System Context). Keep it simple enough to share with non-engineers.

### Mermaid example: EdgeFlow telemetry platform context

```
C4Context
  title System context: EdgeFlow telemetry platform

  Person(device_operator, "Device Operator", "Company B engineer who configures and monitors devices")
  Person(analyst, "Data Analyst", "Company A analyst consuming telemetry data")

  System(edgeflow, "EdgeFlow Platform", "Receives, validates, stores, and distributes telemetry events from edge devices")

  System_Ext(device_fleet, "Device Fleet", "Company B edge devices that generate telemetry events")
  System_Ext(device_registry, "Device Registry API", "Company B service that maintains device registration records")
  System_Ext(analytics_platform, "Analytics Platform", "Downstream consumer of telemetry events (Company A)")
  System_Ext(alerting, "PagerDuty", "On-call alerting for the platform team")

  Rel(device_fleet, edgeflow, "Sends telemetry events", "HTTPS/REST")
  Rel(edgeflow, device_registry, "Validates device registration", "HTTPS/REST")
  Rel(edgeflow, analytics_platform, "Publishes events", "Kafka")
  Rel(edgeflow, alerting, "Sends alerts", "HTTPS")
  Rel(device_operator, edgeflow, "Monitors event ingestion", "Web UI")
  Rel(analyst, analytics_platform, "Queries telemetry data", "SQL")
```

---

## Runbook structure

A runbook is a step-by-step operational guide for a specific procedure. It exists so that an on-call engineer who has never touched the system before can execute the procedure correctly under pressure.

### Runbook template

```markdown
# Runbook: {Procedure name}

**Service:** {Service name}
**Last updated:** {Date}
**Owner:** {Team or person responsible for keeping this current}
**Escalation contact:** {Name and contact for when this runbook is not enough}

## When to use this runbook
{Describe the specific scenario that triggers use of this runbook.
Example: "Use this runbook when PagerDuty fires the 'IngestionLag > 30s' alert."}

## Severity
{P1 — System down | P2 — Degraded | P3 — Warning}

## Prerequisites
Before starting, ensure you have:
- [ ] Access to the Kubernetes cluster ({cluster name})
- [ ] Access to the logging platform ({URL})
- [ ] Access to the metrics dashboard ({URL})
- [ ] The encryption key for the secrets manager (if applicable)

## Diagnosis steps

### Step 1: Check current status
```bash
kubectl get pods -n edgeflow -l app=ingestion-service
kubectl top pods -n edgeflow -l app=ingestion-service
```
Expected output: {describe what healthy output looks like}
If you see {specific error}: proceed to step {n}

### Step 2: Check recent logs
```bash
kubectl logs -n edgeflow -l app=ingestion-service --since=15m | grep -E "ERROR|WARN"
```
Common error patterns and what they mean:
- `"database connection pool exhausted"` → proceed to step 4 (DB connection issue)
- `"device registry unreachable"` → proceed to step 5 (dependency outage)

## Resolution procedures

### Resolution A: Restart the ingestion service
Use this when: pods are in CrashLoopBackOff or error rate is high with no clear root cause in logs
```bash
kubectl rollout restart deployment/ingestion-service -n edgeflow
kubectl rollout status deployment/ingestion-service -n edgeflow
```
Verify: error rate drops below 0.1% within 3 minutes (check Grafana dashboard)
If not resolved within 5 minutes: escalate to {escalation contact}

## Post-incident actions
- [ ] File an incident report within 24 hours
- [ ] Update this runbook if steps were unclear or incorrect
- [ ] Add any new failure patterns discovered to the "Common error patterns" section
```

---

## API usage guide structure

For every API delivered as part of the engagement, provide a usage guide that goes beyond the OpenAPI spec. The spec says what the API does; the guide says how to use it effectively.

### API usage guide template

```markdown
# API usage guide: {API name}

**Version:** {version}
**Base URL:** {staging and production URLs}
**OpenAPI spec:** {link}

## Authentication

{Describe how to obtain credentials and how to include them in requests.
Include a working curl example.}

```bash
# Obtain an API key (Company A provisioning process — contact api-support@companya.example.com)
# Include the key in every request:
curl -X POST https://api.edgeflow.example.com/v1/events \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "dev-001", "event_type": "temperature", "timestamp": "2024-01-15T10:00:00Z"}'
```

## Common operations

### Ingest a single event
{request example, response example, field descriptions for non-obvious fields}

### Batch ingest
{…}

## Error handling

Describe the error envelope, list the most common error codes and what to do:

| Error code | HTTP status | Meaning | What to do |
|------------|-------------|---------|------------|
| DEVICE_NOT_REGISTERED | 422 | Device ID is not in the registry | Verify device is registered via Device Registry API |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests | Back off for the duration in Retry-After header |
| TIMESTAMP_OUT_OF_RANGE | 422 | Timestamp is more than 24h in the past or future | Sync device clock; check timezone handling |

## Rate limits

{Rate limit per API key, per IP, per endpoint. How limits are communicated (headers). What happens when exceeded.}

## Idempotency

{If the API supports idempotency keys, explain how to use them and what guarantees they provide.}

## SDK / client libraries

{Links to official client libraries if they exist. If none, a minimal working client example in the partner's primary language.}
```

---

## Operational handover document

When delivering a system to a partner company for operation:

```markdown
# Operational handover: {System name}

**Version:** {version}
**Handover date:** {date}
**Delivering team contact:** {name, email}
**Receiving team contact:** {name, email}

## System overview
{2-3 paragraph description of what the system does, who uses it, and its criticality}

## Architecture
{Link to architecture document and context diagram}

## Access and credentials
{How the receiving team obtains access to:
- Kubernetes cluster
- Container registry
- Secrets manager
- Monitoring and logging platform
- CI/CD pipeline
- Database admin access (break-glass)}

## Runbooks available
| Scenario | Runbook |
|----------|---------|
| High ingestion lag | {link} |
| Pod crash loop | {link} |
| Database connection exhaustion | {link} |
| Certificate expiry | {link} |

## Monitoring and alerting
{What alerts exist, where they fire, what the thresholds are, and who is on-call}

## Known issues and limitations
{List any known bugs, workarounds, and technical debt that the receiving team needs to be aware of}

## Support model
{How long the delivering company provides support post-handover, what is in scope, escalation path}
```

---

## Documentation quality checklist

Use when assessing documentation delivered as part of an engagement milestone:

### Completeness
- [ ] Root `README.md` exists at repo root with: project description, quickstart, project structure, and links to further docs
- [ ] OpenAPI spec is rendered and accessible to consumers (Swagger UI, Redoc, or `/docs` route) — a spec file in the repo is not sufficient
- [ ] System context diagram exists and is current
- [ ] All public API endpoints documented (OpenAPI spec + usage guide)
- [ ] Runbooks exist for all P1 and P2 operational scenarios
- [ ] Architecture decisions recorded in ADRs
- [ ] Data dictionary for all significant data stores
- [ ] Onboarding guide enables a new engineer to set up a local environment without help

### Accuracy
- [ ] Documentation version matches the delivered software version
- [ ] All curl / code examples tested and working
- [ ] No placeholder text ("[TODO]", "[INSERT HERE]", "{example}")
- [ ] Credentials and endpoints are for the correct environment (not dev hardcoded)

### Usability
- [ ] A new engineer could execute each runbook without prior knowledge
- [ ] API guide contains error handling guidance, not just happy path
- [ ] Architecture document explains decisions, not just the outcome
- [ ] Diagrams are at the correct level of abstraction for the audience

### Operational readiness
- [ ] Runbooks include escalation contacts with current contact details
- [ ] Runbooks include expected resolution time
- [ ] All dashboards linked in runbooks are deployed and accessible
- [ ] Handover document includes known issues and active workarounds

---

## Process

### Assessing documentation completeness

1. Run the documentation quality checklist (Completeness → Accuracy → Usability → Operational readiness).
2. For each missing or inadequate item, record the gap with a specific required action and an effort estimate.
3. Produce the documentation gap assessment in the output format.

### Creating a runbook

1. Identify the specific scenario the runbook covers. One scenario per runbook — do not create a generic "troubleshooting guide".
2. Write the runbook following the template: when to use, severity, prerequisites, diagnosis steps, resolution procedures, post-incident actions.
3. Include specific commands and their expected outputs. A runbook without executable commands is not a runbook — it is a narrative.
4. Include escalation contacts with current contact details.
5. Test the runbook: can an engineer who has never touched the service execute it without additional context?

### Creating a system context diagram

1. Identify the system (the black box), external actors, and data flows.
2. Render using C4 Level 1 (System Context) in Mermaid or ASCII. Label every arrow with protocol and data type.
3. Keep it simple enough to share with non-engineers.

### Creating an API usage guide

1. Write the authentication section first — include a working curl example.
2. Cover common operations with request and response examples for each.
3. Document error codes, their meanings, and what the caller should do.
4. Cover rate limits and idempotency.

### Operational handover

1. Fill the handover document template. Include known issues and active workarounds — omitting these is a failure mode.
2. Verify all runbooks linked from the handover are complete and tested.
3. Confirm the receiving team has access to all required systems before handing over.

### All sub-tasks

4. Append the execution log entry.

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] documentation-system-design — [one-line description of what was triggered]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] documentation-system-design — Runbook created for ingestion service P1 scenarios
[2026-04-20] documentation-system-design — Handover documentation reviewed for device-registry
```

---

## Output format

### Documentation gap assessment

```
## Documentation gap assessment: {System name}

**Assessment date:** {date}
**Assessor:** {name}

| Document type | Exists? | Meets standard? | Gap description |
|---------------|---------|-----------------|-----------------|
| System context diagram | ✅ Yes | ✅ Yes | — |
| Architecture decisions | ✅ Yes | ⚠️ Partial | ADRs exist but 3 major decisions undocumented |
| API reference | ✅ Yes | ✅ Yes | — |
| Runbooks | ⚠️ Partial | ❌ No | Only 2 of 7 P1 scenarios covered |
| Onboarding guide | ❌ No | ❌ No | Missing entirely |

**Overall status:** NOT READY FOR HANDOVER

**Required before handover:**
1. Complete runbooks for P1 scenarios: {list}
2. Create onboarding guide
3. Document ADRs for {list of decisions}

**Estimated effort:** {rough estimate}
**Required by:** {date per contract milestone}
```

---

## Reference files

No reference files exist yet — the `references/` directory is available for runbook templates, C4 diagram starters, API documentation style guides, and operational handover checklists as they are developed.
