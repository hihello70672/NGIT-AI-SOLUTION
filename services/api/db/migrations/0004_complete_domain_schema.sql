-- Retained compatibility migration: billing and metadata tables are created in 0001
-- so all dependent objects are available before reference-data seeding in 0002.
SET search_path TO ngit,public;
INSERT INTO schema_migrations(version) VALUES('0004_complete_domain_schema') ON CONFLICT DO NOTHING;
