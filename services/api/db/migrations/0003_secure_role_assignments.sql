SET search_path TO ngit,public;
-- Grants are keyed by user_id directly; no redundant tenant column is needed.
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;
CREATE POLICY user_role_isolation ON user_roles USING (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid) WITH CHECK (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid);
CREATE INDEX audit_logs_occurred_idx ON audit_logs(occurred_at DESC);
INSERT INTO schema_migrations(version) VALUES('0003_secure_role_assignments');
