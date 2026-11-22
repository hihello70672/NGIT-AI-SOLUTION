#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database}"
for migration in services/api/db/migrations/*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
if [ -n "${APP_DATABASE_URL:-}" ]; then
  psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/tests/test_schema.sql
else
  echo "APP_DATABASE_URL unset; migrations applied, tenant SQL checks skipped." >&2
fi
