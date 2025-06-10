-- Migration: add notes and end_date columns to treaties
ALTER TABLE public.alliance_treaties
  ADD COLUMN notes text,
  ADD COLUMN end_date timestamp with time zone,
  ADD COLUMN status text CHECK (status IN ('proposed','active','cancelled','expired')) DEFAULT 'proposed';
ALTER TABLE public.kingdom_treaties
  ADD COLUMN notes text,
  ADD COLUMN end_date timestamp with time zone,
  ADD COLUMN status text CHECK (status IN ('proposed','active','cancelled','expired')) DEFAULT 'proposed';
