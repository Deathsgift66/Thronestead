-- Migration: extend policies_laws_catalogue with additional fields

ALTER TABLE public.policies_laws_catalogue
  ADD COLUMN category text,
  ADD COLUMN modifiers jsonb DEFAULT '{}'::jsonb,
  ADD COLUMN unlock_at_level integer DEFAULT 1,
  ADD COLUMN is_active boolean DEFAULT true,
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN last_updated timestamp with time zone DEFAULT now();
