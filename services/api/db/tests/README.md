# PostgreSQL schema checks

Use a fresh disposable PostgreSQL 16+ database. Requires `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned app-role connection in `APP_DATABASE_URL`.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The migration principal owns the schema and migration objects. The test login must be non-superuser, not a table owner, and not have `BYPASSRLS`. Provision only schema usage and disposable fixture DML grants needed by the SQL checks; do not expose privileged role/provider/audit records. The SQL suite is intended only for a newly created disposable DB, writes test identities and rolls back test fixtures. Configure server-side `ngit.user_id` from authenticated identity in production; the test sets it directly to test policy behavior. Migration SQL does not create app login roles or grants.

Assertions cover migration-created objects, seed defaults, case-insensitive email, constraints, tenant ownership foreign keys and RLS reads/writes. Checked-in assertions do not establish that tests ran or passed.
