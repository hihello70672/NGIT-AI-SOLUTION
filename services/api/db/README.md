# Database

Phase 1 uses ordered plain SQL migrations under `migrations/` and SQL integration assertions under `tests/`, without introducing an ORM. Apply lexically ordered migrations to fresh PostgreSQL 16+ (composite-FK column-specific `SET NULL` requires PostgreSQL 15+). Migrations create the isolated `ngit` schema, domain tables, RLS and indexes. Reference data is seeded by migration 0002. Migration principal must own/create the schema objects; tenant application role must not own tables, be superuser, or have `BYPASSRLS`.

From repository root, against a fresh disposable database:

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

To execute tenant integration assertions, provision a distinct non-superuser/non-owner application role with schema usage, required table DML, and fixture DML on the disposable test database, then set `APP_DATABASE_URL` to its connection. Do not grant `BYPASSRLS`; the role needs INSERT/SELECT privileges on test fixture tables. The runner applies migrations as `DATABASE_URL`, then executes test SQL as `APP_DATABASE_URL`.

Use transaction-local `ngit.user_id` set only by trusted API code from authenticated server context, never client input. Provider configuration holds opaque credential references, not secret values. External AI is optional. RLS is a database defense-in-depth boundary; audit logs and reference/provider configuration are privileged service data and are not tenant-readable.

The SQL tests assert cross-owner composite-FK rejection, RLS visibility and write isolation, seed presence, uniqueness/check constraints and billing/media/presentation relationships, rolling back fixture rows. No migration or test execution is claimed unless recorded in project status after it actually runs.
