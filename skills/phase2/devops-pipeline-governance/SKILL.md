---
name: devops-pipeline-governance
description: >
  Activate when designing or reviewing CI/CD pipelines, evaluating pipeline security and
  integrity, defining deployment strategies, establishing environment promotion policies,
  setting up release automation, governing infrastructure-as-code practices, defining rollback
  procedures, or troubleshooting pipeline failures blocking a release. Use for pipeline
  architecture, build reproducibility, deployment safety, environment parity, and the
  controls that ensure only reviewed and tested code reaches production.
---

# DevOps pipeline governance

## Purpose

The CI/CD pipeline is the delivery mechanism that turns code into running software. Pipeline governance ensures the pipeline itself cannot be tampered with, that deployments are auditable, and that rollbacks are reliable. A weak pipeline bypasses every quality and security control the team has agreed on — it is worth protecting.

---

## When to use

- Designing or reviewing the CI/CD pipeline architecture for a service or project
- A pipeline stage is failing or consistently slow and the root cause needs to be diagnosed
- Adding a new deployment environment or deployment strategy (canary, blue-green, rolling)
- A security audit has identified pipeline integrity problems (pinned SHAs, secret handling, approval gates)
- Setting up environment promotion policies (staging before production, manual approval gates)
- Defining or improving rollback procedures for deployments
- Infrastructure-as-code practices need to be established or audited (state management, drift detection)
- A pipeline needs to be hardened after an incident or near-miss

## When NOT to use

- Deciding whether a specific release is go/no-go — use `release-readiness`.
- Orchestrating a single PR through its gates to merge — use `pr-merge-orchestrator`.
- Defining the tests that run inside pipeline stages — use `comprehensive-test-strategy`.
- Enforcing API contract tests (Pact, schema registry) that run in the pipeline — use `api-contract-enforcer`.
- Writing database migration steps that the pipeline executes — use `database-migration`.
- Post-incident pipeline hardening as a corrective action — use `incident-postmortem` to identify actions, then this skill to implement them.

---

## Process

### Designing or reviewing a pipeline

1. Confirm the pipeline principles (see below) — every principle must be met. Any violation is a finding.
2. Map the standard pipeline stages against what exists. Identify missing stages or stages that run in the wrong order (e.g. security gates running after deployment).
3. Check pipeline security: third-party actions pinned to full SHA, no secrets printed in logs, CI service accounts have least-privilege, production approval gate exists.
4. Check rollback: verify the rollback procedure is written down, the previous artefact is accessible, and the rollback trigger conditions are defined.
5. Review deployment strategy: canary is the default. Confirm the strategy matches the service's risk profile.
6. For IaC: verify all infrastructure is in code, reviewed through PRs, and `terraform plan` output is reviewed before any production `apply`.
7. Produce the pipeline review checklist output.

### Improving a failing or slow pipeline

1. Identify which stage is failing or slow.
2. For failures: confirm the failure is deterministic, then trace to root cause (test, tooling, config, or environment).
3. For slow stages: look for parallelism opportunities, redundant work (rebuilding what could be promoted), or stages that could run earlier to fail fast.

### All sub-tasks

4. Append the execution log entry.

## Pipeline principles

1. **The pipeline is code.** Pipeline definitions are version-controlled, reviewed, and subject to the same quality standards as application code.
2. **Build once, promote everywhere.** Build a single artefact (container image, binary) and promote it through environments. Do not rebuild the same code for different environments.
3. **No manual steps between staging and production.** Any step that requires a human to click a button is a step that will be skipped under pressure.
4. **Fail fast, fail loud.** Gates that catch problems early (unit tests, SAST) run first. Long-running gates (integration tests, DAST) run after. Never hide failures.
5. **Deployments are repeatable.** Running the same pipeline twice produces the same outcome. No snowflake environments.
6. **Every deployment is auditable.** Who triggered it, what commit, what tests passed, when, to which environment.

---

## Pipeline stages

### Standard pipeline for a backend service

```
Commit pushed
    │
    ▼
[Stage 1: Fast checks] (~2 min)
  - lint + format check
  - type check
  - unit tests
  - secret scanning
    │
    ▼ (fail: block PR merge)
[Stage 2: Build] (~3 min)
  - compile / build
  - build container image
  - image tagging (git SHA + version)
    │
    ▼
[Stage 3: Security gates] (~5 min)
  - SAST (Semgrep)
  - SCA (Snyk)
  - container image scan (Trivy)
    │
    ▼ (fail: block PR merge on Critical/High)
[Stage 4: Integration tests] (~10 min)
  - start ephemeral dependencies (testcontainers)
  - run integration test suite
  - contract tests (Pact verification)
    │
    ▼ (fail: block merge)
[Stage 5: Deploy to staging] (~5 min)
  - push image to registry
  - deploy to staging (Helm upgrade / kubectl apply)
  - run smoke tests
    │
    ▼ (fail: auto-rollback staging)
[Stage 6: Acceptance + performance] (~20 min)
  - run acceptance test suite against staging
  - run performance smoke test (load profile: 10% of peak)
  - DAST scan against staging
    │
    ▼ (fail: block promotion)
[Stage 7: Deploy to production] (manual approval gate)
  - require approval from: {engineering lead}
  - deploy to production (canary: 10% traffic)
  - monitor for 10 minutes
  - promote to 100% OR rollback on error rate threshold
```

---

## Deployment strategies

### Default strategy: canary deployment

Deploy the new version to a small subset of traffic (e.g., 5–10%) while the old version handles the rest. Monitor error rates and latency. Incrementally increase canary traffic if metrics are healthy. Roll back by setting canary traffic to 0%.

