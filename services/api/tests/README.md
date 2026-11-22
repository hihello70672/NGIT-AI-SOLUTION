# API tests

From repository root, install `services/api/requirements.txt` and run:

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

The HTTP and security tests use in-memory test repositories where appropriate. `test_api_integration.py` skips unless `NGIT_TEST_DATABASE_URL` is set. For that test, use a disposable database with all SQL migrations applied and a dedicated application role that is a non-owner, non-superuser and does not have `BYPASSRLS`. The test creates uniquely named records and exercises database-backed registration, login, profile access/update, logout, and default-role persistence. Do not point it at production or shared data.

Database-level tenant/RLS assertions are separate; see `services/api/db/tests/README.md`. Test sources are not evidence that tests have been executed.
