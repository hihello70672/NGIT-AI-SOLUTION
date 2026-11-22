# PostgreSQL schema checks

Use only a fresh, disposable PostgreSQL 16+ database, never production or valuable data. Required tools: `psql` and a valid `DATABASE_URL`.

Migrations must execute as a migration principal allowed to create the `ngit` schema and its objects. The integration SQL must execute using a separately provisioned non-superuser, non-table-owner application-equivalent role without `BYPASSRLS`, with necessary schema and fixture DML privileges. Migrations do not create or grant privileges to an application role.

From repository root:

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The runner applies migrations in lexical order and executes SQL assertions through `APP_DATABASE_URL` when supplied. Assertions verify case-insensitive email uniqueness, role/usage checks, tenant composite FK constraints for conversations/messages and media/video/presentation relationships, RLS-scoped reads/writes, reference seeds and a default-disabled local provider; test fixtures roll back.

Grant only privileges needed by the test role on this disposable database. Production-like roles should not receive fixture-wide DML privileges merely for these tests. Do not use table owner or superuser for tenant RLS checks. No test execution or passing result is implied by these sources or commands.
