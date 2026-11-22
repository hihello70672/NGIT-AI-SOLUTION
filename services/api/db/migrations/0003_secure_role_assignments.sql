SET search_path TO ngit,public;
-- User-role grants are tenant-owned; the role catalog remains shared and read-only to end users.
ALTER TABLE user_roles ADD COLUMN tenant_user_id uuid GENERATED ALWAYS AS (user_id) STORED;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;
CREATE POLICY user_role_isolation ON user_roles USING (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid) WITH CHECK (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid);
CREATE INDEX audit_logs_occurred_idx ON audit_logs(occurred_at DESC);
INSERT INTO schema_migrations(version) VALUES('0003_secure_role_assignments');
