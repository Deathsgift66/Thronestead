-- Migration: add Vacation Mode columns to kingdoms
ALTER TABLE public.kingdoms
  ADD COLUMN is_on_vacation boolean DEFAULT false,
  ADD COLUMN vacation_started_at timestamp with time zone,
  ADD COLUMN vacation_expires_at timestamp with time zone;
