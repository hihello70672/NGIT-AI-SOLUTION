-- Role assignment writes remain privileged service operations. User-role RLS is self-read only.
SET search_path TO ngit, public;
INSERT INTO ngit.schema_migrations(version) VALUES ('0003_secure_role_assignments') ON CONFLICT DO NOTHING;
