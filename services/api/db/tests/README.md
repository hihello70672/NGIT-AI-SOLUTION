# PostgreSQL schema checks

Use a fresh disposable PostgreSQL 16+ database. Requires `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned app-role connection in `APP_DATABASE_URL`.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The migration principal owns schema/migration objects. The test login must be non-superuser, not a table owner, and lack `BYPASSRLS`. For a disposable database, grant schema `USAGE`, select on role/plan/provider reference rows, and fixture DML on `users` and user-owned tables (including sequences only if any are added). Do not grant access to privileged provider or audit data beyond the tested disabled provider reference lookup. Assertions insert two temporary test identities, set their transaction-local `ngit.user_id` values in turn, and roll back all fixtures. Production code sets this value only from authenticated server identity. Migrations do not provision application login roles or grants.

Checks cover email normalization uniqueness, database constraints, owner-scoped RLS, selected seed defaults, and indexes/tenant FK behavior through normal SQL usage. Use only disposable data; checked-in assertions do not prove execution or passing results.
