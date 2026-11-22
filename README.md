# NGIT AI SOLUTION

NGIT is a modular, web-first AI ecosystem with a FastAPI backend, PostgreSQL system of record, and React/TypeScript/Vite client in `apps/web/`. This milestone focuses on stabilizing the web/backend system. Windows, Kali, and Android clients are future adaptations outside this scope.

## Repository layout

```text
apps/web/                 React, TypeScript and Vite web client
services/api/             FastAPI application, feature modules and tests
services/api/db/           PostgreSQL migrations and database tests
docs/                      Architecture, plans, status and interface contracts
docs/interfaces/           Shared protocols, Agent, Brain and Memory contracts
infra/docker/              Local Docker guidance
compose.yaml                PostgreSQL 16 local development service
.env.example                Local development configuration template
```

Preserve existing modules, routes, schemas, migrations and tests. Cross-module consumers use published typed contracts; services own their persistence. The frontend calls backend APIs only and is not an authorization boundary. Credentials and secrets must never be committed.

## Local PostgreSQL

Prerequisite: Docker with the Compose plugin. From the repository root:

```sh
cp .env.example .env
# Replace the example passwords/peppers with unique locally generated values.
docker compose up -d db
docker compose ps
```

Compose currently starts **PostgreSQL only**; it does not containerize the API or web client. PostgreSQL is published on `localhost:5432` by default, with persistent data in the named `ngit_postgres_data` volume. Stop services without deleting data using:

```sh
docker compose down
```

Only use `docker compose down -v` when intentionally deleting the database volume. Apply migrations and run the database checks using the instructions in [`services/api/db/README.md`](services/api/db/README.md). RLS and tenant isolation checks require the documented non-owner, non-superuser application role without `BYPASSRLS`.

## API and web development

See [`services/api/README.md`](services/api/README.md) for Python dependencies, configuration, and API startup, and [`apps/web/README.md`](apps/web/README.md) for frontend setup and scripts. The web application consumes backend APIs; it must not connect directly to PostgreSQL. NGIT Brain retains a local/self-hosted runtime path; external AI APIs are optional.

## Architecture, status and validation

- [Architecture](docs/ARCHITECTURE.md)
- [Dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan](docs/PHASE_PLAN.md)
- [Agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md)
- [Agent](docs/interfaces/AGENT.md), [Brain](docs/interfaces/BRAIN.md), [Memory](docs/interfaces/MEMORY.md) interfaces
- [Current status and validation gaps](docs/STATUS.md)
- [Docker guidance](infra/docker/README.md)

The status record describes phases 1–3 as partly implemented, not fully validated. Test sources in the repository are not evidence that tests ran or passed. Migrations, RLS/grants, Compose lifecycle, API/web suites and builds, and end-to-end startup must be executed before claiming validation. No `docs/TEST_REPORT.md` should be added until tests have actually run, with exact commands, environment, and results. External AI is optional; do not place secrets in source control.
