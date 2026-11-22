# Database

Migration tooling remains an open architecture decision. Phase 1 uses ordered PostgreSQL SQL files under `migrations/` and SQL integration checks under `tests/`, without introducing an ORM. Apply all migrations lexically to fresh PostgreSQL 16+. The baseline and follow-up migrations preserve the existing schema while completing missing billing, provider, media, video and presentation tables.

Local PostgreSQL: from repository root copy `.env.example` to `.env`, then run `docker compose up -d db`. Apply migrations and checks to a disposable database:

```sh
for migration in services/api/db/migrations/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"; done
DATABASE_URL=postgresql://app_user:app_password@localhost:5432/ngit_test sh services/api/db/tests/run.sh
```

Use a non-superuser application role that does not own protected tables. API code must set `ngit.user_id` transaction-locally from authenticated server context, never client input. Provider configuration stores opaque references, not secret values. External AI remains optional. Runtime migrations and tests have not been executed in this task.

See [ERD](../../../docs/ERD.md) and [test instructions](tests/README.md).
