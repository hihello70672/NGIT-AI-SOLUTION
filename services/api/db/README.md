# Database

Phase 1 uses ordered plain SQL migrations under `migrations/` and SQL integration assertions under `tests/`, without introducing an ORM. Apply lexically ordered migrations to fresh PostgreSQL 16+. The schema includes the isolated `ngit` namespace, domain tables, RLS, indexes and seed reference data in migration 0002. Migration principal must own/create schema objects; tenant application role must not own tables, be superuser, or have `BYPASSRLS`.

From repository root, against a fresh disposable database:

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The runner applies SQL migrations as `DATABASE_URL`, then executes integration assertions as `APP_DATABASE_URL` if set. Provision the latter separately as a non-superuser, non-owner role without `BYPASSRLS`, with schema usage and needed test fixture DML privileges. Do not run tenant isolation assertions as a table owner or superuser. Migrations do not provision or grant application-role privileges.

Trusted API code sets transaction-local `ngit.user_id` only from authenticated server context, never client input. Provider configuration holds opaque credential references, not secret values. External AI is optional. Audit logs and reference/provider configuration are privileged service data, not tenant-readable.

SQL checks cover owner-scoped RLS, cross-owner composite foreign keys, seeds, uniqueness/check constraints, and billing/media/presentation relationships; fixtures roll back. No migration or test execution is claimed unless recorded after actually running.
