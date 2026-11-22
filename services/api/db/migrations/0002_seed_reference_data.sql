SET search_path TO ngit, public;
INSERT INTO roles(name,description) VALUES
 ('user','Standard authenticated account'),('admin','Privileged administrative account')
ON CONFLICT(name) DO NOTHING;
INSERT INTO billing_plans(plan_key,name,currency,amount_minor,billing_interval,entitlements) VALUES
 ('free','Free','USD',0,'month','{"conversations":true,"media_generation":false}'::jsonb),
 ('pro','Pro','USD',2000,'month','{"conversations":true,"media_generation":true}'::jsonb)
ON CONFLICT(plan_key) DO NOTHING;
INSERT INTO provider_configs(provider_key,display_name,enabled,config) VALUES
 ('local','Local / self-hosted',false,'{"optional":true}'::jsonb)
ON CONFLICT(provider_key) DO NOTHING;
INSERT INTO schema_migrations(version) VALUES ('0002_seed_reference_data') ON CONFLICT DO NOTHING;
