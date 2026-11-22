-- Domain objects are established in 0001 before reference seeds in 0002.
SET search_path TO ngit, public;
INSERT INTO ngit.schema_migrations(version) VALUES ('0004_complete_domain_schema') ON CONFLICT DO NOTHING;
