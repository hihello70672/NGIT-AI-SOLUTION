-- Phase 1 foundational schema. PostgreSQL 16+, isolated in the ngit schema.
CREATE SCHEMA IF NOT EXISTS ngit;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SET search_path TO ngit, public;

CREATE TABLE users (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), email text NOT NULL UNIQUE,
 password_hash text NOT NULL, display_name text NOT NULL,
 status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleted')),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK (email = lower(email)), CHECK (length(trim(display_name)) > 0)
);
CREATE TABLE roles (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE,
 description text NOT NULL DEFAULT '', created_at timestamptz NOT NULL DEFAULT now(),
 CHECK (name ~ '^[a-z][a-z0-9_]*$')
);
CREATE TABLE user_roles (
 user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 role_id uuid NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
 granted_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(user_id,role_id)
);
CREATE INDEX user_roles_role_idx ON user_roles(role_id,user_id);
CREATE TABLE conversations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 title text NOT NULL DEFAULT 'New conversation', status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(user_id,id)
);
CREATE INDEX conversations_user_updated_idx ON conversations(user_id,updated_at DESC,id);
CREATE TABLE messages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL, conversation_id uuid NOT NULL,
 role text NOT NULL CHECK(role IN ('system','user','assistant','tool')), content text NOT NULL,
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(user_id,conversation_id) REFERENCES conversations(user_id,id) ON DELETE CASCADE
);
CREATE INDEX messages_conversation_created_idx ON messages(conversation_id,created_at,id);
CREATE INDEX messages_user_created_idx ON messages(user_id,created_at DESC);
CREATE TABLE memory_records (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 conversation_id uuid, memory_type text NOT NULL CHECK(memory_type IN ('profile','preference','fact','summary')),
 content text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(user_id,conversation_id) REFERENCES conversations(user_id,id) ON DELETE CASCADE
);
CREATE INDEX memory_user_type_updated_idx ON memory_records(user_id,memory_type,updated_at DESC);
CREATE INDEX memory_conversation_idx ON memory_records(user_id,conversation_id) WHERE conversation_id IS NOT NULL;
CREATE TABLE provider_configs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), provider_key text NOT NULL UNIQUE, display_name text NOT NULL,
 enabled boolean NOT NULL DEFAULT false, endpoint_url text, credential_ref text,
 config jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(credential_ref IS NULL OR credential_ref !~* '(secret|token|password)=')
);
CREATE INDEX provider_configs_enabled_idx ON provider_configs(provider_key) WHERE enabled;
CREATE TABLE billing_plans (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), plan_key text NOT NULL UNIQUE, name text NOT NULL,
 currency char(3) NOT NULL DEFAULT 'USD' CHECK(currency ~ '^[A-Z]{3}$'),
 amount_minor bigint NOT NULL DEFAULT 0 CHECK(amount_minor>=0),
 interval text NOT NULL DEFAULT 'month' CHECK(interval IN ('month','year','one_time')),
 active boolean NOT NULL DEFAULT true, entitlements jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE subscriptions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 plan_id uuid NOT NULL REFERENCES billing_plans(id) ON DELETE RESTRICT,
 status text NOT NULL CHECK(status IN ('trialing','active','past_due','cancelled','expired')),
 current_period_start timestamptz, current_period_end timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(current_period_end IS NULL OR current_period_start IS NULL OR current_period_end>current_period_start), UNIQUE(user_id,id)
);
CREATE INDEX subscriptions_user_status_idx ON subscriptions(user_id,status,current_period_end DESC);
CREATE TABLE usage_records (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 subscription_id uuid, metric_key text NOT NULL, quantity bigint NOT NULL CHECK(quantity>=0),
 period_start timestamptz NOT NULL, period_end timestamptz NOT NULL, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(user_id,subscription_id) REFERENCES subscriptions(user_id,id) ON DELETE SET NULL (subscription_id),
 CHECK(period_end>period_start)
);
CREATE INDEX usage_user_period_idx ON usage_records(user_id,period_start DESC,metric_key);
CREATE TABLE media_assets (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 asset_type text NOT NULL CHECK(asset_type IN ('video','image','audio','document')),
 storage_key text NOT NULL, mime_type text NOT NULL, size_bytes bigint CHECK(size_bytes IS NULL OR size_bytes>=0),
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,id), UNIQUE(user_id,storage_key)
);
CREATE INDEX media_assets_user_created_idx ON media_assets(user_id,created_at DESC);
CREATE TABLE videos (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 asset_id uuid, title text NOT NULL, status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','queued','processing','ready','failed','archived')),
 duration_ms bigint CHECK(duration_ms IS NULL OR duration_ms>=0), metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(user_id,id),
 FOREIGN KEY(user_id,asset_id) REFERENCES media_assets(user_id,id) ON DELETE SET NULL (asset_id)
);
CREATE INDEX videos_user_updated_idx ON videos(user_id,updated_at DESC);
CREATE TABLE presentations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 title text NOT NULL, status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','processing','ready','failed','archived')),
 presenter_mode text NOT NULL DEFAULT 'slides' CHECK(presenter_mode IN ('slides','avatar','voiceover')),
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(user_id,id)
);
CREATE INDEX presentations_user_updated_idx ON presentations(user_id,updated_at DESC);
CREATE TABLE presentation_slides (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL, presentation_id uuid NOT NULL,
 position integer NOT NULL CHECK(position>=0), title text NOT NULL DEFAULT '', content jsonb NOT NULL DEFAULT '{}'::jsonb,
 duration_ms bigint CHECK(duration_ms IS NULL OR duration_ms>=0), created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(user_id,presentation_id) REFERENCES presentations(user_id,id) ON DELETE CASCADE, UNIQUE(presentation_id,position)
);
CREATE INDEX presentation_slides_parent_idx ON presentation_slides(user_id,presentation_id,position);
CREATE TABLE audit_logs (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
 action text NOT NULL, resource_type text NOT NULL, resource_id text, request_id text, ip_address inet,
 details jsonb NOT NULL DEFAULT '{}'::jsonb, occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_actor_time_idx ON audit_logs(actor_user_id,occurred_at DESC);
CREATE INDEX audit_resource_time_idx ON audit_logs(resource_type,resource_id,occurred_at DESC);
CREATE INDEX audit_action_time_idx ON audit_logs(action,occurred_at DESC);

-- All user-owned rows use transaction-local authenticated context `ngit.user_id`.
DO $rls$
DECLARE t text;
BEGIN
 FOREACH t IN ARRAY ARRAY['conversations','messages','memory_records','subscriptions','usage_records','media_assets','videos','presentations','presentation_slides'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY user_isolation ON %I USING (user_id = nullif(current_setting(''ngit.user_id'',true),'''')::uuid) WITH CHECK (user_id = nullif(current_setting(''ngit.user_id'',true),'''')::uuid)',t);
 END LOOP;
END $rls$;
-- Migration ledger makes the SQL migration runner repeatable without hiding schema errors.
CREATE TABLE schema_migrations(version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
INSERT INTO schema_migrations(version) VALUES('0001_initial_schema');
