# PostgreSQL schema checks

Use only a fresh, disposable PostgreSQL 16+ database. Requires `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned application-role connection in `APP_DATABASE_URL`.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The migration connection creates the isolated `ngit` schema and objects. The test application role must be a non-superuser and not own tables, must not have `BYPASSRLS`, and must receive schema usage plus only the fixture DML privileges required by the SQL assertions. Migrations intentionally do not create or grant application login roles. The script applies ordered SQL migrations as the migration principal, then runs rollback-only assertions through the application role.

Assertions cover case-insensitive email uniqueness, invalid message roles, nonnegative usage, same-owner conversation/message, video/source-asset and presentation/slide constraints, seed data, disabled local provider default, RLS owner-scoped reads and denied foreign-owner writes. Do not run tenant assertions as table owner or superuser. SQL files and checked-in assertions do not establish that execution occurred or passed; record actual commands and outcomes only after running them.
