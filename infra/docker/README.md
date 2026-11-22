# Local Docker environment

The repository-root `compose.yaml` currently defines a PostgreSQL 16 service only. It includes a named persistent volume and a readiness health check; API and frontend containers are not defined.

From the repository root, prepare local configuration and start the database:

```sh
cp .env.example .env
# Replace example passwords/peppers with unique locally generated values.
docker compose up -d db
docker compose ps
docker compose down
```

PostgreSQL is exposed on `localhost:${POSTGRES_PORT:-5432}`. `docker compose down` preserves the named data volume. Use `docker compose down -v` only when intentionally deleting local database data. Do not commit `.env` or production credentials; environment lookup alone is not a production secret-management solution.

The API/web services should only be added to Compose alongside working containerization and verified startup instructions. See the root README, API/database READMEs, and the phase/status documents for outstanding migration, grants/RLS, application startup, and test validation.
