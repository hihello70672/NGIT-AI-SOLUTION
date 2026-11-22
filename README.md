# NGIT AI SOLUTION

NGIT AI SOLUTION is a web-first, modular application built around a FastAPI backend, PostgreSQL system of record, and a React/TypeScript frontend in `apps/web`. The approved direction prioritizes backend-enforced security and user isolation, local/self-hosted AI runtime options, and optional external integrations.

## Scope and status

The web application is the only frontend in this milestone. NGIT-WINDOWS, NGIT-KALI, and NGIT-ANDROID are out of scope until the web/backend system is stable. The repository contains implementation for Phases 1–4, with integration/runtime validation outstanding as documented in [`docs/STATUS.md`](docs/STATUS.md). Status describes committed work, not verified test results; no test is claimed as passed unless run in the target environment. Later phase capabilities remain planned.

## Local PostgreSQL

Docker Compose currently provides the PostgreSQL development database and readiness check. Application container services are not declared as the implementation/build tooling is not yet selected.

1. Copy `.env.example` to `.env`; adjust local database values if needed. Values in the example are for local development only. Configure a unique `AUTH_TOKEN_PEPPER` before starting the API; see its comment and `services/api/README.md`.
2. Start the database: `docker compose up -d db`.
3. Check status: `docker compose ps`.
4. Stop: `docker compose down`. Add `-v` only if you intend to delete the named database volume.

The root Compose file publishes PostgreSQL on the configured host port for local development. Do not expose this setup publicly or reuse its example database password in production. Never commit `.env` or real credentials.

## API and web development

See [`services/api/README.md`](services/api/README.md) for API setup and test commands, and [`apps/web/README.md`](apps/web/README.md) for the frontend workflow. Database schema checks are documented in `services/api/db/tests/README.md` (if present) and the scripts under `services/api/db/tests/`; PostgreSQL-dependent checks require a disposable PostgreSQL instance.

## Architecture and contracts

- [Architecture and target repository layout](docs/ARCHITECTURE.md)
- [Module dependency map](docs/DEPENDENCY_MAP.md)
- [Phases 1–12](docs/PHASE_PLAN.md)
- [Phase ownership](docs/AGENT_ASSIGNMENTS.md)
- [Status and remaining verification](docs/STATUS.md)
- [Shared API/security/data protocols](docs/interfaces/SHARED_PROTOCOLS.md)
- [Brain](docs/interfaces/BRAIN.md), [Memory and knowledge](docs/interfaces/MEMORY.md), [Personal Agent](docs/interfaces/AGENT.md)

Shared contracts and module boundaries require Chief Architect approval. Open architecture decisions remain open until explicitly approved. External AI APIs are optional; never make the core Brain dependent solely on a third-party API.