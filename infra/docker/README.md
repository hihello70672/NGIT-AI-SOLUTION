# Local container infrastructure

The repository-root `compose.yaml` currently defines PostgreSQL for local development, with a persistent named volume and readiness health check. Start via `docker compose up -d db` and stop via `docker compose down`.

No API or web container is defined yet because those applications and their tooling have not been selected or implemented. Add services only alongside working application deliverables. Local example credentials are not suitable for production.
