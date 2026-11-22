# NGIT AI SOLUTION

NGIT is a web-first modular AI application built around a FastAPI backend, PostgreSQL system of record, and React/TypeScript/Vite frontend in `apps/web/`. This milestone has one frontend only. Windows, Kali, and Android clients are future adaptations and out of scope until the web/backend system is stable.

## Repository status and scope

The repository records implementation through phases 1–4. That implementation record is not runtime validation: tests, migrations, RLS, and Compose checks remain outstanding as detailed in [project status](docs/STATUS.md). Phases 5–12 are not started in the status record. Do not infer production readiness from source files or planned architecture.

NGIT Brain retains a local/self-hosted model-runtime path. External AI APIs are optional; core operation must not depend on them. The current root Docker Compose configuration runs PostgreSQL only, not API/web containers.

## Local PostgreSQL

Requirements: Docker Compose plugin. From the repository root:

```sh
cp .env.example .env
# Edit local values as needed; never commit .env or use example credentials in production.
docker compose up -d db
docker compose ps
# Stop without deleting database data:
docker compose down
# Destructive: remove the named database volume only when intended:
docker compose down -v
```

The Compose service is PostgreSQL 16 with a persistent named volume and readiness health check. `.env.example` contains development-only values, not production secrets. Database port is published for local development; do not expose this setup publicly. Compose lifecycle has not been verified for this update. Follow [local container guidance](infra/docker/README.md).

## API and web development

See [API setup](services/api/README.md) and [web setup](apps/web/README.md) for dependencies, configuration, and commands. Database migration instructions and schema checks are documented in `services/api/db/README.md` and `services/api/db/tests/README.md`. Use disposable PostgreSQL for integration tests. Before exposing Brain generation to untrusted callers, address the authorization gap documented in `docs/STATUS.md`.

## Architecture and contracts

- [Architecture](docs/ARCHITECTURE.md)
- [Dependency map](docs/DEPENDENCY_MAP.md)
- [Phase plan](docs/PHASE_PLAN.md)
- [Agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Status and validation gaps](docs/STATUS.md)
- Shared protocols: [common](docs/interfaces/SHARED_PROTOCOLS.md), [Agent](docs/interfaces/AGENT.md), [Brain](docs/interfaces/BRAIN.md), [Memory](docs/interfaces/MEMORY.md)

PostgreSQL is authoritative. Backend services derive caller context and enforce authorization/ownership; the frontend is not a security boundary. Module integrations use typed published contracts. Shared-contract and boundary changes require Chief Architect review. No test result is claimed here; see status for validation discipline and outstanding checks.

Never commit `.env`, credentials, tokens, or provider secrets. Use local environment configuration and keep credentials server-side.
