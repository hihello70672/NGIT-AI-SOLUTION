#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to a disposable PostgreSQL database}"
root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
for migration in "$root"/db/migrations/*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
if [ -n "${APP_DATABASE_URL:-}" ]; then
  psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$root/db/tests/test_schema.sql"
else
  echo "APP_DATABASE_URL unset; migrations applied, tenant SQL checks skipped." >&2
fi
