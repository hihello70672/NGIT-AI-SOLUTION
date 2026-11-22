-- Local bootstrap for a distinct, non-privileged application login.
-- Init scripts run only when PostgreSQL initializes a fresh data directory.
-- Migrations and deployment provisioning must explicitly grant reviewed,
-- least-privilege access; this role intentionally receives no schema access.
\set ON_ERROR_STOP on

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'ngit_app_user', :'ngit_app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'ngit_app_user')\gexec
