# Local Docker environment

The root `compose.yaml` starts PostgreSQL 16 only. The API and web client are not containerized: follow their own READMEs for those development workflows. No migrations are automatically applied by the database container.

## Start

From the repository root:

```sh
cp .env.example .env
# Replace the example passwords and peppers with unique random local values.
docker compose config
docker compose up -d db
docker compose ps
```

The database uses a named volume (`ngit_postgres_data`) and a readiness check. The one-time init script creates a distinct `ngit_app` login but deliberately grants no schema or object privileges; do not use this login until reviewed, least-privilege grants and required migrations are applied. Migration execution should use a separately controlled migration principal. Init scripts run only when the volume is first initialized, so changing the role values after initialization does not rotate an existing role password.

The default host port is `5432`; set `POSTGRES_PORT` if it is occupied. The database is published only on the local Docker host binding configured by Compose. Do not expose this local setup to untrusted networks.

## Stop and data recovery

```sh
docker compose down
```

This stops containers and preserves the database volume. To intentionally remove local database data as well:

```sh
docker compose down -v
```

That removal is destructive. Back up any data needed before deleting the volume. This local Compose setup does not establish a production backup/recovery policy.

Never commit `.env` or production credentials. Environment variables are configuration inputs, not a production secrets-management solution. See the root README and `services/api/db/README.md` for API and migration setup. Compose lifecycle, migrations, grants, and row-level security must be executed and verified before claiming validation.
