-- Domain tables, tenant constraints, indexes, and forced RLS are defined in 0001.
INSERT INTO ngit.schema_migrations(version) VALUES ('0004_complete_domain_schema') ON CONFLICT DO NOTHING;
