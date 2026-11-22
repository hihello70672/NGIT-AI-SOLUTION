# Local Docker environment

The root `compose.yaml` starts PostgreSQL 16 only. API and web containers are not defined; follow their own READMEs for development setup. The database container does not automatically apply schema migrations.

## Start

From repository root:

```sh
cp .env.example .env
# Replace example passwords and peppers with unique random local values.
docker compose config
docker compose up -d db
docker compose ps
```

Compose uses a named persistent volume (`ngit_postgres_data`) and a readiness check. A first-initialization SQL script creates the separate `NGIT_APP_USER` login using `NGIT_APP_PASSWORD`. It grants no schema/table access: provision reviewed least-privilege database grants before using the login. Use a separately controlled migration principal to apply the ordered migrations. Docker init scripts run only when the data directory is first initialized; updating role variables later does not rotate an existing database role's password.

The default published host port is 5432; set `POSTGRES_PORT` if occupied. Do not expose this local database setup to untrusted networks.

## Stop and recovery

```sh
docker compose down
```

This stops containers and preserves the named volume. To deliberately delete local database data, use `docker compose down -v` only after confirming the data is disposable. This Compose setup does not define production backup/recovery policy; take a suitable backup before destructive operations.

Never commit `.env` or real credentials. Environment variables are configuration, not production secrets management. See root README, `services/api/README.md`, and `services/api/db/README.md`. Migrations, role grants, RLS/isolation, and Compose lifecycle require actual execution and verification before validation claims.
