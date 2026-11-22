# PostgreSQL schema checks

Use a fresh, disposable PostgreSQL 16+ database. Requires `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned application-role connection in `APP_DATABASE_URL`.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

Provision the test login independently: it must be a non-superuser, not a table owner, and not have `BYPASSRLS`. Grant `USAGE` on schema `ngit` and required DML on user tables, but no access to privileged roles/provider/audit data. `test_schema.sql` exercises policies as this role; it sets the transaction-local user context itself for disposable test purposes. Production application code must set `ngit.user_id` only from authenticated server context, never from client input. Migrations do not provision application login roles or grants.

The runner applies migrations in lexical order as migration principal, then runs rollback-only SQL assertions through the app connection. Assertions cover case-insensitive email uniqueness, role/check constraints, same-owner foreign keys, RLS owner-scoped reads and writes, billing seeds and defaults. Run only against disposable data; checked-in assertions do not establish execution or passing results.
