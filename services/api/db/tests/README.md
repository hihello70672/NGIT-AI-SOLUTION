# PostgreSQL schema checks

Use a fresh disposable PostgreSQL 16+ database and a non-superuser role that does not own protected tables. From repository root:

```sh
DATABASE_URL=postgresql://app_user:app_password@localhost:5432/ngit_test sh services/api/db/tests/run.sh
```

The runner applies ordered migrations and executes transactional integration checks for tenant-composite foreign keys, RLS read/write isolation, billing/provider seeds, and media/video/presentation records. Fixtures roll back. Do not use production or valuable data. This document describes checks; it does not claim they have been executed.
