# PostgreSQL schema checks

Run these checks against a disposable PostgreSQL 16+ database with `psql` installed. The runner applies the schema migration, reference seed, and transactional SQL checks:

```sh
DATABASE_URL=postgresql://user:password@localhost:5432/ngit_test sh services/api/db/tests/run.sh
```

Use a fresh empty database. The migration creates the isolated `ngit` schema and enables/forces RLS on user-owned tables. The test checks cross-owner foreign-key rejection, owner-filtered RLS reads and writes, reference seed rows, and verifies all fixtures are rolled back. Never point it at a production or valued database. These checks require PostgreSQL; they are not reported as executed by this documentation.
