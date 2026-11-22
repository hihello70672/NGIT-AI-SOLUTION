# Database

Phase 1 uses ordered plain SQL migrations under `migrations/` and SQL integration assertions under `tests/`, without an ORM. The schema is isolated in `ngit`; migrations include users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation records, audit events, indexes and forced RLS. PostgreSQL 16+ is the target; migration 0005 uses composite-FK column-specific `ON DELETE SET NULL` supported by PostgreSQL 15+.

Run only against a fresh disposable database:

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

`DATABASE_URL` is a migration principal allowed to create the schema and objects. `APP_DATABASE_URL` is a separately provisioned non-superuser, non-owner role without `BYPASSRLS`, with schema usage and required test fixture privileges; the runner applies migrations through the former and executes tenant checks through the latter. The SQL checks roll fixture rows back. Do not use production or valuable data.

Trusted API transactions set `ngit.user_id` only from authenticated server context, never client input. Provider config stores opaque credential references, not credentials. External AI is optional. Role grants, audit logs, provider metadata, and billing reference plans are privileged service data, not tenant-readable. No migrations or tests are claimed as run until actually executed and recorded.
