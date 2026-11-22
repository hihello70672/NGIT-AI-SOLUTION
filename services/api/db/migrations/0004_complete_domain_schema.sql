-- Compatibility migration marker. Domain objects are created in 0001 so
-- billing plan reference data can be seeded by 0002 in lexical migration order.
SET search_path TO ngit,public;
INSERT INTO schema_migrations(version) VALUES('0004_complete_domain_schema') ON CONFLICT DO NOTHING;
