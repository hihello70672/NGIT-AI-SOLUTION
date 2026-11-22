# PostgreSQL schema checks

Use a fresh disposable PostgreSQL 16+ database. Requires `psql`, migration credentials in `DATABASE_URL`, and a separately provisioned app-role connection in `APP_DATABASE_URL`.

```sh
export DATABASE_URL='postgresql://migration_user:password@localhost:5432/ngit_test'
export APP_DATABASE_URL='postgresql://ngit_test_app:password@localhost:5432/ngit_test'
sh services/api/db/tests/run.sh
```

The migration principal owns schema and migration objects. The test login must be non-superuser, not a table owner, and lack `BYPASSRLS`. Provision `USAGE` on schema `ngit`, SELECT on reference rows, and fixture DML for `users` and user-owned tables. Admin-table RLS checks require the role to be granted SELECT/INSERT on `admin_rules` and `service_controls`, while the non-admin identity must have the same grants to prove RLS denies access (not merely SQL grants). Do not grant access to privileged provider or audit data beyond test needs. Assertions insert temporary identities and roll fixtures back.

Checks cover existing owner scope plus admin-table read/write isolation, using the test SQL in `test_schema.sql`. Checked-in assertions do not prove tests were executed or passed.

Migration `0006_admin_control.sql` also creates owner-only SELECT/INSERT policies for `ngit.users`, which are necessary for administrator user listings and account changes when the API connects as the authenticated non-owner role. Role grants remain deployment provisioning work.
