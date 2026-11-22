-- NGIT initial relational schema. Apply migrations in lexical order.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS ngit;
SET search_path TO ngit, public;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL UNIQUE,
    description text NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled','pending')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_idx ON users(lower(email));
CREATE TABLE IF NOT EXISTS user_roles (
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id uuid NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    PRIMARY KEY(user_id, role_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(id,user_id)
);
CREATE TABLE IF NOT EXISTS messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('system','user','assistant','tool')),
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY(conversation_id,user_id) REFERENCES conversations(id,user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS memories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind text NOT NULL,
    content text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billing_plans (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_key text NOT NULL UNIQUE,
    name text NOT NULL,
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    billing_interval text NOT NULL CHECK (billing_interval IN ('month','year','once')),
    entitlements jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS billing_accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id uuid NOT NULL REFERENCES billing_plans(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('trialing','active','past_due','cancelled','ended')),
    current_period_start timestamptz NOT NULL DEFAULT now(),
    current_period_end timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (current_period_end IS NULL OR current_period_end > current_period_start)
);
CREATE TABLE IF NOT EXISTS usage_records (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id uuid REFERENCES subscriptions(id) ON DELETE SET NULL,
    metric text NOT NULL,
    quantity bigint NOT NULL CHECK (quantity >= 0),
    recorded_at timestamptz NOT NULL DEFAULT now()
);

-- Provider rows contain opaque credential references only, never credentials.
CREATE TABLE IF NOT EXISTS provider_configs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_key text NOT NULL UNIQUE,
    display_name text NOT NULL,
    enabled boolean NOT NULL DEFAULT false,
    credential_ref text,
    config jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS media_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    media_type text NOT NULL CHECK (media_type IN ('image','video','audio','document','other')),
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(id,user_id)
);
CREATE TABLE IF NOT EXISTS videos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_asset_id uuid,
    title text NOT NULL DEFAULT '',
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY(source_asset_id,user_id) REFERENCES media_assets(id,user_id) ON DELETE SET NULL (source_asset_id)
);
CREATE TABLE IF NOT EXISTS presentations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(id,user_id)
);
CREATE TABLE IF NOT EXISTS presentation_slides (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    presentation_id uuid NOT NULL,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    metadata jsonb NOT NULL DEFAULT '{}',
    UNIQUE(presentation_id,position),
    FOREIGN KEY(presentation_id,user_id) REFERENCES presentations(id,user_id) ON DELETE CASCADE
);

-- Audit is privileged service data and deliberately has no end-user RLS policy.
CREATE TABLE IF NOT EXISTS audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    action text NOT NULL,
    details jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS user_roles_role_id_idx ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS conversations_user_recent_idx ON conversations(user_id, updated_at DESC, id);
CREATE INDEX IF NOT EXISTS messages_conversation_chronological_idx ON messages(conversation_id,user_id,created_at,id);
CREATE INDEX IF NOT EXISTS memories_user_recent_idx ON memories(user_id,created_at DESC,id);
CREATE INDEX IF NOT EXISTS subscriptions_user_status_idx ON subscriptions(user_id,status);
CREATE INDEX IF NOT EXISTS usage_records_user_recent_idx ON usage_records(user_id,recorded_at DESC,id);
CREATE INDEX IF NOT EXISTS provider_configs_enabled_idx ON provider_configs(provider_key) WHERE enabled;
CREATE INDEX IF NOT EXISTS media_assets_user_recent_idx ON media_assets(user_id,created_at DESC,id);
CREATE INDEX IF NOT EXISTS videos_user_recent_idx ON videos(user_id,created_at DESC,id);
CREATE INDEX IF NOT EXISTS presentations_user_recent_idx ON presentations(user_id,updated_at DESC,id);
CREATE INDEX IF NOT EXISTS presentation_slides_parent_idx ON presentation_slides(presentation_id,user_id,position);
CREATE INDEX IF NOT EXISTS audit_logs_created_idx ON audit_logs(created_at DESC,id);
CREATE INDEX IF NOT EXISTS audit_logs_actor_created_idx ON audit_logs(actor_user_id,created_at DESC,id);

-- RLS ownership context must be set transaction-locally by trusted API code.
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['conversations','messages','memories','billing_accounts','subscriptions','usage_records','media_assets','videos','presentations','presentation_slides'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY %I ON %I USING (user_id = nullif(current_setting(''ngit.user_id'', true), '''')::uuid) WITH CHECK (user_id = nullif(current_setting(''ngit.user_id'', true), '''')::uuid)',t||'_owner',t);
 END LOOP;
END $$;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
CREATE POLICY users_self_select ON users FOR SELECT USING (id = nullif(current_setting('ngit.user_id',true),'')::uuid);
CREATE POLICY users_self_update ON users FOR UPDATE USING (id = nullif(current_setting('ngit.user_id',true),'')::uuid) WITH CHECK (id = nullif(current_setting('ngit.user_id',true),'')::uuid);
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;
CREATE POLICY user_roles_self_select ON user_roles FOR SELECT USING (user_id = nullif(current_setting('ngit.user_id',true),'')::uuid);

INSERT INTO schema_migrations(version) VALUES ('0001_initial_schema') ON CONFLICT DO NOTHING;
