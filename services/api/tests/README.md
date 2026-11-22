# API tests

From repository root, install `services/api/requirements.txt`, then run `PYTHONPATH=. pytest services/api/tests`. The API tests isolate the user service at the boundary and do not require PostgreSQL; database migrations and RLS are verified separately using `services/api/db/tests/run.sh` against a disposable PostgreSQL instance.
