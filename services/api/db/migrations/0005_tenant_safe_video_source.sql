-- Scope a video's optional source asset to the same tenant. A composite
-- foreign key with ON DELETE SET NULL (source_asset_id) requires PostgreSQL 15+.
SET search_path TO ngit,public;
ALTER TABLE videos DROP CONSTRAINT IF EXISTS videos_source_asset_id_user_id_fkey;
ALTER TABLE videos ADD CONSTRAINT videos_source_asset_owner_fkey
  FOREIGN KEY(source_asset_id,user_id) REFERENCES media_assets(id,user_id)
  ON DELETE SET NULL (source_asset_id);
CREATE INDEX IF NOT EXISTS videos_source_asset_owner_idx ON videos(source_asset_id,user_id);
INSERT INTO schema_migrations(version) VALUES('0005_tenant_safe_video_source') ON CONFLICT DO NOTHING;
