-- Migration: expand unit_movements table

ALTER TABLE public.unit_movements
  ADD COLUMN unit_level INTEGER,
  ADD COLUMN visible_enemies JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN issued_by UUID REFERENCES public.users(user_id),
  ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
