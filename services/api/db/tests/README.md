# PostgreSQL schema checks

Run against a fresh, disposable PostgreSQL 16+ database using `psql` and a non-superuser role that does not own the `ngit` tables:

```sh
DATABASE_URL=postgresql://app_user:app_password@localhost:5432/ngit_test sh services/api/db/tests/run.sh
```

The runner applies every ordered migration and executes transactional schema/isolation checks. It verifies tenant-composite foreign keys, RLS filtering and write rejection, media/presentation inserts, reference seeds, and rollback of fixtures. Never point it at production or valuable data. The script is committed executable intent, but configure executable permission when checking out if required; run with `sh` as shown.