**When to use:** Most standard deployments. Provides gradual risk exposure and automatic rollback on metric thresholds.

```yaml
# Argo Rollouts canary strategy
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10   # 10% of traffic to new version
        - pause: {duration: 5m}
        - analysis:       # Run analysis before proceeding
            templates:
              - templateName: success-rate-check
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 100
      canaryService: ingestion-service-canary
      stableService: ingestion-service-stable
      analysis:
        successCondition: "result[0] >= 0.999"
        failureLimit: 1
```

**When to use blue-green instead:** Services with stateful connections where rolling updates cause disruption, or major version releases requiring instant cutover. Blue-green requires double infrastructure during the switch — canary is cheaper for standard deployments.

**When to use feature flags:** When deployment needs to be decoupled from feature release (e.g., new customer-visible features, A/B testing). Add them when the specific need arises — not as a default.

---

## Infrastructure-as-code (IaC) governance

Core rules:
- All infrastructure is defined in code (Terraform, Pulumi, CDK, Kubernetes manifests)
- No manual changes to production infrastructure ("ClickOps" is prohibited)
- IaC changes go through the same PR process as application code
- `terraform plan` output is reviewed before `apply` runs in production
- State files are never committed to version control; use remote state with locking

IaC security gates in CI: `terraform validate` + security scan (Checkov or tfsec, block on Critical) before any `apply`.

See `references/iac-guide.md` for tool-specific patterns (Terraform state management, drift detection).

---

## Rollback procedures

### Automated rollback triggers

Configure automatic rollback when the deployment health check fails:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate | > 1% for 2 minutes | Auto-rollback canary to 0% |
| p99 latency | > 2× baseline for 2 minutes | Auto-rollback canary to 0% |
| Pod crash-loop | Any pod restarting > 3 times | Auto-rollback deployment |
| Health check failure | > 20% of pods failing /healthz | Auto-rollback deployment |

### Manual rollback procedure

```bash
# Kubernetes — rollback to previous revision
kubectl rollout undo deployment/ingestion-service -n edgeflow

# Verify rollback
kubectl rollout status deployment/ingestion-service -n edgeflow

# Check which image is now running
kubectl get deployment ingestion-service -o jsonpath='{.spec.template.spec.containers[0].image}'
```

For Helm-managed deployments:
```bash
# List revision history
helm history ingestion-service -n edgeflow

# Rollback to previous release
helm rollback ingestion-service -n edgeflow

# Rollback to specific revision
helm rollback ingestion-service 3 -n edgeflow
```

### Database migration rollback

Database migrations are the most dangerous part of a deployment. Follow these rules:
1. All migrations must be backward compatible with the previous application version (allow running old code against the new schema).
2. Destructive changes (column drops, type changes) use a three-phase process: add new → deploy new app → remove old.
3. Every migration has a corresponding down migration that is tested.
4. Migrations are run before the deployment, not as part of pod startup.

```bash
# Run migration before deployment (not during)
kubectl run db-migrate --image=companya/ingestion-service:1.2.0 \
  --restart=Never \
  --command -- python manage.py migrate

# Monitor migration completion
kubectl wait --for=condition=complete job/db-migrate --timeout=300s
```

---

## Pipeline security

### Secrets in CI
- Never print secrets with `echo` in pipeline scripts
- Use masked variables for all secrets in CI (GitHub secrets, GitLab CI variables with `masked: true`)
- Service account credentials used by CI have least-privilege permissions (deploy only to their target environment)
- Pipeline service accounts do not have production access until explicitly granted for the production stage

### Pipeline integrity
- All pipeline configuration files (`*.yml` in `.github/workflows/`) are reviewed in PRs
- Third-party GitHub Actions/GitLab CI components are pinned to a full commit SHA, not a tag
- Supply chain attacks via compromised actions are mitigated by SHA pinning

```yaml
# BAD — tag can be moved by attacker to point to malicious code
- uses: actions/checkout@v4

# GOOD — pinned to immutable SHA
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

### Audit log requirements

Every production deployment must be auditable. Log and retain:
- Triggered by (human or automated, with identity)
- Git commit SHA deployed
- Container image digest deployed
- All CI gates passed with pass/fail status
- Deployment timestamp
- Deployment to which environment

---

## Output format

### Pipeline review checklist

```
## Pipeline review: {Service name}

**Pipeline file:** {path}
**Reviewer:** {name}
**Date:** {date}

| Check | Status | Notes |
|-------|--------|-------|
| Tests run before build | ✅ | |
| Secrets not printed | ✅ | |
| Third-party actions pinned to SHA | ❌ | actions/checkout uses tag, not SHA |
| Build produces single artefact | ✅ | |
| Staging deployed before production | ✅ | |
| Production gate requires approval | ✅ | |
| Rollback procedure defined | ⚠️ | Procedure exists but not tested |

**Blocking findings:** {list}
**Recommendations:** {list}
```

---

## Skill execution log

When this skill fires, append one line to `docs/skill-log.md` before doing anything else:

```
[YYYY-MM-DD] devops-pipeline-governance — [one-line description of what was reviewed or changed]
```

If `docs/skill-log.md` does not exist yet, create it with the header defined in the `sdlc-orchestrator` skill.

Example entries:
```
[2026-04-20] devops-pipeline-governance — CI pipeline review: third-party actions pinned to SHA
[2026-04-20] devops-pipeline-governance — Blue-green deployment configured for ingestion-service
```

---

## Reference files

- `references/feature-flags-guide.md` — feature flag integration patterns for CI/CD pipelines, progressive delivery with flags, rollback via flag toggle, and flag hygiene in deployment workflows.
