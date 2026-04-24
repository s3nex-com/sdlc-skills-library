# Feature flags and progressive delivery guide

## When to use feature flags vs canary deployment vs blue-green

These three techniques solve related but distinct problems. Using the wrong one creates unnecessary complexity.

| Technique | Use when | Key characteristic |
|-----------|----------|-------------------|
| **Feature flags** | Decoupling deployment from release; per-customer rollout; A/B testing; kill switches for risky integrations | Code is deployed but feature is off; you control who sees it and when |
| **Canary deployment** | Standard code deployments where you want to validate before full rollout | A percentage of traffic hits the new version; works at the infrastructure level, not per-feature |
| **Blue-green** | Major version releases with stateful connections that can't handle rolling restarts; instant cutover needed | Two full environments run simultaneously; traffic switches atomically |

**For most deployments: use canary.** It is the default progressive delivery mechanism — handled by your deployment tooling (Argo Rollouts, Flagger, etc.) without any code changes.

**Add feature flags when:** You need per-customer control, a kill switch independent of deployment, or you want to keep in-progress features deployable to production while they are incomplete.

**Use blue-green when:** You have a stateful service (WebSocket connections, long-running jobs) that cannot tolerate a rolling restart, or a breaking change that requires atomic cutover of multiple components simultaneously.

---

## Flag types

Using the right flag type clarifies intent, helps enforce cleanup discipline, and makes the flag register easier to manage.

### Release flags

Temporary flags that gate a new feature until it is fully rolled out. They have a short natural lifespan: create at feature start, remove after full rollout.

```python
if feature_flags.is_enabled("new_device_validation"):
    result = new_validation_service.validate(event)
else:
    result = legacy_validation_service.validate(event)
```

**Cleanup deadline:** Set at creation. Release flags should be removed within 2 sprints of reaching 100% rollout.

---

### Operational flags (kill switches)

Long-lived flags that act as circuit breakers for risky or expensive integrations. Unlike release flags, these are not expected to be removed — they are a permanent operational control.

```python
if feature_flags.is_enabled("email_notifications"):
    notification_service.send_email(event)
# If flag is off, silently skip — degraded but not broken
```

Kill switches should be used for: third-party API integrations with unreliable SLAs, expensive asynchronous jobs that can be safely deferred, and any feature where "off" is a safe degraded state.

---

### Experiment flags

Short-lived flags for A/B testing. They require targeting logic (e.g., assign users consistently to variant A or B) and cleanup after the experiment concludes.

```python
variant = feature_flags.get_variant("dashboard_layout", user_id=user.id)
if variant == "new_layout":
    return render_new_dashboard(user)
else:
    return render_legacy_dashboard(user)
```

**Cleanup deadline:** Remove when the experiment concludes and a winner is declared. Never leave experiment flags running indefinitely — the code path not taken accumulates drift.

---

### Permission flags

Long-lived flags tied to customer configuration. These control which customers have access to a feature — they are not temporary, they are an access control mechanism.

```python
if feature_flags.is_enabled("beta_api_v2", organisation_id=org.id):
    return api_v2_handler(request)
else:
    return api_v1_handler(request)
```

Permission flags live in customer configuration, not in a release flag system. They do not have a cleanup deadline — they are removed when the feature is generally available and the legacy path is dropped.

---

## Flag lifecycle management

This is the most important section. Flags that are not actively managed accumulate as debt — dead code paths, test complexity, configuration drift. The lifecycle is:

### 1. Creation

When creating a flag, decide and document:
- **Flag name:** descriptive and namespaced (`new_device_validation`, not `flag_1`)
- **Type:** release / operational / experiment / permission
- **Default value:** what happens when the flag service is unavailable or the flag is not configured
- **Owner:** who is responsible for removing it
- **Target removal date:** for release and experiment flags — set this at creation, not "later"

Register the flag in the flag register (see Flag debt management section).

