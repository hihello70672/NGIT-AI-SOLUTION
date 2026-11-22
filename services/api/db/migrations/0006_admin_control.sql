-- Durable admin rules and service controls; audit events use the existing audit_logs table.
CREATE TABLE IF NOT EXISTS ngit.admin_rules (
    action text PRIMARY KEY CHECK (action ~ '^[a-z][a-z0-9_.-]{0,126}$'),
    roles text[] NOT NULL CHECK (cardinality(roles) BETWEEN 1 AND 20),
    approval_required boolean NOT NULL DEFAULT false,
    restricted boolean NOT NULL DEFAULT false,
    updated_by uuid REFERENCES ngit.users(id) ON DELETE SET NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (NOT restricted OR approval_required)
);
CREATE TABLE IF NOT EXISTS ngit.service_controls (
    service text PRIMARY KEY CHECK (service ~ '^[a-z][a-z0-9_-]{0,63}$'),
    enabled boolean NOT NULL,
    updated_by uuid REFERENCES ngit.users(id) ON DELETE SET NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE ngit.admin_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngit.admin_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY admin_rules_admin_select ON ngit.admin_rules FOR SELECT USING (
  EXISTS (SELECT 1 FROM ngit.user_roles ur JOIN ngit.roles r ON r.id=ur.role_id
          WHERE ur.user_id=nullif(current_setting('ngit.user_id',true),'')::uuid AND r.name='admin'));
CREATE POLICY admin_rules_admin_write ON ngit.admin_rules FOR ALL USING (
  EXISTS (SELECT 1 FROM ngit.user_roles ur JOIN ngit.roles r ON r.id=ur.role_id
          WHERE ur.user_id=nullif(current_setting('ngit.user_id',true),'')::uuid AND r.name='admin'))
  WITH CHECK (EXISTS (SELECT 1 FROM ngit.user_roles ur JOIN ngit.roles r ON r.id=ur.role_id
          WHERE ur.user_id=nullif(current_setting('ngit.user_id',true),'')::uuid AND r.name='admin'));
ALTER TABLE ngit.service_controls ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngit.service_controls FORCE ROW LEVEL SECURITY;
CREATE POLICY service_controls_admin_select ON ngit.service_controls FOR SELECT USING (
  EXISTS (SELECT 1 FROM ngit.user_roles ur JOIN ngit.roles r ON r.id=ur.role_id
          WHERE ur.user_id=nullif(current_setting('ngit.user_id',true),'')::uuid AND r.name='admin'));
CREATE POLICY service_controls_admin_write ON ngit.service_controls FOR ALL USING (
  EXISTS (SELECT 1 FROM ngit.user_roles ur JOIN ngit.roles r ON r.id=ur.role_id
          WHERE ur.user_id=nullif(current_setting('ngit.user_id',true),'')::uuid AND r.name='admin'))
  WITH CHECK (EXISTS (SELECT 1 FROM ngit.user_roles ur JOIN ngit.roles r ON r.id=ur.role_id
          WHERE ur.user_id=nullif(current_setting('ngit.user_id',true),'')::uuid AND r.name='admin'));
INSERT INTO ngit.schema_migrations(version) VALUES ('0006_admin_control') ON CONFLICT DO NOTHING;
