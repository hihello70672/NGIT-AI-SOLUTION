#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database}"
# Run as a migration principal with schema/table creation privileges. Configure
# APP_DATABASE_URL to test as the provisioned non-owner application role.
for migration in services/api/db/migrations/*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
if [ -n "${APP_DATABASE_URL:-}" ]; then
  psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/api/db/tests/test_schema.sql
else
  echo "APP_DATABASE_URL unset; migrations applied, tenant integration test skipped." >&2
fi
