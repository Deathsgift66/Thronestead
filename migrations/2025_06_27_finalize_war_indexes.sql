-- Migration: finalize foreign keys and add indexes

-- Link tactical wars to primary wars table
ALTER TABLE public.wars_tactical
  ADD CONSTRAINT wars_tactical_war_id_fkey
  FOREIGN KEY (war_id) REFERENCES public.wars(war_id) ON DELETE CASCADE;

-- Index frequently queried war_id columns
CREATE INDEX IF NOT EXISTS combat_logs_war_id_idx ON public.combat_logs(war_id);
CREATE INDEX IF NOT EXISTS war_scores_war_id_idx ON public.war_scores(war_id);
CREATE INDEX IF NOT EXISTS unit_movements_war_id_idx ON public.unit_movements(war_id);

-- Add version_tag to unit_stats for schema versioning
ALTER TABLE public.unit_stats
  ADD COLUMN version_tag text DEFAULT 'v6.12.2025.5.54';
