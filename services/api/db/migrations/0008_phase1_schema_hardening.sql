-- Phase 1 hardening: migration bookkeeping, tenant-safe conversation/message
-- relationships, provider metadata, and supporting indexes.
BEGIN;

ALTER TABLE ngit.schema_migrations ADD COLUMN IF NOT EXISTS checksum text;
ALTER TABLE ngit.schema_migrations ADD COLUMN IF NOT EXISTS execution_ms bigint;

-- Messages already carry user_id. Require it to be the same owner as their
-- conversation so tenant consistency is enforced by the database.
ALTER TABLE ngit.messages
  DROP CONSTRAINT IF EXISTS messages_conversation_id_user_id_fkey;
ALTER TABLE ngit.messages
  ADD CONSTRAINT messages_conversation_id_user_id_fkey
  FOREIGN KEY (conversation_id, user_id)
  REFERENCES ngit.conversations(id, user_id) ON DELETE CASCADE;

-- Common access paths for conversation history, memory retrieval and billing.
CREATE INDEX IF NOT EXISTS messages_user_recent_idx
  ON ngit.messages (user_id, created_at DESC, id);
CREATE INDEX IF NOT EXISTS memories_user_kind_recent_idx
  ON ngit.memories (user_id, kind, created_at DESC, id);
CREATE INDEX IF NOT EXISTS billing_payments_user_recent_idx
  ON ngit.billing_payments (user_id, created_at DESC, id);
CREATE INDEX IF NOT EXISTS billing_webhook_events_received_idx
  ON ngit.billing_webhook_events (received_at DESC, provider_key, event_id);

-- Provider records are operational metadata only. Never store API keys here;
-- credential_ref is an opaque server-side secret-manager reference.
ALTER TABLE ngit.provider_configs
  ADD COLUMN IF NOT EXISTS credential_ref text,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- Idempotent schema version marker. Earlier versions remain untouched.
INSERT INTO ngit.schema_migrations(version)
VALUES ('0008_phase1_schema_hardening')
ON CONFLICT (version) DO NOTHING;
COMMIT;
