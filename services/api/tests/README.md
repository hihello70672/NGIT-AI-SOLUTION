# API tests

From the repository root, install `services/api/requirements.txt`, then run:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

The API/security unit tests do not require PostgreSQL. Database migrations and RLS behavior require disposable PostgreSQL and are tested separately with `services/api/db/tests/run.sh`. Tests are not claimed as passing unless actually executed. Security token, approval, audit, and emergency-stop state is process-local; this implementation is not suitable for multi-worker production without approved shared persistence.
