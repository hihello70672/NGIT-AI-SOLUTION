# NGIT AI SOLUTION

NGIT AI SOLUTION is a web-first, modular application built around a FastAPI backend and PostgreSQL. This repository is at the Phase 1 foundation stage: architecture and local-development conventions are documented, while product modules remain planned rather than implemented.

## Scope

- `apps/web` is the sole frontend in this milestone. No Windows, Kali, or Android application is in scope.
- `services/api` is the planned modular FastAPI application. Module directories are added alongside real implementation rather than as empty placeholders.
- PostgreSQL is the planned system of record. Domain persistence and migrations will be introduced as features are implemented.
- External AI, search, browser, and payment integrations are optional adapters, not prerequisites for core startup.

## Local services

The Docker Compose configuration provides PostgreSQL and a database health check. The API service is intentionally not included yet: no application implementation or framework/tooling decisions beyond the approved architecture exist at this foundation stage.

1. Copy `.env.example` to `.env` and adjust the local database values if needed.
2. Start PostgreSQL with `docker compose up -d db`.
3. Stop it with `docker compose down`. Add `-v` only when you intend to delete the local database volume.

Do not commit `.env` or credentials. Compose database credentials are development-only values, not production secrets.

## Architecture and contracts

- [Architecture](docs/ARCHITECTURE.md)
- [Dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan](docs/PHASE_PLAN.md)
- [Agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Shared API, error, event, and service conventions](docs/interfaces/SHARED_PROTOCOLS.md)

Open decisions are recorded in the architecture document; this repository does not silently select tools that the approved plan leaves open.
