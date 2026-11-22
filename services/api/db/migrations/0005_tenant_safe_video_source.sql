-- PostgreSQL 16 does not support a column-list SET NULL action for composite FKs.
-- Keep the optional source nullable, and use RESTRICT to preserve tenant ownership.
SET search_path TO ngit, public;
ALTER TABLE ngit.videos DROP CONSTRAINT IF EXISTS videos_source_asset_id_user_id_fkey;
ALTER TABLE ngit.videos ADD CONSTRAINT videos_source_asset_owner_fkey
 FOREIGN KEY(source_asset_id,user_id) REFERENCES ngit.media_assets(id,user_id) ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS videos_source_asset_owner_idx ON ngit.videos(source_asset_id,user_id) WHERE source_asset_id IS NOT NULL;
INSERT INTO ngit.schema_migrations(version) VALUES('0005_tenant_safe_video_source') ON CONFLICT DO NOTHING;
