-- Migration: enforce single kingdom per user
ALTER TABLE public.kingdoms
  ADD CONSTRAINT kingdoms_user_id_key UNIQUE (user_id);
