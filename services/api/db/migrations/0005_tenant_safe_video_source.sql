-- Add the same-tenant source constraint idempotently (PostgreSQL 16 compatible).
SET search_path TO ngit, public;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='videos_source_asset_owner_fkey' AND conrelid='ngit.videos'::regclass) THEN
  ALTER TABLE ngit.videos ADD CONSTRAINT videos_source_asset_owner_fkey FOREIGN KEY(source_asset_id,user_id) REFERENCES ngit.media_assets(id,user_id) ON DELETE RESTRICT;
 END IF;
END $$;
CREATE INDEX IF NOT EXISTS videos_source_asset_owner_idx ON ngit.videos(source_asset_id,user_id) WHERE source_asset_id IS NOT NULL;
INSERT INTO ngit.schema_migrations(version) VALUES('0005_tenant_safe_video_source') ON CONFLICT DO NOTHING;
