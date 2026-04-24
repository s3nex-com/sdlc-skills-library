# Local dev setup patterns

Target: a new engineer has the full stack running locally in **under 90 minutes on day 1**. If it takes longer, the setup is the problem and needs fixing before the next hire.

---

## Principles

1. **One command to bring up, one command to tear down.** `make up` / `make down` or equivalent. If there are more steps, they are bugs.
2. **Tool versions pinned explicitly** via `asdf` or `mise` (`.tool-versions` file committed). Not "install Node 20" — the exact patch version.
3. **Secrets for local dev never leave local.** Developers either use a shared sandbox secret bundle or a per-developer `.env.local` generated from a template. Never the real production secrets.
4. **Seed data ships with the repo.** A fresh checkout produces a working app with sample users, not an empty database.
5. **Smoke test verifies the stack is up.** `make smoke` runs a `/healthz` curl and one read-write round trip. Exits non-zero on failure.

---

## Tool version pinning

Pick one, commit the config, document in README.

### asdf / mise

Both read a `.tool-versions` file at the repo root:

```
# .tool-versions
nodejs 22.11.0
python 3.12.5
golang 1.23.3
terraform 1.9.8
docker-compose 2.29.0
```

`mise` is the newer, faster option; `asdf` has wider plugin ecosystem. Either works — pick one team-wide, don't mix.

On first clone:
```bash
mise install        # installs every version in .tool-versions
mise current        # verify versions are active
```

---

## Docker Compose template

Minimum pattern for a typical service (API + DB + cache + message bus):

```yaml
# compose.yaml
services:
  api:
    build: .
    environment:
      - DATABASE_URL=postgres://dev:dev@db:5432/app
      - REDIS_URL=redis://cache:6379
      - NATS_URL=nats://bus:4222
      - AUTH_SECRET_FILE=/run/secrets/auth_local
    env_file:
      - .env.local
    ports: ["8080:8080"]
    depends_on:
      db:
        condition: service_healthy
      cache: { condition: service_started }
      bus:   { condition: service_started }
    secrets: [auth_local]

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=dev
      - POSTGRES_DB=app
    volumes:
      - ./dev/seed.sql:/docker-entrypoint-initdb.d/seed.sql:ro
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d app"]
      interval: 2s
      retries: 20

  cache:
    image: redis:7-alpine

  bus:
    image: nats:2.10-alpine

volumes:
  db_data:

secrets:
  auth_local:
    file: ./dev/auth_local.secret
```

Key points:
- `healthcheck` on the DB so `api` waits for it.
- Seed SQL mounts into the postgres init dir — fresh DB is populated on first `up`.
- Local-only secrets mounted via Docker secrets, not env vars. File is gitignored.
- Bind-mount code for hot reload in dev — see your language-specific patterns.

---

## Secrets for local dev

**Never** commit real production secrets. Never use them locally either.

### Pattern 1 — `.env.local.example` template

Commit `.env.local.example` with placeholders:

```
# .env.local.example — copy to .env.local on first clone
AUTH_JWT_SECRET=change-me-local-only
STRIPE_API_KEY=sk_test_local_placeholder
SENTRY_DSN=
FEATURE_FLAG_KEY=dev-key
```

`.env.local` is gitignored. On first run, `make bootstrap` copies `.env.local.example` → `.env.local` if missing.

### Pattern 2 — Shared dev bundle (team secrets manager)

For secrets where each dev needs the same non-prod value (sandbox API keys, test OAuth apps):

```bash
make fetch-dev-secrets   # pulls from 1Password / Vault / doppler into .env.local
```

Access is gated by SSO group membership. Revocation is one action when someone leaves.

### Never do
- Commit `.env` or `.env.local`.
- Share secrets via Slack DM, email, or screenshots.
- Reuse production keys in local dev.

---

## Seed data

A fresh `make up` should leave the app with:
- At least 3 test users with known passwords.
- One tenant / workspace / org entity.
- Representative domain data: a few orders, invoices, devices, whatever the domain produces.
- Admin + non-admin user for role testing.

Keep seed data in SQL files or fixtures in the repo at `dev/seed.sql` or `dev/fixtures/`. Real PII never appears in seed data.

---

## The "hello world" smoke test

Part of day 1. Confirms the whole loop works before the new engineer tries to change anything.

```makefile
# Makefile
.PHONY: up down smoke bootstrap

bootstrap:
	@test -f .env.local || cp .env.local.example .env.local
	mise install
	docker compose pull

up:
	docker compose up -d --wait

down:
	docker compose down -v

smoke:
	@curl -sf localhost:8080/healthz || (echo "healthz failed"; exit 1)
	@curl -sf -u dev@example.com:devpass localhost:8080/api/me | grep -q '"email"' \
		|| (echo "auth round-trip failed"; exit 1)
	@echo "smoke OK"
```

Day 1 command sequence:

```bash
git clone <repo> && cd <repo>
make bootstrap
make up
make smoke   # must print "smoke OK"
```

If any step fails, the onboarding doc has a bug — file a PR to fix it that afternoon, before moving on.

---

## Local dev smells (fix these before next hire arrives)

- Setup instructions involve "edit this file manually with your username".
- More than one command required to bring the stack up.
- Stack works only on Intel Macs but not ARM (or vice versa). Build multi-arch images.
- Tool versions in README drift from what people actually run. `.tool-versions` fixes this.
- "Just ask [one person] for the dev secret bundle" — automate `make fetch-dev-secrets` instead.
- Seed data assumes a manual step ("now log in and create a tenant"). Script it.

Every smell becomes a week-2-retro action item until it's fixed.
