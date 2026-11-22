# PostgreSQL schema checks

Use a fresh, disposable PostgreSQL 16+ database. Requires `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned application-role connection in `APP_DATABASE_URL`.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

Provision the test login independently: it must be a non-superuser, not a table owner, and not have `BYPASSRLS`. Grant schema `USAGE` and the needed fixture DML privileges on user tables, but no access to privileged roles/provider/audit data. The assertions first create user fixtures with no user context, then use transaction-local `ngit.user_id` for each owner's records and verify an explicit foreign-owner write is denied. This context setup exists only for disposable tests. Production application code sets `ngit.user_id` only from authenticated server context, never client input. Migrations do not provision application login roles or grants.

The runner applies migrations in lexical order as migration principal, then executes rollback-only SQL assertions through the app connection. Tests cover case-insensitive email uniqueness, database checks, same-tenant foreign keys, RLS owner-scoped records, billing/reference seeds and optional-provider defaults. Run only against disposable data; checked-in assertions do not establish execution or passing results.
