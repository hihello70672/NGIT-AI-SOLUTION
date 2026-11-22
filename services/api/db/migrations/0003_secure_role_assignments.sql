-- Compatibility marker retained for ordered migration history. User-role RLS
-- is established in 0001; role grants remain privileged service operations.
SET search_path TO ngit, public;
INSERT INTO schema_migrations(version) VALUES ('0003_secure_role_assignments') ON CONFLICT DO NOTHING;
