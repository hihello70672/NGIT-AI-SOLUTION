# PostgreSQL schema checks

Use a fresh disposable PostgreSQL 16+ database. Never point this test at production or valuable data. Required tools are `psql` and a working `DATABASE_URL` connection.

The ordered migration runner must execute as a migration principal allowed to create the `ngit` schema and its objects. That principal is not the tenant application role. For meaningful RLS checks, separately provision a non-superuser, non-table-owner role without `BYPASSRLS`, grant only the schema/table privileges needed by application queries, and execute the tenant isolation assertions as that role. The migrations do not create or grant privileges to an application role automatically; do not use a table owner or superuser as the tenant request identity.

From the repository root:

```sh
# Against a fresh, disposable database; migration principal must own/create schema objects.
DATABASE_URL=postgresql://migration_user:migration_password@localhost:5432/ngit_test \
  sh services/api/db/tests/run.sh
```

The runner applies ordered migrations then executes transactional integration checks for tenant-composite foreign keys, user-scoped RLS read/write behavior, billing/provider seeds, and media/video/presentation records. Fixture rows roll back. The included runner performs both migration and test execution using the same URL; to validate RLS under a separately provisioned non-owner role, apply migrations as the migration principal first, then run `psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/tests/test_schema.sql` with the application-role URL and ensure the role has the required table privileges. The test script's fixture inserts also need appropriate fixture privileges; if the production-like application role is deliberately read/write-limited, use a dedicated non-owner test role with the same lack of ownership and `BYPASSRLS`, granting fixture DML only on the disposable test database.

Run only against a newly created disposable database: migrations use `IF NOT EXISTS` for objects and are not a general-purpose schema drift repair tool. This document describes checks and commands; it does not claim they have been executed or passed.
