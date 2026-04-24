# Flag registry template

Maintain one of these per project. Store as `flag-registry.yaml` in the repo root or as a table in your team wiki. The goal is a single, authoritative list of every active flag — type, owner, and expiry date visible at a glance.

---

## YAML format (recommended for version-controlled projects)

```yaml
# flag-registry.yaml
# Every active feature flag in this project.
# Release and experiment flags MUST have an expires date set at creation.
# Run `scripts/check-stale-flags.py` to surface overdue cleanup.

flags:

  - flag: release_new_device_onboarding
    type: release            # release | experiment | ops | permission
    owner: thanassis
    created: 2025-11-01
    expires: 2025-12-01
    default: false
    status: rolling-out (60%)
    description: New 5-min onboarding flow for IoT devices. Replaces 12-step legacy wizard.
    removal-criteria: stable at 100% for 14 days, no rollback events in 7 days

  - flag: exp_dashboard_layout_v2
    type: experiment
    owner: alice
    created: 2025-11-10
    expires: 2025-12-10
    default: control
    status: active (50/50 split)
    description: A/B test of new sidebar layout vs current top-nav layout.
    removal-criteria: experiment concluded, winner promoted to default

  - flag: ops_email_notifications
    type: ops
    owner: bob
    created: 2025-06-01
    expires: ~            # ops flags do not have a planned removal date
    default: true
    status: active (on)
    description: Kill switch for email notification delivery. Set to false to halt all outbound email without a deployment.
    removal-criteria: n/a — review annually

  - flag: perm_beta_api_v2
    type: permission
    owner: carol
    created: 2025-09-15
    expires: ~            # removed when API v2 is GA and v1 is dropped
    default: false
    status: active — enabled for 12 beta orgs
    description: Gates access to API v2 endpoints per organisation. Controlled via customer config.
    removal-criteria: API v1 deprecated and all customers migrated
```

---

## Markdown table format (for wikis and PR descriptions)

| Flag | Type | Owner | Created | Expires | Status | Description |
|------|------|-------|---------|---------|--------|-------------|
| `release_new_device_onboarding` | release | thanassis | 2025-11-01 | 2025-12-01 | Rolling out (60%) | New 5-min onboarding flow for IoT devices |
| `exp_dashboard_layout_v2` | experiment | alice | 2025-11-10 | 2025-12-10 | Active (50/50) | A/B test of sidebar vs top-nav layout |
| `ops_email_notifications` | ops | bob | 2025-06-01 | — | Active (on) | Kill switch for outbound email |
| `perm_beta_api_v2` | permission | carol | 2025-09-15 | — | Active (12 orgs) | Per-org gate for API v2 access |

---

## Naming conventions

| Flag type | Prefix | Example |
|-----------|--------|---------|
| Release | `release_` | `release_device_onboarding_new_flow` |
| Experiment | `exp_` | `exp_dashboard_layout_v2` |
| Ops / kill switch | `ops_` | `ops_email_notifications` |
| Permission / tenant gate | `perm_` | `perm_beta_api_v2` |

Pattern: `{prefix}{feature_area}_{what_it_controls}`

Avoid generic names like `new_feature`, `flag_1`, `test_mode`. The name should be readable in a log line without context.

---

## Stale flag detection query

If you maintain the registry as YAML, use this check in CI or a monthly audit script:

```python
import yaml
from datetime import date

with open("flag-registry.yaml") as f:
    registry = yaml.safe_load(f)

today = date.today()
stale = []
for flag in registry["flags"]:
    expires = flag.get("expires")
    if expires and expires != "~" and expires < today:
        stale.append(flag["flag"])

if stale:
    print("OVERDUE flag cleanup required:")
    for name in stale:
        print(f"  - {name}")
    exit(1)
```

---

## Cleanup checklist (copy into the cleanup task)

```
[ ] Remove flag check from all call sites in the codebase
[ ] Delete the else branch (old behaviour) and its supporting code
[ ] Remove tests that only exercised the old behaviour
[ ] Delete the flag from the flag service (Unleash / LaunchDarkly / env config)
[ ] Remove entry from flag-registry.yaml
[ ] PR reviewed and merged
[ ] Verify: grep for flag name returns zero matches in source (excluding this file)
```