---

### 2. Gradual rollout

For release flags, roll out incrementally with monitoring between each step:

```
0% → 1% → 10% → 50% → 100%
```

At each step:
- Monitor error rate, latency, and business metrics for 15–30 minutes
- If metrics degrade: set flag back to previous percentage; investigate
- If metrics are stable: proceed to the next step

Do not jump from 0% to 100% — the whole point of a flag-based rollout is the ability to limit blast radius.

---

### 3. Full rollout

When the flag reaches 100% and metrics are stable:
- Update the flag register: status = "pending cleanup"
- Assign a cleanup task to the sprint
- Do not leave the flag at 100% indefinitely — the else branch is now dead code

---

### 4. Cleanup

Cleanup means removing the flag AND the conditional code. The goal is a codebase with no flag checks — just the new behaviour.

1. Remove the flag check from code
2. Remove the else branch (the old behaviour)
3. Remove tests that tested the old behaviour
4. Delete the flag from the flag service configuration
5. Remove from the flag register

A PR that removes a flag should be straightforward — if it is large, the flag was probably gating too much.

**Maximum flag age for release flags:** 2 sprints after reaching 100% rollout. After that, the cleanup task is overdue.

---

## Testing with feature flags

**The critical rule: test both flag states (on and off) in CI.** Code that only passes tests with the flag on is not shippable.

### Parameterised tests for both states

```python
@pytest.mark.parametrize("flag_enabled", [True, False])
def test_ingest_with_new_validation(flag_enabled, feature_flags):
    feature_flags.set("new_device_validation", flag_enabled)
    # test behaviour for both states
    event = TelemetryEventFactory()
    result = ingestion_service.ingest(event)

    if flag_enabled:
        assert result.validated_by == "new_validation_service"
    else:
        assert result.validated_by == "legacy_validation_service"
```

### Test helper for flag control

Provide a test helper that explicitly sets flag state — never rely on the default value in tests:

```python
@pytest.fixture
def feature_flags():
    """Provides a feature flag client with explicit control for tests."""
    return InMemoryFeatureFlagClient(defaults={
        "new_device_validation": False,
        "email_notifications": True,
    })
```

The `InMemoryFeatureFlagClient` is a test double that accepts `flags.set("flag_name", True/False)` — no network calls, no external state, no test flakiness from flag service availability.

### Acceptance tests with flags

Tag BDD scenarios that depend on a flag and run the full suite with each state:

```gherkin
@flag:new_device_validation
Scenario: New validation rejects events from unregistered devices
  Given the "new_device_validation" flag is enabled
  When I POST a telemetry event from device "dev-999"
  And device "dev-999" is not registered
  Then the response status is 422
  And the error code is "DEVICE_NOT_REGISTERED_V2"
```

Run the suite twice in CI: once with all flags at their default, once with all `@flag:*` scenarios exercised with the flag explicitly enabled.

---

## Flag debt management

Flags accumulate silently. Without explicit management, a codebase can drift to dozens of active flags, many of which are effectively dead code paths that nobody dares to remove.

### Flag register

Maintain a simple register of all active flags. This can be a table in your internal wiki, a YAML file in the repository, or a dashboard in your flag service. At minimum, track:

| Flag name | Type | Default | Owner | Created | Target removal | Status |
|-----------|------|---------|-------|---------|---------------|--------|
| new_device_validation | Release | false | Alice | 2026-04-01 | 2026-05-15 | Rolling out (50%) |
| email_notifications | Operational | true | Bob | 2025-11-01 | — | Permanent |
| dashboard_layout | Experiment | control | Carol | 2026-04-10 | 2026-05-10 | Active |

---

### Weekly review

Every sprint planning or weekly sync: review flags past their target removal date. Any overdue flag gets a priority cleanup task in the current sprint. It is not optional — flag debt is real debt.

---

### Failing test for stale flags

