# NGIT AI SOLUTION v4.0

NGIT is a modular, web-first AI ecosystem: a React/TypeScript/Vite web client, FastAPI backend services, and PostgreSQL persistence. This milestone focuses on stabilizing the web/backend system. NGIT-WINDOWS, NGIT-KALI and NGIT-ANDROID are future projects outside this scope.

The architecture supports local or self-hosted AI operation. External AI/provider APIs are optional and are not a required foundation. The web client is not an authorization boundary: backend services own security, identity, data ownership, billing and policy decisions.

## Repository layout

```text
apps/web/                 React, TypeScript, Vite frontend; sole frontend
services/api/             FastAPI application, modules, DB integration, tests
services/api/db/migrations/ Ordered PostgreSQL SQL migrations
services/api/db/tests/    Disposable-database schema/isolation checks
 docs/                    Architecture, dependency, ERD, phase, status, ownership
 docs/interfaces/         Shared protocols and module contracts
infra/docker/             Local Compose and PostgreSQL guidance
compose.yaml              Local PostgreSQL service
.env.example              Local configuration template; not credentials
```

Preserve existing module paths and implementation. Each domain module owns behavior, persistence/migrations and tests, and publishes contracts to consumers. Do not add empty scaffolding to imitate a target sketch.

## Local PostgreSQL

Prerequisites: Docker Engine and the Compose plugin. From repository root:

```sh
cp .env.example .env
# Replace sample passwords and peppers with unique local random values.
docker compose config
docker compose up -d db
docker compose ps
```

Compose starts PostgreSQL 16 only; API and frontend containers are not defined. The database has a readiness health check and named volume. Ordered SQL migrations are in `services/api/db/migrations/`. The Compose bootstrap creates a distinct app login without schema/object privileges; provision reviewed, least-privilege grants before using it. Follow the database README for disposable DB tests and migration/application role guidance.

Stop with `docker compose down` to preserve database data. `docker compose down -v` deletes the volume and is destructive. See [Docker operations](infra/docker/README.md), [database](services/api/db/README.md), [API](services/api/README.md) and [web](apps/web/README.md).

Never commit `.env`, credentials or production secrets. Example values must be replaced; environment lookup alone is not production secret management.

## Architecture and delivery

- [Architecture](docs/ARCHITECTURE.md)
- [Module dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan and integration gates](docs/PHASE_PLAN.md)
- [Agent ownership](docs/AGENT_ASSIGNMENTS.md)
- [ERD](docs/ERD.md)
- [Current status and known caveats](docs/STATUS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md)

Tests, builds, migrations, database isolation, Compose lifecycle and runtime checks count as evidence only when actually run and recorded. Checked-in tests are not evidence of passing results. Do not publish a test report or release claim without executing and documenting the checks.
