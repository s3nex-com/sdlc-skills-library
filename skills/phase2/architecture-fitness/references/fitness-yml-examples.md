# `.fitness.yml` examples

Annotated examples for three common architectures. Copy and adapt — the key is to define only the layers and rules that exist in your actual codebase.

---

## Layered monolith

Typical web app: API handlers → services → repository → models.

```yaml
# .fitness.yml
import_rules:
  no_circular_imports: true
  layer_boundaries:
    api:        [services, models]   # handlers may call services or read models directly
    services:   [repository, models]
    repository: [models]
    # nothing imports from api
  dependency_budget: 30
  approved_deps_file: approved-deps.txt

quality:
  coverage_floor: 75
  dead_module_days: 90

docs:
  api_docs_required: true
  adr_for_new_services: false       # monolith: no new top-level services expected
```

**What this enforces:**
- `api/` can call `services/` — fine
- `services/` calling `api/` directly — violation
- `repository/` calling `services/` — violation
- A new third-party dep not in `approved-deps.txt` — violation

---

## Microservices (per-service repo)

Each service is a standalone repo. Fitness rules enforce internal layer discipline within the service.

```yaml
# .fitness.yml
import_rules:
  no_circular_imports: true
  layer_boundaries:
    handlers:  [domain, infra]
    domain:    []                    # pure domain — no imports from other layers
    infra:     [domain]
  dependency_budget: 20             # tighter: services should be small

quality:
  coverage_floor: 80
  dead_module_days: 60              # tighter: small codebases should not have dead code

docs:
  api_docs_required: true
  adr_for_new_services: false
```

**Key difference from monolith:** `domain` has no allowed imports — it must be pure business logic. Any import from `infra` or `handlers` into `domain` is a hard violation.

---

## Hexagonal architecture (ports and adapters)

Core domain is isolated; adapters wrap external systems.

```yaml
# .fitness.yml
import_rules:
  no_circular_imports: true
  layer_boundaries:
    adapters:    [ports, domain]     # adapters implement ports and may use domain types
    ports:       [domain]            # ports define interfaces using domain types only
    domain:      []                  # domain is pure — zero external dependencies
    config:      [adapters, ports, domain]  # config wires everything together
  dependency_budget: 25

quality:
  coverage_floor: 85               # hexagonal is testable — hold it to a higher floor
  dead_module_days: 90

docs:
  api_docs_required: true
  adr_for_new_services: true       # new adapters require an ADR
```

**Common mistake:** placing framework code (FastAPI routes, SQLAlchemy models) in `domain/`. The fitness check will catch this once `domain: []` is enforced.

---

## Exceptions file

Place alongside `.fitness.yml` at the repo root.

```yaml
# .fitness-exceptions.yml
exceptions:
  - rule: layer_boundary
    location: config/bootstrap.py
    reason: "Bootstrap must reach db directly to initialise the connection pool before adapters load"
    owner: platform-team
    expires: 2026-09-01

  - rule: dependency_budget
    package: boto3
    reason: "S3 integration added in Q1 spike — evaluate moving to pre-signed URL proxy by Q3"
    owner: infra-team
    expires: 2026-07-01
```

Every exception must have `owner` and `expires`. Expired exceptions are treated as active violations by the CI scripts — they do not silently pass.
