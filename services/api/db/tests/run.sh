#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database}"
# Use a new disposable database. Migrations are intentionally forward-only.
for migration in services/api/db/migrations/*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/tests/test_schema.sql
