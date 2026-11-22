# PostgreSQL schema checks

Use a fresh, disposable PostgreSQL 16+ database. `DATABASE_URL` must be a
migration principal that can create the isolated `ngit` schema and its objects.
`APP_DATABASE_URL` must identify a separately provisioned non-owner,
non-superuser role without `BYPASSRLS`, with the schema/table grants needed by
the application and these tests.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The runner applies migrations lexically, then runs the existing admin-policy
checks and `test_phase1.sql` as the application principal. The latter verifies
required domain tables, seeded roles/provider metadata, tenant-scoped reads and
the composite message/conversation ownership constraint. An unset application
URL is explicitly a migration-only run; it does not verify RLS. Never point the
suite at production or valuable data. No credentials or secret values belong
in this repository. Checks are not evidence of execution until run and recorded.
