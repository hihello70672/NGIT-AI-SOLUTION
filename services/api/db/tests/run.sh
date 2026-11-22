#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database}"
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
for migration in "$root"/db/migrations/*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
if [ -z "${APP_DATABASE_URL:-}" ]; then
  echo "APP_DATABASE_URL unset; migrations applied, application-role isolation tests skipped." >&2
  exit 0
fi
psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$root/db/tests/test_schema.sql"
psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$root/db/tests/test_phase1.sql"
