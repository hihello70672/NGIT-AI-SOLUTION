-- Compatibility migration: the current initial schema already enforces grants RLS.
SET search_path TO ngit,public;
DO $migration$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='ngit' AND tablename='user_roles' AND policyname='user_isolation') THEN
  ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
  ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;
  CREATE POLICY user_isolation ON user_roles USING (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid) WITH CHECK (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid);
 END IF;
END $migration$;
INSERT INTO schema_migrations(version) VALUES('0003_secure_role_assignments') ON CONFLICT(version) DO NOTHING;
