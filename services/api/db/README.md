# Database

The database migration tooling decision remains open in the architecture plan. Phase 1 provides ordered PostgreSQL SQL migrations in `migrations/` and SQL integration checks in `tests/`; it does not introduce an ORM or migration framework.

For local development, start PostgreSQL with `docker compose up -d db` from the repository root (copy `.env.example` to `.env` first). Apply the SQL files to a fresh database in lexical order:

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/migrations/0001_initial_schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/migrations/0002_seed_reference_data.sql
```

Run `DATABASE_URL=... sh services/api/db/tests/run.sh` against a disposable empty database. The checks require `psql` and PostgreSQL. Set `ngit.user_id` transaction-locally from trusted authenticated server context before accessing RLS-protected tables. Never accept ownership context from client input. The application connection must be non-superuser and not own the protected tables.

Do not place provider credentials in PostgreSQL or source control. `provider_configs.credential_ref` is only an opaque reference; external AI providers remain optional.
