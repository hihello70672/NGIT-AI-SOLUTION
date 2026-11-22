# NGIT AI SOLUTION

NGIT is a web-first modular AI application built around a FastAPI backend, PostgreSQL system of record, and React/TypeScript frontend in `apps/web`. This milestone has one frontend; NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID are out of scope until the web/backend system is stable.

## Scope and status

The repository includes implementation for early phases, but committed code and documentation are not proof of runtime behavior. See [project status](docs/STATUS.md) for recorded evidence and outstanding validation. Do not claim tests, migrations, RLS, or Compose lifecycle checks passed unless they were actually run. Later phase capabilities remain planned until implemented and validated.

## Local PostgreSQL

Docker Compose currently defines PostgreSQL for local development. The API and web containers are not included in Compose because their application/container build tooling has not been selected for this setup.

1. Copy `.env.example` to `.env` and change local database values if needed. Configure a unique `AUTH_TOKEN_PEPPER` before starting the API; see [API setup](services/api/README.md). Example values are for local development only.
2. Start PostgreSQL: `docker compose up -d db`.
3. Check service status: `docker compose ps`.
4. Stop PostgreSQL: `docker compose down`. Add `-v` only if you intend to delete the named database volume.

The database port is published for local development. Do not expose this setup publicly or reuse its example password in production. Never commit `.env` or real credentials.

## API and web development

See [API instructions](services/api/README.md) and [web instructions](apps/web/README.md) for their setup and test commands. Database schema checks are documented in `services/api/db/tests/README.md`; PostgreSQL-dependent checks require a disposable database.

## Architecture and contracts

- [Architecture and repository target](docs/ARCHITECTURE.md)
- [Module dependency map](docs/DEPENDENCY_MAP.md)
- [Phased delivery plan](docs/PHASE_PLAN.md)
- [Agent assignments](docs/AGENT_ASSIGNMENTS.md)
- [Status and validation gaps](docs/STATUS.md)
- [Shared protocols](docs/interfaces/SHARED_PROTOCOLS.md)
- [Agent](docs/interfaces/AGENT.md), [Brain](docs/interfaces/BRAIN.md), and [Memory](docs/interfaces/MEMORY.md) contracts
- [Local container guidance](infra/docker/README.md)

Domain modules share one FastAPI application and PostgreSQL initially, with distinct ownership and typed service boundaries. User ownership is derived from authenticated server context; frontend checks are never authoritative. Keep a local/self-hosted Brain runtime path available. External AI APIs are optional. Do not add a broker, distributed services, vector persistence, or unapproved integrations by assumption.

Shared contracts and module boundaries require Chief Architect review. Preserve existing working paths and review the interface documents before extending them. Open decisions and runtime caveats remain documented; this repository does not assert production readiness.
