-- Composite ownership FK prevents cross-tenant video source references.
SET search_path TO ngit, public;
INSERT INTO ngit.schema_migrations(version) VALUES ('0005_tenant_safe_video_source') ON CONFLICT DO NOTHING;
