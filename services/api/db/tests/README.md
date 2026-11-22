# PostgreSQL schema checks

Use a fresh disposable PostgreSQL 16+ database only. Required: `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned test application role connection in `APP_DATABASE_URL`.

The migration principal must create the `ngit` schema and schema objects. The assertion role must be a non-superuser, non-table-owner without `BYPASSRLS`; grant required schema usage and fixture DML only on the disposable test database. Migrations do not provision/grant application-role privileges.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The script runs ordered migrations as the migration principal, then transactional SQL assertions as the test application role. Checks cover case-insensitive email uniqueness, invalid message role and negative usage rejection, conversation/message/video/presentation tenant constraints, owner-scoped RLS reads/writes, reference data and disabled local provider. Fixture records roll back. Never run tenant checks as table owner or superuser. This document and checked-in assertions do not claim execution or passing tests.
