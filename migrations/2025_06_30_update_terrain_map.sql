-- Migration: add fields to terrain_map for schema v6.12.2025.13.16
ALTER TABLE public.terrain_map
  ADD COLUMN IF NOT EXISTS map_type text DEFAULT 'battlefield',
  ADD COLUMN IF NOT EXISTS tile_schema_version integer DEFAULT 1,
  ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
  ADD COLUMN IF NOT EXISTS map_source text DEFAULT 'auto-generated',
  ADD COLUMN IF NOT EXISTS map_features jsonb DEFAULT '{}'::jsonb;
