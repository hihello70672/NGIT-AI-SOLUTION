# NGIT AI SOLUTION

NGIT is a modular, web-first AI ecosystem with a FastAPI backend, PostgreSQL system of record, and React/TypeScript/Vite web client in `apps/web/`. This milestone focuses on the web application and backend. Windows, Kali, and Android clients are future adaptations and are out of scope until the web/backend system is stable.

## Repository map

```text
apps/web/                  React, TypeScript, Vite frontend
services/api/              FastAPI backend, modules, database migrations and tests
infra/docker/              Local Docker guidance
docs/                      Architecture, dependencies, phases, status and shared interfaces
compose.yaml               Local PostgreSQL Compose service
.env.example               Development configuration template
```

The paths above describe the repository organization, not completion of every planned module. See [project status](docs/STATUS.md), [architecture](docs/ARCHITECTURE.md), and [phase plan](docs/PHASE_PLAN.md) for evidence and open validation work.

## Local PostgreSQL

Prerequisite: Docker with the Compose plugin. From the repository root:

```sh
cp .env.example .env
# Replace example pepper values with locally generated random values before starting the API.
docker compose up -d db
docker compose ps
```

The root Compose file currently runs PostgreSQL 16 only; it does not containerize the API or web client. Database data is held in a named volume. Stop without deleting it using `docker compose down`. `docker compose down -v` deletes the named database volume and its data; use only when that is intended. Follow [local Docker guidance](infra/docker/README.md) and the database migration instructions in `services/api/db/README.md`. Compose lifecycle and migrations are not claimed as validated here.

## API and web development

See [API setup](services/api/README.md) for Python dependencies, configuration, and startup, and [web setup](apps/web/README.md) for frontend commands. The frontend calls documented backend APIs and never connects directly to PostgreSQL. Authorization is enforced by backend services, not the UI.

NGIT Brain must retain a local or self-hosted runtime path. External AI APIs are optional. Keep credentials and secrets server-side; never commit `.env` or real credentials. Checked-in test sources do not indicate that tests ran. Record exact commands and outcomes when performing validation.

## Architecture and contracts

- [Architecture](docs/ARCHITECTURE.md)
- [Dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan](docs/PHASE_PLAN.md)
- [Agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Status and validation gaps](docs/STATUS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md), [Agent](docs/interfaces/AGENT.md), [Brain](docs/interfaces/BRAIN.md), and [Memory](docs/interfaces/MEMORY.md) contracts

Preserve existing routes, modules, migrations, and tests. Module consumers use published contracts, not private internals or another module's tables. Shared contract and boundary changes require Chief Architect review.
