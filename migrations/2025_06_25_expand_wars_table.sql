-- Migration: expand wars table with additional metadata columns
ALTER TABLE public.wars
  ADD COLUMN attacker_kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
  ADD COLUMN defender_kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
  ADD COLUMN war_type TEXT,
  ADD COLUMN is_retaliation BOOLEAN DEFAULT FALSE,
  ADD COLUMN treaty_triggered BOOLEAN DEFAULT FALSE,
  ADD COLUMN victory_condition TEXT,
  ADD COLUMN outcome TEXT,
  ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT now(),
  ADD COLUMN submitted_by UUID REFERENCES public.users(user_id);

CREATE INDEX IF NOT EXISTS idx_wars_attacker ON public.wars (attacker_id);
CREATE INDEX IF NOT EXISTS idx_wars_defender ON public.wars (defender_id);
CREATE INDEX IF NOT EXISTS idx_wars_status ON public.wars (status);
CREATE INDEX IF NOT EXISTS idx_wars_type ON public.wars (war_type);
