-- Role assignment writes are privileged service operations; user-role RLS is self-read only.
INSERT INTO ngit.schema_migrations(version) VALUES ('0003_secure_role_assignments') ON CONFLICT DO NOTHING;
