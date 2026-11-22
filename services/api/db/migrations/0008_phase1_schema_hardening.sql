-- Phase 1 hardening: migration bookkeeping, tenant-safe message ownership,
-- and supporting indexes. Provider credentials remain opaque references.
BEGIN;
ALTER TABLE ngit.schema_migrations ADD COLUMN IF NOT EXISTS checksum text;
ALTER TABLE ngit.schema_migrations ADD COLUMN IF NOT EXISTS execution_ms bigint;

ALTER TABLE ngit.messages
  DROP CONSTRAINT IF EXISTS messages_conversation_id_user_id_fkey;
ALTER TABLE ngit.messages
  ADD CONSTRAINT messages_conversation_id_user_id_fkey
  FOREIGN KEY (conversation_id, user_id)
  REFERENCES ngit.conversations(id, user_id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS messages_user_recent_idx
  ON ngit.messages (user_id, created_at DESC, id);
CREATE INDEX IF NOT EXISTS memories_user_kind_recent_idx
  ON ngit.memories (user_id, kind, created_at DESC, id);
CREATE INDEX IF NOT EXISTS billing_payments_user_recent_idx
  ON ngit.billing_payments (user_id, created_at DESC, id);
CREATE INDEX IF NOT EXISTS billing_webhook_events_received_idx
  ON ngit.billing_webhook_events (received_at DESC, provider_key, event_id);

ALTER TABLE ngit.provider_configs
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

INSERT INTO ngit.schema_migrations(version)
VALUES ('0008_phase1_schema_hardening')
ON CONFLICT (version) DO NOTHING;
COMMIT;
