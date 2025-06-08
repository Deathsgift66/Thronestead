-- Migration: extend projects_player with build state and audit columns

ALTER TABLE public.projects_player
  ADD COLUMN IF NOT EXISTS build_state text NULL DEFAULT 'building',
  ADD COLUMN IF NOT EXISTS is_active boolean NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS started_by uuid NULL,
  ADD COLUMN IF NOT EXISTS last_updated timestamp with time zone NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS expires_at timestamp with time zone NULL,
  ADD CONSTRAINT projects_player_started_by_fkey FOREIGN KEY (started_by)
    REFERENCES users (user_id) ON DELETE SET NULL,
  ADD CONSTRAINT projects_player_build_state_check CHECK (
    build_state = ANY (ARRAY['queued','building','completed','expired'])
  );
