-- Compatibility marker; tenant policy is established by migration 0001.
SET search_path TO ngit,public;
INSERT INTO schema_migrations(version) VALUES('0003_secure_role_assignments') ON CONFLICT(version) DO NOTHING;
