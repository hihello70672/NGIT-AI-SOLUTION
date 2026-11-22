#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database}"
# The initializer is intended for an empty database; use a fresh disposable DB per run.
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/migrations/0001_initial_schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/migrations/0002_seed_reference_data.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/tests/test_schema.sql
