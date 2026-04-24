# Layer boundary guide

Common layer structures and how to express them in `.fitness.yml`. Includes worked examples of violations and their fixes.

---

## Common layer structures

### Three-layer web app

```
api/          ← HTTP handlers, request parsing, response serialisation
services/     ← business logic, orchestration
db/           ← database access, ORM models, queries
```

```yaml
layer_boundaries:
  api:      [services]     # api calls services only
  services: [db]           # services call db only
  db:       []             # db has no downstream imports
```

**What is not allowed:** `services/` importing from `api/` (reverse flow), `api/` calling `db/` directly (skip layer).

---

### Four-layer with models

```
api/          ← handlers
services/     ← business logic
repository/   ← data access (no ORM details exposed above this layer)
models/       ← plain data classes, no logic
```

```yaml
layer_boundaries:
  api:        [services, models]       # handlers may read models for serialisation
  services:   [repository, models]
  repository: [models]
  models:     []
```

---

### Hexagonal (ports and adapters)

```
domain/       ← pure business logic, no framework imports
ports/        ← abstract interfaces (Python ABCs or protocols)
adapters/     ← implementations: HTTP, DB, message queue
config/       ← wiring and dependency injection
```

```yaml
layer_boundaries:
  domain:   []
  ports:    [domain]
  adapters: [ports, domain]
  config:   [adapters, ports, domain]
```

---

### Feature-based (vertical slices)

Some teams prefer features over layers. Fitness still applies — no cross-feature imports except through a shared kernel.

```
features/
  orders/
  payments/
  users/
shared/       ← types and utilities shared across features
```

```yaml
layer_boundaries:
  "features/orders":   [shared]
  "features/payments": [shared]
  "features/users":    [shared]
  shared:              []             # shared may not import from features
```

This prevents feature coupling: `payments/` cannot import `orders/` directly. Shared types live in `shared/`.

---

## Worked violations and fixes

### Violation: skip-layer import

```
VIOLATION: layer_boundary — api/routes/user.py imports db/session.py directly (api → db not allowed)
```

**Root cause:** engineer accessed the database session directly from a route handler to avoid writing a service method.

**Fix:** move the database access into `services/user_service.py` and call the service from the route:

```python
# Before (violation)
# api/routes/user.py
from db.session import get_session

# After (fix)
# api/routes/user.py
from services.user_service import get_user_by_id
```

---

### Violation: reverse flow

```
VIOLATION: layer_boundary — services/notification.py imports api/schemas.py (services → api not allowed)
```

**Root cause:** a Pydantic schema defined in `api/` was reused in a service for an internal data structure.

**Fix:** move the shared schema to `models/` or a `shared/` directory that both `api/` and `services/` may import:

```python
# Before (violation)
# services/notification.py
from api.schemas import NotificationPayload

# After (fix)
# services/notification.py
from models.notification import NotificationPayload
```

---

### Violation: circular import

```
VIOLATION: circular_import — services/order.py → services/payment.py → services/order.py
```

**Root cause:** two services call each other, creating a cycle.

**Fix:** extract the shared logic into a third module that both services import:

```python
# Before (cycle)
# services/order.py
from services.payment import charge_card

# services/payment.py
from services.order import get_order_total

# After (no cycle)
# services/pricing.py  ← new module
def get_order_total(order): ...

# services/order.py
from services.pricing import get_order_total

# services/payment.py
from services.pricing import get_order_total
```

---

## Defining layers by directory depth

`.fitness.yml` matches layer names to top-level directory names by default. For monorepos or nested structures, use path prefixes:

```yaml
layer_boundaries:
  "src/api":      ["src/services"]
  "src/services": ["src/db"]
  "src/db":       []
```

The scripts use prefix matching — `src/api/routes/user.py` matches the `src/api` layer rule.
