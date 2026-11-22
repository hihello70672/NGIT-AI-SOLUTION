# Database

The migration-tooling decision remains open. Phase 1 uses ordered PostgreSQL SQL migrations under `migrations/` and SQL integration checks under `tests/`; no ORM is introduced. Apply all migrations lexically to a fresh PostgreSQL 16+ database. Migration 0004 completes domain tables missing from early 0001 versions and preserves existing installations; all migrations are idempotent where practical.

For local development, start PostgreSQL with `docker compose up -d db` from the repository root (copy `.env.example` to `.env` first). Apply migrations and run checks against a disposable database:

```sh
for migration in services/api/db/migrations/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"; done
DATABASE_URL=postgresql://app_user:app_password@localhost:5432/ngit_test sh services/api/db/tests/run.sh
```

The application role must be a non-superuser and must not own protected tables; `FORCE ROW LEVEL SECURITY` alone cannot constrain superusers. API code sets `ngit.user_id` transaction-locally from authenticated server context, never client input. Provider configurations store opaque secret-manager references, not credentials. External AI integrations are optional.

The existing baseline migration is preserved; review its historical source before production acceptance. See [ERD](../../../docs/ERD.md) and [test instructions](tests/README.md).
