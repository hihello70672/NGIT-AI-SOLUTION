-- Same-tenant source asset constraint (composite FK) and lookup index are established in 0001.
INSERT INTO ngit.schema_migrations(version) VALUES ('0005_tenant_safe_video_source') ON CONFLICT DO NOTHING;