Write a test that fails if a release flag has been at 100% for more than N days without being cleaned up:

```python
def test_no_stale_release_flags():
    """Fails if any release flag has been fully rolled out for more than 14 days."""
    stale_flags = [
        flag for flag in flag_register.get_all()
        if flag.type == "release"
        and flag.rollout_percentage == 100
        and (date.today() - flag.full_rollout_date).days > 14
    ]
    assert stale_flags == [], (
        f"Stale release flags detected (fully rolled out for > 14 days): "
        f"{[f.name for f in stale_flags]}. "
        "Remove the flag and its conditional code."
    )
```

This test failing in CI is a forcing function — it cannot be ignored like a Jira ticket can.

---

## Tooling options

### LaunchDarkly

Full-featured commercial flag service. SDKs for every language; sophisticated targeting (by user, organisation, percentage, custom attributes); experimentation platform built in; audit log. Best choice for teams that need complex per-user or per-organisation targeting and have budget for it.

- **Strengths:** Best-in-class targeting, analytics, and experimentation
- **Trade-offs:** Cost; vendor dependency; overkill for simple binary flags
- **Use when:** Per-customer or per-segment targeting is a core requirement

---

### Unleash

Open source, self-hosted (or Unleash-hosted). Good balance of features — percentage rollout, user targeting, environment awareness — without the cost of LaunchDarkly. Strong community and well-maintained SDKs.

- **Strengths:** Open source; self-hosted control; solid feature set; Kubernetes-friendly
- **Trade-offs:** You operate the infrastructure
- **Use when:** You need more than env-var flags but want full control and no vendor dependency

---

### Flipt

Open source, Kubernetes-native, lightweight. Simpler than Unleash; good gRPC API; designed for cloud-native environments. Good choice if you want flags managed as Kubernetes resources.

- **Strengths:** Lightweight; Kubernetes-native; low operational overhead
- **Trade-offs:** Smaller ecosystem; less mature than Unleash
- **Use when:** You are running on Kubernetes and want infrastructure-native flag management

---

### Environment variables

For the simplest cases — binary on/off per environment, no targeting, few flags — environment variables are a valid and underappreciated option. They require no external service, no SDK, no network calls, and no operational overhead.

```python
# Simple env-var flag (works fine for a small team with few flags)
ENABLE_NEW_DEVICE_VALIDATION = os.getenv("ENABLE_NEW_DEVICE_VALIDATION", "false").lower() == "true"
```

Set in your deployment configuration (Helm values, Kubernetes ConfigMap, docker-compose env) and control per-environment.

**Limitations:** No gradual rollout (it is all-or-nothing per deployment), no per-user targeting, no audit log. When you need those, move to Unleash or LaunchDarkly.

**For a small team with fewer than ~10 active flags and no per-customer targeting needs:** environment variables are a perfectly reasonable starting point. Just document them.

---

## Integration with the deployment pipeline

Feature flags and canary deployments are complementary — not alternatives. Here is how they fit together:

```
1. Feature developed behind a flag (flag default: off)
   → Code is merged and deployed to production
   → Feature is invisible to users — flag is off

2. QA validates the feature with flag on in staging
   → Flag is set to 100% in staging environment only
   → Run full acceptance test suite with flag on

3. Gradual production rollout
   → Canary handles the code deployment (e.g., 10% of pods run new code)
   → Feature flag separately controls who sees the new feature
   → Monitor: error rate, latency, business metrics at each rollout step

4. Full rollout
   → Flag reaches 100%
   → Canary completes — all pods run new code
   → Metrics stable for 24–48 hours

5. Cleanup sprint
   → Remove flag and conditional code
   → PR reviewed and merged
   → Flag removed from flag register
   → Done
```

The separation of concerns matters: the canary controls the code version running in production; the feature flag controls which users see the new behaviour. You can roll back the code without touching the flag, or disable the feature without rolling back the code.
