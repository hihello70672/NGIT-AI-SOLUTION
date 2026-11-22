# Local container infrastructure

The repository-root `compose.yaml` currently defines PostgreSQL for local development, with a persistent named volume and readiness health check. Start with `docker compose up -d db`; inspect with `docker compose ps`; stop with `docker compose down`. Add `-v` only when intentionally deleting the named database volume.

The Compose file does not define API or web containers. Add application services only alongside working application/container deliverables and verified commands; do not imply they exist or are validated. Copy `.env.example` to `.env` for local configuration, use unique credentials outside the example, and never commit `.env` or expose the development database publicly. Compose lifecycle and database behavior still require runtime validation.

See the root [README](../../README.md), [API setup](../../services/api/README.md), and [database check instructions](../../services/api/db/tests/README.md).
