# NGIT AI SOLUTION

NGIT is a modular, web-first AI ecosystem with a FastAPI backend, PostgreSQL system of record, and React/TypeScript/Vite web client at `apps/web/`. This milestone focuses on the web/backend system. Windows, Kali, and Android clients are future adaptations and are out of scope until the web system is stable.

## Repository layout

```text
apps/web/          React, TypeScript and Vite client
services/api/      FastAPI API, feature modules, database migrations and tests
docs/              Architecture, dependency, phase, status and shared-interface docs
infra/docker/      Local Docker guidance
compose.yaml       Local PostgreSQL service only
.env.example       Development configuration template
```

The layout describes current organization, not completion of every planned module. Preserve existing modules, routes, migrations and tests. Cross-module consumers use published typed contracts; services own their persistence. The frontend calls backend APIs and is not an authorization boundary. PostgreSQL is never accessed directly from browser code.

## Local PostgreSQL

Prerequisite: Docker with the Compose plugin. From the repository root:

```sh
cp .env.example .env
# Replace the example pepper values with locally generated random values before starting the API.
docker compose up -d db
docker compose ps
```

The checked-in Compose file starts PostgreSQL 16 only; it does not containerize the API or web client. By default the database is published on localhost port 5432. The named volume `ngit_postgres_data` persists database data. Stop without deleting data with `docker compose down`. `docker compose down -v` deletes the database volume and its data; use only when that is intentional.

Apply SQL migrations following the instructions in [`services/api/db/README.md`](services/api/db/README.md). There are five ordered migrations (`0001`–`0005`). Database initialization, grants/RLS, and Compose lifecycle have not been runtime-validated according to [`docs/STATUS.md`](docs/STATUS.md). Tenant isolation checks must use a non-owner, non-superuser application role without `BYPASSRLS`, not a superuser or table owner.

## API and web development

See [`services/api/README.md`](services/api/README.md) for Python dependencies, environment configuration and API startup, and [`apps/web/README.md`](apps/web/README.md) for frontend commands. The frontend consumes documented backend APIs. External AI APIs are optional; NGIT Brain retains a local/self-hosted runtime path. Keep secrets out of source control and use `.env.example` only as a template.

## Architecture, status and verification

- [Architecture](docs/ARCHITECTURE.md) and [dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan](docs/PHASE_PLAN.md) and [agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md), [Agent](docs/interfaces/AGENT.md), [Brain](docs/interfaces/BRAIN.md), and [Memory](docs/interfaces/MEMORY.md)
- [Current status and validation gaps](docs/STATUS.md)
- [Local Docker guidance](infra/docker/README.md)

The migration inventory was checked against actual files: exactly five SQL migration files, `0001` through `0005`. Checked-in tests are test sources only, not evidence they ran. No test pass, live database startup, release, or production readiness is claimed here. Run the documented suites and record exact commands, environment, and outcomes only after execution. `docs/TEST_REPORT.md` is intentionally absent until that work has occurred.
