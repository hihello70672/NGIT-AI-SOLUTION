# NGIT AI SOLUTION

NGIT is a modular, web-first AI ecosystem with a React/TypeScript/Vite client, FastAPI services, and PostgreSQL as the system of record. This milestone focuses on stabilizing the web/backend system. Windows, Kali, and Android adaptations are future projects and are outside this scope.

## Repository layout

```text
apps/web/             React, TypeScript and Vite frontend
services/api/         FastAPI application, feature modules, migrations and tests
docs/                 Architecture, dependencies, phases, assignments and status
docs/interfaces/      Shared protocols and Brain, Memory and Agent contracts
infra/docker/         Local Docker guidance
compose.yaml          PostgreSQL 16 local development service
.env.example          Local configuration template; contains examples, not secrets
```

Preserve existing modules, routes, schemas, migrations and tests. Modules own their persistence and use published typed contracts across boundaries. The web client consumes backend APIs and is not an authorization boundary. NGIT Brain must retain a local/self-hosted runtime path; external AI APIs are optional.

## Local PostgreSQL

Prerequisite: Docker with the Compose plugin. From the repository root:

```sh
cp .env.example .env
# Replace example passwords and peppers with unique locally generated values.
docker compose up -d db
docker compose ps
```

Compose currently starts PostgreSQL only; it does not containerize the API or web client. The database is published on localhost port 5432 by default and uses a named persistent volume. Stop it with `docker compose down`. Use `docker compose down -v` only when intentionally deleting local database data. Never commit `.env` or real credentials.

See [API setup](services/api/README.md), [database guidance](services/api/db/README.md), [web setup](apps/web/README.md), and [Docker guidance](infra/docker/README.md). Apply migrations and run tests using their documented instructions. No test-passing or release claim is made here; consult [status](docs/STATUS.md) for validation gaps. Create a test report only after executing tests and recording exact commands, environment, and results.

## Architecture and delivery plan

- [Architecture](docs/ARCHITECTURE.md)
- [Dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan](docs/PHASE_PLAN.md)
- [Agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md)
- [Agent](docs/interfaces/AGENT.md), [Brain](docs/interfaces/BRAIN.md), and [Memory](docs/interfaces/MEMORY.md) interfaces
- [Project status](docs/STATUS.md)

Shared-contract or module-boundary changes require Chief Architect review. Tests and runtime checks are not considered validated unless actually executed; no verified release or downloadable package is claimed.