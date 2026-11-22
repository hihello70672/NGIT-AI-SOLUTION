# NGIT AI SOLUTION v4.0

NGIT is a modular, web-first AI ecosystem: a React/TypeScript/Vite web client, FastAPI backend services, and PostgreSQL persistence. This milestone stabilizes the web/backend platform. NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID are future projects, not current deliverables.

The architecture supports local or self-hosted AI execution. External AI and provider APIs are optional integrations, never a required foundation. The web client is not an authorization boundary; security, ownership, billing, and policy decisions belong to backend services.

## Repository layout

```text
apps/web/                 React, TypeScript, Vite frontend; sole frontend
services/api/             FastAPI application, modules, database integration, tests
services/api/db/migrations/ Ordered PostgreSQL SQL migrations
services/api/db/tests/    Disposable-database isolation/schema checks
 docs/                    Architecture, dependency, ERD, phase, status, assignments
 docs/interfaces/         Shared and module interface contracts
infra/docker/             Local Compose and PostgreSQL guidance
compose.yaml              Local PostgreSQL service
.env.example              Local configuration template; replace examples locally
```

Preserve existing code and paths. Proposed domain subfolders are not a reason to create empty scaffolding. Each domain module owns its behavior, persistence/migrations, and tests, and publishes contracts to its consumers.

## Local PostgreSQL

Prerequisites: Docker Engine and the Compose plugin. From the repository root:

```sh
cp .env.example .env
# Set unique local passwords and pepper values in .env.
docker compose config
docker compose up -d db
docker compose ps
```

Compose starts PostgreSQL 16 only; API and frontend containers are not defined. The database has a readiness check and named volume. Ordered schema migrations are under `services/api/db/migrations/`; the Compose init script creates a separate app login but intentionally does not grant it schema access. Follow the database README to provision a disposable test database and carefully scoped migration/application roles. Do not use the privileged migration principal as the API login.

Stop while preserving data with `docker compose down`. To intentionally delete the local data volume, use `docker compose down -v` only after confirming data can be discarded. Detailed guidance: [Docker environment](infra/docker/README.md), [database](services/api/db/README.md), [API](services/api/README.md), [web](apps/web/README.md).

Never commit `.env`, credentials, or production secrets. Example values must be changed before use; environment lookup alone is not production secret management.

## Architecture and delivery

- [Architecture](docs/ARCHITECTURE.md)
- [Module dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan and verification gates](docs/PHASE_PLAN.md)
- [Agent ownership](docs/AGENT_ASSIGNMENTS.md)
- [ERD](docs/ERD.md)
- [Current implementation status and known caveats](docs/STATUS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md)

Tests, builds, migrations, database isolation, Compose lifecycle, and runtime checks are evidence only when actually run and recorded. Checked-in test sources do not establish passing results. Do not publish a test report or release claim without executing and recording the verification.
