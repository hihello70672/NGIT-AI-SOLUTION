-- Local bootstrap for the distinct application login. Init scripts run only
-- when the PostgreSQL data directory is first initialized. The role is
-- intentionally not granted schema/table access here: reviewed migrations and
-- deployment-specific grants must provision the least privileges required.
\set ON_ERROR_STOP on

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'ngit_app_user', :'ngit_app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'ngit_app_user')\gexec
